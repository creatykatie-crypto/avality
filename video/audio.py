"""Score + sound design for the Avality film, synthesised from scratch.

96 BPM ("effortless flow"). One bar = 2.5 s, so every scene is two bars and
every cue in scene.html lands on a beat.  Writes out/score.wav (48 kHz stereo).
"""
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 48000
DUR = 30.0
BEAT = 60 / 96
BAR = 4 * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)


def b(n):
    return n * BEAT


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env_adsr(n, a, d, s, r, sustain_len):
    t = np.arange(n) / SR
    e = np.zeros(n)
    e = np.where(t < a, t / a, e)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / d, e)
    e = np.where((t >= a + d) & (t < sustain_len), s, e)
    rel = t >= sustain_len
    e[rel] = s * np.exp(-(t[rel] - sustain_len) / r)
    return e


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= N:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 + pan))


def lowpass(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), 'low', output='sos'), x)


def highpass(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), 'high', output='sos'), x)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band', output='sos'), x)


# --------------------------------------------------------------------------
# Instruments
# --------------------------------------------------------------------------
def pad_voice(f, length):
    """Warm, slow pad: a few detuned soft harmonics, filtered."""
    n = int((length + 2.0) * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        for h, amp in ((1, 1.0), (2, 0.35), (3, 0.12), (4, 0.05)):
            s += amp * np.sin(2 * np.pi * ff * h * t + rng.uniform(0, 6.28))
    s *= env_adsr(n, 0.9, 0.5, 0.8, 0.9, length)
    return lowpass(s, 2200) / 6


def pluck(f, length=0.9):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    e = (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.22)
    return lowpass(s * e, 5000)


def bell(f, length=2.4):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, amp, dec in ((1, 1.0, 1.1), (2.0, 0.4, 0.7), (3.01, 0.18, 0.45), (4.2, 0.08, 0.25)):
        s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / dec)
    return s * (1 - np.exp(-t / 0.002))


def sub(f, length):
    n = int((length + 0.3) * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * env_adsr(n, 0.05, 0.2, 0.85, 0.15, length)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.16)


def hat():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    return highpass(rng.standard_normal(n), 7000) * np.exp(-t / 0.018)


def blip(f0, f1, length=0.09):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / length)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.03)


def whoosh(length, lo, hi, peak=0.6):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # sweep a band through the noise in chunks
    out = np.zeros(n)
    chunks = 24
    for c in range(chunks):
        a, z = c * n // chunks, (c + 1) * n // chunks
        k = c / (chunks - 1)
        fc = lo * (hi / lo) ** k
        out[a:z] = bandpass(x, fc * 0.7, min(fc * 1.4, SR / 2 - 100))[a:z]
    e = np.where(t < peak * length, t / (peak * length), (length - t) / ((1 - peak) * length))
    return out * e ** 2


def click():
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    tick = highpass(rng.standard_normal(n), 2500) * np.exp(-t / 0.004)
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.018)
    return 0.6 * tick + body


# --------------------------------------------------------------------------
# Harmony: two bars per scene.
# --------------------------------------------------------------------------
# (bar index, chord MIDI notes, bass root)
A2, C3, D3, E3, F2, G2 = 45, 48, 50, 52, 41, 43
CHORDS = [
    (0, [57, 60, 64, 67, 71], A2),   # Am9      — the endless thread
    (1, [53, 57, 60, 64, 67], F2),   # Fmaj9
    (2, [57, 60, 64, 67, 71], A2),   # Am9      — the crowded week
    (3, [53, 57, 60, 64, 67], F2),   # Fmaj9
    (4, [50, 57, 60, 64, 65], D3),   # Dm9      — the scan
    (5, [55, 60, 62, 65, 69], G2),   # G9sus    — the gap appears
    (6, [48, 55, 59, 62, 64], C3),   # Cmaj9    — the meeting
    (7, [53, 57, 60, 64, 67], F2),   # Fmaj9/C
    (8, [57, 60, 64, 67, 71], A2),   # Am9      — "Everyone's free."
    (9, [55, 60, 62, 65, 69], G2),   # G9sus    — "Finally."
    (10, [48, 55, 59, 62, 64, 67], C3),  # Cmaj9 — Avality, held to the end
]

for bar, notes, root in CHORDS:
    start = bar * BAR
    length = BAR if bar < 10 else DUR - start - 0.6
    level = {0: .55, 1: .55, 2: .7, 3: .7, 8: .5, 9: .5, 10: .85}.get(bar, .8)
    for j, m in enumerate(notes):
        add(pad_voice(hz(m), length), start - 0.15, level * 0.5, pan=(j / (len(notes) - 1) - 0.5) * 0.7)
    if 4 <= bar <= 10:
        add(sub(hz(root), length), start, {8: 0.12, 9: 0.12, 10: 0.22}.get(bar, 0.28))

# Arpeggio — "flow" — from the moment the week appears until the meeting is booked.
for bar, notes, root in CHORDS:
    if not 2 <= bar <= 7:
        continue
    seq = [notes[0] + 12, notes[2] + 12, notes[3] + 12, notes[4] + 12, notes[3] + 12, notes[2] + 12, notes[1] + 12, notes[2] + 12]
    for i in range(8):
        t = bar * BAR + i * BEAT / 2
        vel = 0.5 if bar < 4 else 0.7
        add(pluck(hz(seq[i])), t, 0.16 * vel * (1.0 if i % 2 == 0 else 0.75), pan=0.35 if i % 2 else -0.35)

# Pulse — the only stretch with drums, while Avality does the work (bars 4–7).
for beat_i in range(16, 32):
    t = b(beat_i)
    add(kick(), t, 0.42 if beat_i % 2 == 0 else 0.26)
    add(hat(), t + BEAT / 2, 0.05, pan=0.3)
    add(hat(), t, 0.025, pan=-0.3)

# --------------------------------------------------------------------------
# Sound design — only where an action needs a voice.
# --------------------------------------------------------------------------
# message bubbles land on beats 1..6, rising slightly so the thread feels endless
for i in range(6):
    add(blip(1100 + i * 40, 1500 + i * 40), b(1 + i), 0.12, pan=-0.25 if i % 2 == 0 else 0.25)
# bubbles collapse into the week
add(whoosh(1.4, 300, 2400, peak=0.7), b(7) - 0.1, 0.05)
# the scan
add(whoosh(1.7, 500, 5000, peak=0.55), b(16), 0.035, pan=0)
# the gap: a clear two-note bell, B5 → E6
add(bell(hz(83)), b(19), 0.13, pan=0.1)
add(bell(hz(88)), b(19) + 0.09, 0.08, pan=-0.1)
# three people say yes
for i, m in enumerate((84, 88, 91)):
    add(bell(hz(m), 0.8), b(27 + i * 0.5), 0.05, pan=-0.3 + 0.3 * i)
# the tap
add(click(), b(29) - 0.03, 0.22)
add(bell(hz(96), 1.2), b(29) + 0.05, 0.04)
# the name: the gap closes — C major bell resolve
for i, m in enumerate((72, 79, 84, 88)):
    add(bell(hz(m), 3.5), b(41) + i * 0.035, 0.07, pan=(i - 1.5) * 0.2)

# --------------------------------------------------------------------------
# Space + master
# --------------------------------------------------------------------------
ir_n = int(2.6 * SR)
tt = np.arange(ir_n) / SR
irL = rng.standard_normal(ir_n) * np.exp(-tt / 0.55)
irR = rng.standard_normal(ir_n) * np.exp(-tt / 0.55)
irL, irR = lowpass(irL, 6000), lowpass(irR, 6000)
irL /= np.sqrt((irL ** 2).sum())
irR /= np.sqrt((irR ** 2).sum())
wetL = fftconvolve(L, irL)[:N]
wetR = fftconvolve(R, irR)[:N]
mixL = highpass(L + 0.32 * wetL, 28)
mixR = highpass(R + 0.32 * wetR, 28)

# gentle fade in and out
t = np.arange(N) / SR
fade = np.clip(t / 0.25, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1) ** 1.5
mixL *= fade
mixR *= fade

# soft-clip glue, then normalise to -1 dBFS
st = np.stack([mixL, mixR], 1)
st = np.tanh(st / np.abs(st).max() * 1.2)
st *= 10 ** (-1 / 20) / np.abs(st).max()
wavfile.write('out/score.wav', SR, (st * 32767).astype(np.int16))
print('score done', st.shape, 'rms dBFS', 20 * np.log10(np.sqrt((st ** 2).mean())))
