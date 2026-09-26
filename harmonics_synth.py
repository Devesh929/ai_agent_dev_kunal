pkg update -y && pkg install clang -y && cat > ~/iqoo15_ml_lab.c <<'EOF'
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

#ifdef __aarch64__
#include <arm_neon.h>
#endif

volatile sig_atomic_t STOP = 0;

typedef struct {
    int id;
    int hidden;
    int seq;
    uint64_t end_ns;
    uint64_t steps;
    double ops;
    double loss;
    double attention_loss;
    double vision_loss;
    double audio_loss;
} Worker;

static uint64_t nowns() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000ULL + t.tv_nsec;
}

static void handler(int x) {
    (void)x;
    STOP = 1;
}

static uint64_t rng(uint64_t *s) {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    return *s;
}

static float rf(uint64_t *s) {
    return ((rng(s) & 0xFFFFFF) / 8388608.0f) - 1.0f;
}

static float dot(const float *a, const float *b, int n) {
#ifdef __aarch64__

    float32x4_t s0 = vdupq_n_f32(0);
    float32x4_t s1 = vdupq_n_f32(0);
    float32x4_t s2 = vdupq_n_f32(0);
    float32x4_t s3 = vdupq_n_f32(0);

    int i = 0;

    for (; i + 16 <= n; i += 16) {

        s0 = vfmaq_f32(
            s0,
            vld1q_f32(a + i),
            vld1q_f32(b + i)
        );

        s1 = vfmaq_f32(
            s1,
            vld1q_f32(a + i + 4),
            vld1q_f32(b + i + 4)
        );

        s2 = vfmaq_f32(
            s2,
            vld1q_f32(a + i + 8),
            vld1q_f32(b + i + 8)
        );

        s3 = vfmaq_f32(
            s3,
            vld1q_f32(a + i + 12),
            vld1q_f32(b + i + 12)
        );
    }

    float32x4_t t0 = vaddq_f32(s0, s1);
    float32x4_t t1 = vaddq_f32(s2, s3);
    float32x4_t t = vaddq_f32(t0, t1);

    float32x2_t p =
        vadd_f32(
            vget_low_f32(t),
            vget_high_f32(t)
        );

    p = vpadd_f32(p, p);

    float out = vget_lane_f32(p, 0);

    for (; i < n; i++)
        out += a[i] * b[i];

    return out;

#else

    float x = 0;

    for (int i = 0; i < n; i++)
        x += a[i] * b[i];

    return x;

#endif
}

static float gelu(float x) {
    return 0.5f * x *
        (1.0f +
        tanhf(
            0.79788456f *
            (x + 0.044715f * x*x*x)
        ));
}

static void norm(float *x, int n) {

    double m = 0;
    double q = 0;

    for (int i = 0; i < n; i++) {
        m += x[i];
        q += x[i] * x[i];
    }

    m /= n;

    double variance =
        q / n - m*m;

    float inv =
        1.0f /
        sqrtf(
            (float)variance +
            1e-5f
        );

    for (int i = 0; i < n; i++)
        x[i] =
            (x[i] - (float)m) *
            inv;
}

static void softmax(float *x, int n) {

    float mx = x[0];

    for (int i = 1; i < n; i++)
        if (x[i] > mx)
            mx = x[i];

    double sum = 0;

    for (int i = 0; i < n; i++) {
        x[i] = expf(x[i] - mx);
        sum += x[i];
    }

    float inv = 1.0f / (float)sum;

    for (int i = 0; i < n; i++)
        x[i] *= inv;
}

static float transformer(
    float *tokens,
    float *Q,
    float *K,
    float *V,
    float *A,
    float *O,
    int seq,
    int h,
    uint64_t *state)
{
    for (int t = 0; t < seq; t++) {

        float *x =
            tokens + t*h;

        norm(x, h);

        for (int d = 0; d < h; d++) {

            float q = 0;
            float k = 0;
            float v = 0;

            for (int j = 0; j < h; j++) {

                float z =
                    ((j*37 + d*17) % 127)
                    / 127.0f;

                q +=
                    x[j] *
                    sinf(z*2.1f) *
                    0.025f;

                k +=
                    x[j] *
                    cosf(z*2.7f) *
                    0.025f;

                v +=
                    x[j] *
                    sinf(z*3.4f) *
                    0.025f;
            }

            Q[t*h+d] = q;
            K[t*h+d] = k;
            V[t*h+d] = v;
        }
    }

    float scale =
        1.0f /
        sqrtf((float)h);

    for (int i = 0; i < seq; i++) {

        for (int j = 0; j < seq; j++) {

            A[i*seq+j] =
                dot(
                    Q+i*h,
                    K+j*h,
                    h
                ) * scale;
        }

        softmax(
            A+i*seq,
            seq
        );
    }

    double loss = 0;

    for (int i = 0; i < seq; i++) {

        for (int d = 0; d < h; d++) {

            float s = 0;

            for (int j = 0; j < seq; j++) {

                s +=
                    A[i*seq+j] *
                    V[j*h+d];
            }

            O[i*h+d] =
                gelu(s);

            float target =
                0.55f *
                sinf(
                    (float)(i+d)*0.012f
                ) +

                0.45f *
                cosf(
                    (float)(i*5+d)*0.008f
                );

            float err =
                O[i*h+d] -
                target;

            loss +=
                err*err;

            tokens[i*h+d] -=
                0.0003f *
                err;

            tokens[i*h+d] +=
                0.000005f *
                rf(state);
        }
    }

    return
        (float)(
            loss /
            (seq*h)
        );
}

static float vision(
    float *img,
    float *tmp,
    int W,
    int H)
{
    static float kernel[25] = {
         0.01,-0.02,-0.03,-0.02, 0.01,
        -0.02, 0.03, 0.08, 0.03,-0.02,
        -0.03, 0.08, 0.72, 0.08,-0.03,
        -0.02, 0.03, 0.08, 0.03,-0.02,
         0.01,-0.02,-0.03,-0.02, 0.01
    };

    double loss = 0;

    for (int y = 2; y < H-2; y++) {

        for (int x = 2; x < W-2; x++) {

            float z = 0;
            int p = 0;

            for (int yy = -2; yy <= 2; yy++)
                for (int xx = -2; xx <= 2; xx++)
                    z +=
                        img[(y+yy)*W+x+xx] *
                        kernel[p++];

            z = gelu(z);

            tmp[y*W+x] = z;

            float target =
                sinf(x*0.017f) *
                cosf(y*0.021f);

            float e =
                z-target;

            loss += e*e;
        }
    }

    for (int i = 0; i < W*H; i += 5)
        img[i] =
            img[i]*0.998f +
            tmp[i]*0.002f;

    return
        loss /
        (W*H);
}

static float audio(
    float *wave,
    float *spectrum,
    int N,
    int bins,
    uint64_t *state)
{
    float f0 =
        90.0f +
        fabsf(rf(state))*150;

    float formant1 =
        450 +
        fabsf(rf(state))*550;

    float formant2 =
        1100 +
        fabsf(rf(state))*1300;

    for (int i = 0; i < N; i++) {

        float t =
            i / 16000.0f;

        float s = 0;

        for (int h = 1; h <= 32; h++) {

            float f =
                f0*h;

            float g1 =
                1.0f /
                (
                    1.0f +
                    fabsf(
                        f-formant1
                    )/100.0f
                );

            float g2 =
                1.0f /
                (
                    1.0f +
                    fabsf(
                        f-formant2
                    )/180.0f
                );

            s +=
                sinf(
                    2*M_PI*f*t
                ) *
                (g1 + 0.65f*g2) /
                h;
        }

        wave[i] =
            tanhf(s);
    }

    double loss = 0;

    for (int b = 0; b < bins; b++) {

        float freq =
            40 +
            b*18;

        float re = 0;
        float im = 0;

        for (int i = 0; i < N; i += 4) {

            float a =
                -2*M_PI *
                freq*i /
                16000.0f;

            re +=
                wave[i] *
                cosf(a);

            im +=
                wave[i] *
                sinf(a);
        }

        float mag =
            sqrtf(
                re*re +
                im*im
            ) /
            (N/4);

        spectrum[b] =
            mag;

        float target =
            expf(
                -fabsf(
                    freq-formant1
                ) /
                500
            );

        float e =
            mag-target;

        loss +=
            e*e;
    }

    return
        loss /
        bins;
}

static void *worker(void *arg) {

    Worker *w =
        (Worker*)arg;

    int H =
        w->hidden;

    int S =
        w->seq;

    uint64_t state =
        0x123456789abcdefULL ^
        ((uint64_t)w->id<<24);

    float *tokens =
        aligned_alloc(
            64,
            S*H*sizeof(float)
        );

    float *Q =
        aligned_alloc(
            64,
            S*H*sizeof(float)
        );

    float *K =
        aligned_alloc(
            64,
            S*H*sizeof(float)
        );

    float *V =
        aligned_alloc(
            64,
            S*H*sizeof(float)
        );

    float *A =
        aligned_alloc(
            64,
            S*S*sizeof(float)
        );

    float *O =
        aligned_alloc(
            64,
            S*H*sizeof(float)
        );

    int W = 384;
    int IH = 384;

    float *img =
        aligned_alloc(
            64,
            W*IH*sizeof(float)
        );

    float *tmp =
        aligned_alloc(
            64,
            W*IH*sizeof(float)
        );

    int N = 8192;
    int bins = 192;

    float *wave =
        aligned_alloc(
            64,
            N*sizeof(float)
        );

    float *spec =
        aligned_alloc(
            64,
            bins*sizeof(float)
        );

    if (!tokens || !Q || !K || !V ||
        !A || !O || !img || !tmp ||
        !wave || !spec)
        return NULL;

    for (int i = 0; i < S*H; i++)
        tokens[i] =
            rf(&state);

    for (int i = 0; i < W*IH; i++)
        img[i] =
            rf(&state);

    while (
        !STOP &&
        nowns() <
        w->end_ns
    ) {

        float l1 =
            transformer(
                tokens,
                Q,
                K,
                V,
                A,
                O,
                S,
                H,
                &state
            );

        float l2 =
            vision(
                img,
                tmp,
                W,
                IH
            );

        float l3 =
            audio(
                wave,
                spec,
                N,
                bins,
                &state
            );

        w->attention_loss =
            l1;

        w->vision_loss =
            l2;

        w->audio_loss =
            l3;

        w->loss =
            0.55*l1 +
            0.30*l2 +
            0.15*l3;

        w->ops +=
            (double)S*S*H*2 +
            (double)S*H*H*6 +
            (double)W*IH*25*2 +
            (double)N*bins/2;

        w->steps++;
    }

    free(tokens);
    free(Q);
    free(K);
    free(V);
    free(A);
    free(O);
    free(img);
    free(tmp);
    free(wave);
    free(spec);

    return NULL;
}

static uint64_t read_value(
    const char *name)
{
    FILE *f =
        fopen(
            "/proc/meminfo",
            "r"
        );

    if (!f)
        return 0;

    char k[64];
    char u[32];

    unsigned long long v;

    while (
        fscanf(
            f,
            "%63s %llu %31s",
            k,
            &v,
            u
        ) == 3)
    {
        if (
            strcmp(
                k,
                name
            ) == 0
        )
        {
            fclose(f);
            return v;
        }
    }

    fclose(f);
    return 0;
}

static double tempC() {

    double best = -1;

    char p[256];

    for (int z=0;z<128;z++) {

        snprintf(
            p,
            sizeof(p),
            "/sys/class/thermal/thermal_zone%d/temp",
            z
        );

        FILE *f =
            fopen(
                p,
                "r"
            );

        if (!f)
            continue;

        double v;

        if (
            fscanf(
                f,
                "%lf",
                &v
            ) == 1
        ) {

            if (v > 1000)
                v /= 1000;

            else if (v > 150)
                v /= 10;

            if (
                v > 15 &&
                v < 130 &&
                v > best
            )
                best = v;
        }

        fclose(f);
    }

    return best;
}

static double cpuMHz(int cpu) {

    char path[256];

    snprintf(
        path,
        sizeof(path),
        "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq",
        cpu
    );

    FILE *f =
        fopen(
            path,
            "r"
        );

    if (!f)
        return -1;

    double kHz;

    if (
        fscanf(
            f,
            "%lf",
            &kHz
        ) != 1
    ) {
        fclose(f);
        return -1;
    }

    fclose(f);

    return
        kHz /
        1000.0;
}

static void memory_sweep(
    uint8_t *mem,
    uint64_t bytes,
    uint64_t pass)
{
    if (!mem)
        return;

    for (
        uint64_t i=0;
        i<bytes;
        i+=64
    ) {

        mem[i] =
            (uint8_t)(
                mem[i] +
                pass +
                (i>>6)
            );
    }
}

int main() {

    signal(
        SIGINT,
        handler
    );

    signal(
        SIGTERM,
        handler
    );

    long cores =
        sysconf(
            _SC_NPROCESSORS_ONLN
        );

    if (cores < 1)
        cores = 1;

    int runtime = 1200;

    char *x =
        getenv(
            "DURATION"
        );

    if (x)
        runtime =
            atoi(x);

    double ramGB = 6.0;

    x =
        getenv(
            "RAM_GB"
        );

    if (x)
        ramGB =
            atof(x);

    uint64_t totalKB =
        read_value(
            "MemTotal:"
        );

    uint64_t availKB =
        read_value(
            "MemAvailable:"
        );

    uint64_t requested =
        (uint64_t)(
            ramGB *
            1073741824.0
        );

    uint64_t reserve =
        2ULL *
        1073741824ULL;

    uint64_t allowed =
        requested;

    uint64_t availableBytes =
        availKB *
        1024ULL;

    if (
        availableBytes >
        reserve &&
        allowed >
        availableBytes-reserve
    )
        allowed =
            availableBytes-reserve;

    uint8_t *arena = NULL;

    uint64_t arenaSize =
        allowed;

    while (
        arenaSize >=
        256ULL*1024*1024
    ) {

        arena =
            malloc(
                arenaSize
            );

        if (arena)
            break;

        arenaSize =
            arenaSize *
            85 /
            100;
    }

    if (arena) {

        for (
            uint64_t i=0;
            i<arenaSize;
            i+=4096
        )
            arena[i] =
                (i>>12) &
                255;
    }

    int hidden =
        224;

    int seq =
        72;

    pthread_t *threads =
        calloc(
            cores,
            sizeof(pthread_t)
        );

    Worker *workers =
        calloc(
            cores,
            sizeof(Worker)
        );

    uint64_t start =
        nowns();

    uint64_t end =
        start +
        (uint64_t)runtime *
        1000000000ULL;

    printf("\n");
    printf("============================================================\n");
    printf(" iQOO 15 MULTIMODAL COMPUTE LAB\n");
    printf("============================================================\n");

    printf(
        "CPU cores          : %ld\n",
        cores
    );

#ifdef __aarch64__
    printf(
        "Vector backend     : ARM64 NEON/FMA\n"
    );
#else
    printf(
        "Vector backend     : generic\n"
    );
#endif

    printf(
        "Physical RAM       : %.2f GiB\n",
        totalKB *
        1024.0 /
        1073741824.0
    );

    printf(
        "RAM arena          : %.2f GiB\n",
        arenaSize /
        1073741824.0
    );

    printf(
        "Runtime            : %d sec\n",
        runtime
    );

    printf(
        "Transformer        : seq=%d hidden=%d\n",
        seq,
        hidden
    );

    printf(
        "Vision             : 384x384 5x5 convolution\n"
    );

    printf(
        "Audio              : 32-harmonic formant synthesis\n"
    );

    printf(
        "Telemetry          : every 10 seconds\n\n"
    );

    for (
        int i=0;
        i<cores;
        i++
    ) {

        workers[i].id =
            i;

        workers[i].hidden =
            hidden;

        workers[i].seq =
            seq;

        workers[i].end_ns =
            end;

        pthread_create(
            &threads[i],
            NULL,
            worker,
            &workers[i]
        );
    }

    uint64_t pass = 0;

    while (
        !STOP &&
        nowns() <
        end
    ) {

        sleep(10);

        memory_sweep(
            arena,
            arenaSize,
            pass++
        );

        double elapsed =
            (
                nowns() -
                start
            ) /
            1e9;

        uint64_t freeKB =
            read_value(
                "MemAvailable:"
            );

        double totalOps = 0;
        uint64_t steps = 0;

        double loss = 0;
        double llm = 0;
        double visionL = 0;
        double audioL = 0;

        for (
            int i=0;
            i<cores;
            i++
        ) {

            totalOps +=
                workers[i].ops;

            steps +=
                workers[i].steps;

            loss +=
                workers[i].loss;

            llm +=
                workers[i].
                attention_loss;

            visionL +=
                workers[i].
                vision_loss;

            audioL +=
                workers[i].
                audio_loss;
        }

        loss /= cores;
        llm /= cores;
        visionL /= cores;
        audioL /= cores;

        double used =
            (
                totalKB -
                freeKB
            ) *
            1024.0 /
            1073741824.0;

        double temperature =
            tempC();

        printf(
            "\n[%6.0fs] "
            "steps=%llu "
            "GFLOP/s=%7.2f\n",
            elapsed,
            (unsigned long long)steps,
            totalOps /
            elapsed /
            1e9
        );

        printf(
            " RAM: %.2f / %.2f GiB",
            used,
            totalKB *
            1024.0 /
            1073741824.0
        );

        if (
            temperature > 0
        )
            printf(
                " | temp %.1f C",
                temperature
            );

        printf("\n");

        printf(
            " Loss total=%8.6f "
            "LLM=%8.6f "
            "vision=%8.6f "
            "voice=%8.6f\n",
            loss,
            llm,
            visionL,
            audioL
        );

        printf(
            " CPU MHz:"
        );

        for (
            int c=0;
            c<cores;
            c++
        ) {

            double mhz =
                cpuMHz(c);

            if (mhz > 0)
                printf(
                    " %d:%.0f",
                    c,
                    mhz
                );
        }

        printf("\n");

        fflush(stdout);

        if (
            temperature >= 88
        ) {

            printf(
                "THERMAL GUARD: cooling for 20 seconds\n"
            );

            fflush(stdout);

            sleep(20);
        }
    }

    STOP = 1;

    for (
        int i=0;
        i<cores;
        i++
    )
        pthread_join(
            threads[i],
            NULL
        );

    double elapsed =
        (
            nowns() -
            start
        ) /
        1e9;

    double ops = 0;

    uint64_t steps = 0;

    for (
        int i=0;
        i<cores;
        i++
    ) {

        ops +=
            workers[i].ops;

        steps +=
            workers[i].steps;
    }

    printf("\n");
    printf("============================================================\n");
    printf(" FINAL REPORT\n");
    printf("============================================================\n");

    printf(
        "Runtime          : %.2f sec\n",
        elapsed
    );

    printf(
        "Training steps   : %llu\n",
        (unsigned long long)steps
    );

    printf(
        "Compute volume   : %.3f TFLOP-equivalent\n",
        ops /
        1e12
    );

    printf(
        "Average compute  : %.2f GFLOP/s\n",
        ops /
        elapsed /
        1e9
    );

    printf(
        "RAM arena        : %.2f GiB\n",
        arenaSize /
        1073741824.0
    );

    printf(
        "Workers          : %ld\n",
        cores
    );

    printf("============================================================\n");

    free(arena);
    free(threads);
    free(workers);

    return 0;
}
EOF

clang -O3 -ffast-math -funroll-loops \
-pthread ~/iqoo15_ml_lab.c -lm \
-o ~/iqoo15_ml_lab && \
RAM_GB=6 DURATION=1200 ~/iqoo15_ml_lab
