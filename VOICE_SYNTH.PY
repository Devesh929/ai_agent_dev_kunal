cat > voice_lab.py <<'PY'
import math
import random
import wave
import struct
import csv
import cmath
from pathlib import Path

# ============================================================
# MOBILE VOICE SIGNAL SYNTHESIS + ANALYSIS LAB
# Pure Python - designed to run in Termux
# ============================================================

SAMPLE_RATE = 16000
DURATION_PER_VOWEL = 0.75
F0 = 125.0                   # fundamental pitch in Hz
MAX_HARMONICS = 35
OUTPUT_WAV = "synthetic_voice.wav"
OUTPUT_CSV = "voice_analysis.csv"

random.seed(42)

# Approximate formant frequencies:
# F1, F2, F3
VOWELS = {
    "A": (730, 1090, 2440),
    "E": (530, 1840, 2480),
    "I": (270, 2290, 3010),
    "O": (570, 840, 2410),
    "U": (300, 870, 2240),
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def db(x):
    if x <= 1e-12:
        return -120.0
    return 20.0 * math.log10(x)


def rms(signal):
    return math.sqrt(sum(x*x for x in signal) / max(1, len(signal)))


def peak(signal):
    return max(abs(x) for x in signal)


def zero_crossing_rate(signal):
    count = 0

    for a, b in zip(signal[:-1], signal[1:]):
        if (a < 0 <= b) or (a >= 0 > b):
            count += 1

    return count / len(signal)


# ============================================================
# FORMANT MODEL
#
# Instead of filtering afterward, each harmonic gets weighted
# depending on its distance from vocal tract resonances.
# ============================================================

def resonance(freq, center, bandwidth):

    distance = (freq - center) / bandwidth

    return 1.0 / math.sqrt(
        1.0 + distance * distance
    )


def formant_gain(freq, formants):

    f1, f2, f3 = formants

    g1 = resonance(freq, f1, 90)
    g2 = resonance(freq, f2, 120)
    g3 = resonance(freq, f3, 180)

    # weighted mixture
    gain = (
        1.00 * g1 +
        0.70 * g2 +
        0.35 * g3
    )

    return gain


# ============================================================
# SYNTHESIZE ONE VOWEL
# ============================================================

def synthesize_vowel(name, formants, duration):

    samples = []

    total = int(duration * SAMPLE_RATE)

    phases = [
        random.random() * 2 * math.pi
        for _ in range(MAX_HARMONICS)
    ]

    for n in range(total):

        t = n / SAMPLE_RATE

        # ----------------------------------------------------
        # Pitch vibrato
        # ----------------------------------------------------

        vibrato_rate = 5.2
        vibrato_depth = 0.012

        pitch = F0 * (
            1 +
            vibrato_depth *
            math.sin(2 * math.pi * vibrato_rate * t)
        )

        # ----------------------------------------------------
        # Slow pitch drift
        # ----------------------------------------------------

        pitch *= (
            1 +
            0.008 *
            math.sin(2 * math.pi * 0.8 * t)
        )

        sample = 0.0

        # ----------------------------------------------------
        # Harmonic glottal source
        # ----------------------------------------------------

        for h in range(1, MAX_HARMONICS + 1):

            freq = h * pitch

            if freq >= SAMPLE_RATE / 2:
                break

            # Natural harmonic rolloff
            harmonic_amp = 1.0 / (h ** 1.25)

            # Vocal tract resonance
            vocal_gain = formant_gain(
                freq,
                formants
            )

            amp = harmonic_amp * vocal_gain

            sample += amp * math.sin(
                2 * math.pi * freq * t +
                phases[h - 1]
            )

        # ----------------------------------------------------
        # Breath noise
        # ----------------------------------------------------

        breath = random.uniform(-1, 1) * 0.018

        sample += breath

        # ----------------------------------------------------
        # Attack / Release envelope
        # ----------------------------------------------------

        attack = 0.06
        release = 0.10

        if t < attack:

            envelope = t / attack

        elif t > duration - release:

            envelope = max(
                0,
                (duration - t) / release
            )

        else:

            envelope = 1.0

        # slight human amplitude modulation
        envelope *= (
            0.96 +
            0.04 *
            math.sin(2 * math.pi * 3.1 * t)
        )

        sample *= envelope

        samples.append(sample)

    # normalize individual vowel
    p = peak(samples)

    if p > 0:

        samples = [
            0.82 * x / p
            for x in samples
        ]

    return samples


# ============================================================
# BUILD FULL SPEECH-LIKE SIGNAL
# ============================================================

voice = []
regions = []

print()
print("=" * 65)
print("       TERMUX VOICE SYNTHESIS + SIGNAL ANALYSIS LAB")
print("=" * 65)
print()

cursor = 0

for vowel, formants in VOWELS.items():

    print(
        f"Synthesizing vowel {vowel} "
        f"with formants {formants}"
    )

    segment = synthesize_vowel(
        vowel,
        formants,
        DURATION_PER_VOWEL
    )

    start = cursor
    voice.extend(segment)

    cursor += len(segment)

    regions.append(
        (
            vowel,
            start,
            cursor,
            formants
        )
    )

    # tiny pause
    silence_samples = int(
        0.08 * SAMPLE_RATE
    )

    voice.extend(
        [0.0] * silence_samples
    )

    cursor += silence_samples


# ============================================================
# GLOBAL NORMALIZATION
# ============================================================

p = peak(voice)

if p > 0:

    voice = [
        0.95 * x / p
        for x in voice
    ]


# ============================================================
# WRITE WAV FILE
# ============================================================

with wave.open(
    OUTPUT_WAV,
    "w"
) as wf:

    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)

    for x in voice:

        val = int(
            max(
                -32767,
                min(
                    32767,
                    x * 32767
                )
            )
        )

        wf.writeframes(
            struct.pack("<h", val)
        )


# ============================================================
# AUTOCORRELATION PITCH ESTIMATION
# ============================================================

def estimate_pitch(signal):

    # use only limited signal
    x = signal[:4096]

    mean = sum(x) / len(x)

    x = [
        sample - mean
        for sample in x
    ]

    minimum_pitch = 70
    maximum_pitch = 350

    min_lag = int(
        SAMPLE_RATE / maximum_pitch
    )

    max_lag = int(
        SAMPLE_RATE / minimum_pitch
    )

    best_lag = None
    best_corr = -1e30

    for lag in range(
        min_lag,
        max_lag + 1
    ):

        correlation = 0.0

        for i in range(
            len(x) - lag
        ):

            correlation += (
                x[i] *
                x[i + lag]
            )

        if correlation > best_corr:

            best_corr = correlation
            best_lag = lag

    if best_lag:

        return (
            SAMPLE_RATE /
            best_lag
        )

    return 0


# ============================================================
# SIMPLE DFT
#
# We only inspect selected frequencies instead of computing
# a full FFT. This keeps it pure Python and mobile friendly.
# ============================================================

def spectral_magnitude(
    signal,
    frequency
):

    n_samples = len(signal)

    real = 0.0
    imag = 0.0

    for n, x in enumerate(signal):

        angle = (
            -2 *
            math.pi *
            frequency *
            n /
            SAMPLE_RATE
        )

        real += (
            x *
            math.cos(angle)
        )

        imag += (
            x *
            math.sin(angle)
        )

    return (
        math.sqrt(
            real*real +
            imag*imag
        ) /
        n_samples
    )


# ============================================================
# ASCII SPECTRUM
# ============================================================

def ascii_spectrum(signal):

    print()
    print("=" * 65)
    print("ASCII FREQUENCY SPECTRUM")
    print("=" * 65)

    frequencies = list(
        range(
            100,
            3501,
            100
        )
    )

    magnitudes = []

    short_signal = signal[:2048]

    for frequency in frequencies:

        magnitude = spectral_magnitude(
            short_signal,
            frequency
        )

        magnitudes.append(magnitude)

    maximum = max(magnitudes)

    for frequency, magnitude in zip(
        frequencies,
        magnitudes
    ):

        relative = (
            magnitude / maximum
            if maximum
            else 0
        )

        bars = int(
            relative * 45
        )

        print(
            f"{frequency:4d} Hz | "
            +
            "█" * bars
        )


# ============================================================
# ANALYSIS
# ============================================================

print()
print("=" * 65)
print("GLOBAL SIGNAL ANALYSIS")
print("=" * 65)

duration = (
    len(voice) /
    SAMPLE_RATE
)

global_rms = rms(voice)

global_peak = peak(voice)

global_zcr = zero_crossing_rate(
    voice
)

print(
    f"Sample rate          : {SAMPLE_RATE} Hz"
)

print(
    f"Samples              : {len(voice)}"
)

print(
    f"Duration             : {duration:.3f} sec"
)

print(
    f"Peak amplitude       : {global_peak:.4f}"
)

print(
    f"RMS amplitude        : {global_rms:.4f}"
)

print(
    f"RMS level            : {db(global_rms):.2f} dBFS"
)

print(
    f"Zero crossing rate   : {global_zcr:.5f}"
)


# ============================================================
# ANALYZE EACH VOWEL
# ============================================================

results = []

print()
print("=" * 65)
print("VOWEL ANALYSIS")
print("=" * 65)

for (
    vowel,
    start,
    end,
    formants
) in regions:

    segment = voice[
        start:end
    ]

    # discard attack for pitch estimation
    analysis_start = int(
        0.15 *
        SAMPLE_RATE
    )

    analysis_segment = segment[
        analysis_start:
        analysis_start + 4096
    ]

    pitch = estimate_pitch(
        analysis_segment
    )

    segment_rms = rms(
        segment
    )

    segment_peak = peak(
        segment
    )

    zcr = zero_crossing_rate(
        segment
    )

    print()
    print(
        f"Vowel: {vowel}"
    )

    print(
        f"  Estimated pitch : "
        f"{pitch:.2f} Hz"
    )

    print(
        f"  RMS             : "
        f"{segment_rms:.4f}"
    )

    print(
        f"  Peak            : "
        f"{segment_peak:.4f}"
    )

    print(
        f"  Zero crossing   : "
        f"{zcr:.5f}"
    )

    print(
        f"  Target formants : "
        f"{formants[0]}, "
        f"{formants[1]}, "
        f"{formants[2]} Hz"
    )

    # Formant-region spectral amplitudes

    amplitudes = []

    for frequency in formants:

        amp = spectral_magnitude(
            analysis_segment[:2048],
            frequency
        )

        amplitudes.append(
            amp
        )

    print(
        "  Spectral energy :"
    )

    for frequency, amp in zip(
        formants,
        amplitudes
    ):

        print(
            f"      {frequency:4d} Hz "
            f"-> {amp:.6f}"
        )

    results.append(
        [
            vowel,
            pitch,
            segment_rms,
            segment_peak,
            zcr,
            formants[0],
            formants[1],
            formants[2],
            amplitudes[0],
            amplitudes[1],
            amplitudes[2],
        ]
    )


# ============================================================
# HARMONIC ANALYSIS
# ============================================================

print()
print("=" * 65)
print("HARMONIC ANALYSIS OF FIRST VOWEL")
print("=" * 65)

first_segment = voice[
    regions[0][1]:
    regions[0][2]
]

analysis = first_segment[
    int(
        0.2 *
        SAMPLE_RATE
    ):
]

for h in range(
    1,
    16
):

    freq = h * F0

    magnitude = spectral_magnitude(
        analysis[:2048],
        freq
    )

    bars = int(
        min(
            40,
            magnitude * 180
        )
    )

    print(
        f"H{h:02d} "
        f"{freq:7.1f} Hz "
        f"{magnitude:8.5f} "
        +
        "▓" * bars
    )


# ============================================================
# ASCII SPECTRUM
# ============================================================

ascii_spectrum(
    first_segment[
        int(
            0.15 *
            SAMPLE_RATE
        ):
    ]
)


# ============================================================
# SAVE CSV ANALYSIS
# ============================================================

with open(
    OUTPUT_CSV,
    "w",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow(
        [
            "vowel",
            "estimated_pitch_hz",
            "rms",
            "peak",
            "zero_crossing_rate",
            "formant_1_hz",
            "formant_2_hz",
            "formant_3_hz",
            "formant_1_energy",
            "formant_2_energy",
            "formant_3_energy",
        ]
    )

    writer.writerows(
        results
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 65)
print("EXPERIMENT COMPLETE")
print("=" * 65)

print()

print(
    "Generated audio :",
    Path(
        OUTPUT_WAV
    ).resolve()
)

print(
    "Analysis CSV    :",
    Path(
        OUTPUT_CSV
    ).resolve()
)

print()
print(
    "The WAV contains a simulated vocal tract producing:"
)

print(
    "A -> E -> I -> O -> U"
)

print()

print(
    "Fundamental pitch:",
    F0,
    "Hz"
)

print()

print(
    "Experiment demonstrates:"
)

print(
    "  - Glottal harmonic source"
)

print(
    "  - Vocal tract resonances / formants"
)

print(
    "  - Harmonic spectral structure"
)

print(
    "  - Pitch estimation using autocorrelation"
)

print(
    "  - RMS / peak / zero-crossing analysis"
)

print(
    "  - Frequency-domain analysis"
)

print(
    "  - Voice signal synthesis"
)

print()
PY

python voice_lab.py
