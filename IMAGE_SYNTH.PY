pkg update -y && pkg install clang -y && cat > $HOME/mobile_multimodal_ml.c <<'EOF'
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <sys/sysinfo.h>

#if defined(__aarch64__)
#include <arm_neon.h>
#endif

static volatile sig_atomic_t stop_flag = 0;

typedef struct {
    int id;
    int hidden;
    int seq;
    int vocab;
    uint64_t end_ns;
    double ops;
    double loss;
    uint64_t steps;
} Worker;

static uint64_t now_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

static void stop_handler(int s) {
    (void)s;
    stop_flag = 1;
}

static float randf(uint64_t *s) {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    return ((float)(*s & 0xffffff) / 8388608.0f) - 1.0f;
}

static float dot(const float *a, const float *b, int n) {
#if defined(__aarch64__)
    float32x4_t x0=vdupq_n_f32(0),x1=vdupq_n_f32(0),x2=vdupq_n_f32(0),x3=vdupq_n_f32(0);
    int i=0;
    for(; i+16<=n; i+=16){
        x0=vfmaq_f32(x0,vld1q_f32(a+i),vld1q_f32(b+i));
        x1=vfmaq_f32(x1,vld1q_f32(a+i+4),vld1q_f32(b+i+4));
        x2=vfmaq_f32(x2,vld1q_f32(a+i+8),vld1q_f32(b+i+8));
        x3=vfmaq_f32(x3,vld1q_f32(a+i+12),vld1q_f32(b+i+12));
    }
    x0=vaddq_f32(vaddq_f32(x0,x1),vaddq_f32(x2,x3));
    float32x2_t p=vadd_f32(vget_low_f32(x0),vget_high_f32(x0));
    p=vpadd_f32(p,p);
    float r=vget_lane_f32(p,0);
    for(;i<n;i++) r+=a[i]*b[i];
    return r;
#else
    float r=0;
    for(int i=0;i<n;i++) r+=a[i]*b[i];
    return r;
#endif
}

static float gelu(float x) {
    return 0.5f*x*(1.0f+tanhf(0.79788456f*(x+0.044715f*x*x*x)));
}

static void layernorm(float *x,int n) {
    double m=0,q=0;
    for(int i=0;i<n;i++){m+=x[i];q+=(double)x[i]*x[i];}
    m/=n;
    double v=q/n-m*m;
    float inv=1.0f/sqrtf((float)v+1e-5f);
    for(int i=0;i<n;i++) x[i]=(x[i]-(float)m)*inv;
}

static void softmax(float *x,int n) {
    float mx=x[0];
    for(int i=1;i<n;i++) if(x[i]>mx) mx=x[i];
    double s=0;
    for(int i=0;i<n;i++){x[i]=expf(x[i]-mx);s+=x[i];}
    float inv=1.0f/(float)s;
    for(int i=0;i<n;i++) x[i]*=inv;
}

static float image_conv_step(float *img,float *out,int w,int h,float *k) {
    double loss=0;
    for(int y=1;y<h-1;y++) {
        for(int x=1;x<w-1;x++) {
            float z=0;
            int ki=0;
            for(int yy=-1;yy<=1;yy++)
                for(int xx=-1;xx<=1;xx++)
                    z += img[(y+yy)*w+x+xx]*k[ki++];
            z=gelu(z);
            out[y*w+x]=z;
            float target=sinf((float)x*0.035f)+cosf((float)y*0.027f);
            float e=z-target;
            loss += e*e;
        }
    }
    return (float)(loss/(w*h));
}

static float transformer_step(
    float *tokens,
    float *q,
    float *k,
    float *v,
    float *att,
    float *proj,
    int seq,
    int hidden,
    uint64_t *state
){
    for(int t=0;t<seq;t++) {
        float *x=tokens+t*hidden;
        layernorm(x,hidden);

        for(int j=0;j<hidden;j++) {
            float aq=0,ak=0,av=0;
            for(int i=0;i<hidden;i++) {
                float r=(float)((i*31+j*17)%97)/97.0f;
                aq += x[i]*sinf(r*3.1f)*0.03f;
                ak += x[i]*cosf(r*2.7f)*0.03f;
                av += x[i]*sinf(r*1.9f)*0.03f;
            }
            q[t*hidden+j]=aq;
            k[t*hidden+j]=ak;
            v[t*hidden+j]=av;
        }
    }

    float scale=1.0f/sqrtf((float)hidden);

    for(int i=0;i<seq;i++) {
        for(int j=0;j<seq;j++) {
            att[i*seq+j]=dot(q+i*hidden,k+j*hidden,hidden)*scale;
        }
        softmax(att+i*seq,seq);
    }

    double loss=0;

    for(int i=0;i<seq;i++) {
        for(int d=0;d<hidden;d++) {
            float z=0;
            for(int j=0;j<seq;j++)
                z += att[i*seq+j]*v[j*hidden+d];

            proj[i*hidden+d]=gelu(z);

            float target =
                0.6f*sinf((float)(i+d)*0.013f) +
                0.4f*cosf((float)(i*3+d)*0.009f);

            float e=proj[i*hidden+d]-target;
            loss+=e*e;

            tokens[i*hidden+d] -= 0.0005f*e;
            tokens[i*hidden+d] += 0.00001f*randf(state);
        }
    }

    return (float)(loss/(seq*hidden));
}

static float voice_step(float *wave,float *spec,int n,int bins,uint64_t *state) {
    float f0=90.0f + fabsf(randf(state))*160.0f;
    float f1=500.0f + fabsf(randf(state))*400.0f;
    float f2=1200.0f + fabsf(randf(state))*1000.0f;

    for(int i=0;i<n;i++) {
        float t=(float)i/16000.0f;
        float x=0;

        for(int h=1;h<=20;h++) {
            float f=f0*h;
            float g1=1.0f/(1.0f+fabsf(f-f1)/100.0f);
            float g2=1.0f/(1.0f+fabsf(f-f2)/180.0f);
            x += sinf(2*M_PI*f*t)*(g1+0.7f*g2)/(float)h;
        }

        wave[i]=tanhf(x*0.7f);
    }

    double loss=0;

    for(int b=0;b<bins;b++) {
        float freq=50.0f+b*20.0f;
        float re=0,im=0;

        for(int i=0;i<n;i+=4) {
            float a=-2.0f*M_PI*freq*i/16000.0f;
            re += wave[i]*cosf(a);
            im += wave[i]*sinf(a);
        }

        float mag=sqrtf(re*re+im*im)/(n/4);
        spec[b]=mag;

        float target=expf(-fabsf(freq-f1)/700.0f);
        float e=mag-target;
        loss += e*e;
    }

    return (float)(loss/bins);
}

static void *worker_fn(void *arg) {
    Worker *w=(Worker*)arg;

    int hidden=w->hidden;
    int seq=w->seq;

    uint64_t st=0x9e3779b97f4a7c15ULL ^ ((uint64_t)w->id<<32);

    float *tokens=aligned_alloc(64,(size_t)seq*hidden*sizeof(float));
    float *q=aligned_alloc(64,(size_t)seq*hidden*sizeof(float));
    float *k=aligned_alloc(64,(size_t)seq*hidden*sizeof(float));
    float *v=aligned_alloc(64,(size_t)seq*hidden*sizeof(float));
    float *att=aligned_alloc(64,(size_t)seq*seq*sizeof(float));
    float *proj=aligned_alloc(64,(size_t)seq*hidden*sizeof(float));

    int iw=320,ih=320;
    float *img=aligned_alloc(64,(size_t)iw*ih*sizeof(float));
    float *out=aligned_alloc(64,(size_t)iw*ih*sizeof(float));

    int ns=8192,bins=180;
    float *wave=aligned_alloc(64,(size_t)ns*sizeof(float));
    float *spec=aligned_alloc(64,(size_t)bins*sizeof(float));

    if(!tokens||!q||!k||!v||!att||!proj||!img||!out||!wave||!spec)
        return NULL;

    for(int i=0;i<seq*hidden;i++) tokens[i]=randf(&st);
    for(int i=0;i<iw*ih;i++) img[i]=randf(&st);

    float kernel[9]={0.05f,-0.12f,0.07f,-0.08f,0.95f,-0.10f,0.06f,-0.11f,0.04f};

    while(!stop_flag && now_ns()<w->end_ns) {
        float llm_loss=transformer_step(tokens,q,k,v,att,proj,seq,hidden,&st);
        float img_loss=image_conv_step(img,out,iw,ih,kernel);
        float voice_loss=voice_step(wave,spec,ns,bins,&st);

        for(int i=0;i<iw*ih;i+=17)
            img[i]=0.995f*img[i]+0.005f*out[i];

        w->loss = 0.55*llm_loss + 0.30*img_loss + 0.15*voice_loss;

        w->ops +=
            (double)seq*seq*hidden*2.0 +
            (double)seq*hidden*hidden*6.0 +
            (double)iw*ih*9.0*2.0 +
            (double)ns*bins/2.0;

        w->steps++;
    }

    free(tokens); free(q); free(k); free(v); free(att); free(proj);
    free(img); free(out); free(wave); free(spec);

    return NULL;
}

static uint64_t mem_available_kb() {
    FILE *f=fopen("/proc/meminfo","r");
    if(!f) return 0;

    char key[64],unit[32];
    unsigned long long v;

    while(fscanf(f,"%63s %llu %31s",key,&v,unit)==3) {
        if(strcmp(key,"MemAvailable:")==0) {
            fclose(f);
            return v;
        }
    }

    fclose(f);
    return 0;
}

static uint64_t mem_total_kb() {
    FILE *f=fopen("/proc/meminfo","r");
    if(!f) return 0;

    char key[64],unit[32];
    unsigned long long v;

    while(fscanf(f,"%63s %llu %31s",key,&v,unit)==3) {
        if(strcmp(key,"MemTotal:")==0) {
            fclose(f);
            return v;
        }
    }

    fclose(f);
    return 0;
}

static double cpu_load() {
    double l[3]={0};
    getloadavg(l,3);
    return l[0];
}

static double temperature() {
    double max=-1;
    char p[256];

    for(int z=0;z<128;z++) {
        snprintf(p,sizeof(p),"/sys/class/thermal/thermal_zone%d/temp",z);
        FILE *f=fopen(p,"r");
        if(!f) continue;

        double v;
        if(fscanf(f,"%lf",&v)==1) {
            if(v>1000) v/=1000;
            else if(v>150) v/=10;

            if(v>15 && v<130 && v>max) max=v;
        }

        fclose(f);
    }

    return max;
}

int main() {
    signal(SIGINT,stop_handler);
    signal(SIGTERM,stop_handler);

    long cores=sysconf(_SC_NPROCESSORS_ONLN);
    if(cores<1) cores=1;
    if(cores>32) cores=32;

    int runtime=1200;
    char *e=getenv("DURATION_SEC");
    if(e && atoi(e)>0) runtime=atoi(e);

    double requested_gb=8.0;
    e=getenv("RAM_GB");
    if(e && atof(e)>0) requested_gb=atof(e);

    uint64_t available=mem_available_kb()*1024ULL;
    uint64_t reserve=1536ULL*1024ULL*1024ULL;

    uint64_t requested=(uint64_t)(requested_gb*1024.0*1024.0*1024.0);

    uint64_t safe=requested;

    if(available>reserve && safe>available-reserve)
        safe=available-reserve;

    if(safe<256ULL*1024ULL*1024ULL)
        safe=256ULL*1024ULL*1024ULL;

    uint8_t *arena=NULL;
    uint64_t arena_size=safe;

    while(arena_size>=256ULL*1024ULL*1024ULL) {
        arena=malloc(arena_size);
        if(arena) break;
        arena_size=(uint64_t)(arena_size*0.85);
    }

    if(arena) {
        for(uint64_t i=0;i<arena_size;i+=4096)
            arena[i]=(uint8_t)((i>>12)^0x5a);
    }

    int hidden=192;
    int seq=64;

    pthread_t *th=calloc(cores,sizeof(pthread_t));
    Worker *workers=calloc(cores,sizeof(Worker));

    uint64_t start=now_ns();
    uint64_t end=start+(uint64_t)runtime*1000000000ULL;

    printf("\nMULTIMODAL MOBILE ML ENGINE\n");
    printf("CPU cores       : %ld\n",cores);

#if defined(__aarch64__)
    printf("SIMD            : ARM64 NEON\n");
#else
    printf("SIMD            : generic\n");
#endif

    printf("Runtime         : %d sec\n",runtime);
    printf("RAM arena       : %.2f GiB\n",(double)arena_size/1073741824.0);
    printf("Transformer     : seq=%d hidden=%d\n",seq,hidden);
    printf("Image workload  : 320x320 convolution\n");
    printf("Voice workload  : harmonic synthesis + spectral loss\n\n");

    for(int i=0;i<cores;i++) {
        workers[i].id=i;
        workers[i].hidden=hidden;
        workers[i].seq=seq;
        workers[i].vocab=4096;
        workers[i].end_ns=end;

        pthread_create(&th[i],NULL,worker_fn,&workers[i]);
    }

    uint64_t sweep=0;
    uint64_t last_sweep=start;

    while(!stop_flag && now_ns()<end) {
        sleep(10);

        uint64_t n=now_ns();
        double elapsed=(n-start)/1e9;

        double total_ops=0;
        double total_loss=0;
        uint64_t steps=0;

        for(int i=0;i<cores;i++) {
            total_ops += workers[i].ops;
            total_loss += workers[i].loss;
            steps += workers[i].steps;
        }

        if(arena && n-last_sweep>9000000000ULL) {
            for(uint64_t i=0;i<arena_size;i+=4096) {
                arena[i]=(uint8_t)(arena[i]+1+(sweep&7));
            }
            sweep++;
            last_sweep=n;
        }

        uint64_t total_kb=mem_total_kb();
        uint64_t avail_kb=mem_available_kb();
        double used_gb=(double)(total_kb-avail_kb)*1024.0/1073741824.0;
        double total_gb=(double)total_kb*1024.0/1073741824.0;
        double t=temperature();

        printf(
            "time=%6.1fs | "
            "RAM=%5.2f/%5.2f GiB | "
            "load=%4.2f | "
            "steps=%llu | "
            "loss=%9.6f | "
            "throughput=%8.2f GFLOP/s",
            elapsed,
            used_gb,
            total_gb,
            cpu_load(),
            (unsigned long long)steps,
            cores?total_loss/cores:0,
            total_ops/elapsed/1e9
        );

        if(t>0) printf(" | temp=%5.1fC",t);

        printf("\n");
        fflush(stdout);

        if(t>88.0) {
            printf("thermal protection active\n");
            fflush(stdout);
            sleep(20);
        }
    }

    stop_flag=1;

    for(int i=0;i<cores;i++)
        pthread_join(th[i],NULL);

    double elapsed=(now_ns()-start)/1e9;
    double total_ops=0;
    uint64_t total_steps=0;

    for(int i=0;i<cores;i++) {
        total_ops += workers[i].ops;
        total_steps += workers[i].steps;
    }

    printf("\nFINAL REPORT\n");
    printf("Elapsed         : %.2f sec\n",elapsed);
    printf("Training steps  : %llu\n",(unsigned long long)total_steps);
    printf("Compute         : %.3f TFLOP-equivalent\n",total_ops/1e12);
    printf("Average speed   : %.2f GFLOP/s\n",total_ops/elapsed/1e9);
    printf("RAM arena       : %.2f GiB\n",(double)arena_size/1073741824.0);

    free(arena);
    free(th);
    free(workers);

    return 0;
}
EOF

clang -O3 -ffast-math -funroll-loops -pthread \
$HOME/mobile_multimodal_ml.c -lm \
-o $HOME/mobile_multimodal_ml && \
DURATION_SEC=1200 RAM_GB=8 $HOME/mobile_multimodal_ml
