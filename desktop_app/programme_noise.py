"""GB/T 6278-2012 simulated programme noise.

Pink noise (power spectral density proportional to 1/f) passed through the
weighting network of GB/T 6278-2012 figure 2. The network is the passive
ladder in that figure:

    source -- 430 ohm -- 2.2 uF --+-- 330 ohm -- 2.2 uF --+-- 0.47 uF --+-- out
                                  |                      |              |
                                3.3 kohm               3.3 kohm        10 kohm
                                  |                      |              |
                                 91 nF                  68 nF          gnd

Overall gain is arbitrary. Conformance is the 1/3-octave power spectrum in
the standard table, which has a bilateral tolerance at each centre frequency.
Phase is not specified; synthesis uses a random phase so the time signal is
Gaussian and is not clipped.
"""

import numpy as np

# Analog transfer function of figure 2, highest power of s first.
# Numerator is proportional to s^3 (three series capacitors).
ANALOG_B = np.array(
    [0.0, 0.0, 1138852028.0449145, 0.0, 0.0, 0.0],
    dtype=np.float64,
)
ANALOG_A = np.array(
    [
        1.0,
        115323.33109599353,
        1821497859.3101158,
        997848351403.9052,
        138963679056551.78,
        4597229662083177.0,
    ],
    dtype=np.float64,
)

CENTER_HZ = np.array(
    [
        20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200,
        250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
        2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000,
    ],
    dtype=np.float64,
)
TARGET_DB = np.array(
    [
        -13.5, -10.2, -7.4, -5.2, -3.5, -2.3, -1.4, -0.9, -0.5, -0.2, -0.1,
        0, 0, 0, 0, 0, 0, -0.1, -0.3, -0.6, -1.0,
        -1.6, -2.5, -3.7, -5.1, -7.0, -9.4, -11.9, -14.8, -18.2, -21.6,
    ],
    dtype=np.float64,
)
TOLERANCE_DB = np.array(
    [
        3.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.8, 0.6, 0.5, 0.5,
        0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.6, 0.7, 0.8, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 2.0, 3.0,
    ],
    dtype=np.float64,
)


def analog_response(freqs):
    """Complex gain of the figure-2 network at frequencies in hertz."""
    freqs = np.asarray(freqs, dtype=np.float64)
    s = 1j * (2.0 * np.pi) * freqs
    return np.polyval(ANALOG_B, s) / np.polyval(ANALOG_A, s)


def third_octave_levels_db(n_points=24000):
    """Unnormalised 1/3-octave powers, in dB, of ideal pink noise through figure 2.

    Integration limits are the nominal 1/3-octave edges fc / 2**(1/6) .. fc * 2**(1/6).
    A constant added to every band is meaningless; compare with spectrum_fits_gbt6278.
    """
    f = np.geomspace(8.0, 40000.0, int(n_points))
    density = (np.abs(analog_response(f)) ** 2) / f
    levels = np.empty(CENTER_HZ.shape[0], dtype=np.float64)
    half = 2.0 ** (1.0 / 6.0)
    for i, centre in enumerate(CENTER_HZ):
        f1 = centre / half
        f2 = centre * half
        mask = (f >= f1) & (f < f2)
        power = np.trapezoid(density[mask], f[mask])
        levels[i] = 10.0 * np.log10(power)
    return levels


def spectrum_fits_gbt6278(levels_db):
    """Return (fits, margin_db).

    margin_db is how far the allowed reference-offset interval extends.
    Positive margin means every band can sit inside its tolerance together.
    """
    levels_db = np.asarray(levels_db, dtype=np.float64)
    lo = -np.inf
    hi = np.inf
    for reading, target, tol in zip(levels_db, TARGET_DB, TOLERANCE_DB):
        lo = max(lo, (target - tol) - reading)
        hi = min(hi, (target + tol) - reading)
    return bool(lo <= hi), float(hi - lo)


# 24 dB/octave Butterworth, the slope used for band-limited loudspeaker noise.
BANDPASS_ORDER = 4
BAND_MIN_HZ = 20.0
BAND_MAX_HZ = 20000.0
# Handles cannot sit closer than one 1/3-octave, so the passband stays real.
MIN_BAND_RATIO = 2.0 ** (1.0 / 6.0)


def _section_q(section_index):
    """Q of one second-order section in a 4th-order Butterworth cascade."""
    return 1.0 / (2.0 * np.sin((2.0 * section_index - 1.0) * np.pi / (2.0 * BANDPASS_ORDER)))


def normalize_band(f_low, f_high, fs):
    """Clamp cutoffs into 20 Hz .. min(20 kHz, 0.98*Nyquist) and keep them apart."""
    hi_lim = min(BAND_MAX_HZ, 0.98 * float(fs) / 2.0)
    lo = float(f_low)
    hi = float(f_high)
    if not np.isfinite(lo):
        lo = BAND_MIN_HZ
    if not np.isfinite(hi):
        hi = hi_lim
    lo = min(max(lo, BAND_MIN_HZ), hi_lim)
    hi = min(max(hi, BAND_MIN_HZ), hi_lim)
    if hi < lo * MIN_BAND_RATIO:
        hi = min(hi_lim, lo * MIN_BAND_RATIO)
        if hi < lo * MIN_BAND_RATIO:
            lo = max(BAND_MIN_HZ, hi / MIN_BAND_RATIO)
    return lo, hi


def band_is_full(f_low, f_high):
    """True when the knob is at both ends and the programme spectrum must stay untouched."""
    return float(f_low) <= 20.5 and float(f_high) >= 19900.0


def _rbj_section(kind, f0, fs, q):
    """Bilinear lowpass or highpass biquad, a0 normalised to 1. Returns b0,b1,b2,1,a1,a2."""
    w0 = 2.0 * np.pi * float(f0) / float(fs)
    cw = np.cos(w0)
    alpha = np.sin(w0) / (2.0 * q)
    if kind == "low":
        b0 = (1.0 - cw) / 2.0
        b1 = 1.0 - cw
        b2 = (1.0 - cw) / 2.0
    else:
        b0 = (1.0 + cw) / 2.0
        b1 = -(1.0 + cw)
        b2 = (1.0 + cw) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cw
    a2 = 1.0 - alpha
    return (b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0)


def bandpass_sos(fs, f_low, f_high):
    """Four biquads: two highpass then two lowpass. Empty when the band is full-span."""
    f_low, f_high = normalize_band(f_low, f_high, fs)
    if band_is_full(f_low, f_high):
        return ()
    sections = []
    for k in (1, 2):
        q = _section_q(k)
        sections.append(_rbj_section("high", f_low, fs, q))
        sections.append(_rbj_section("low", f_high, fs, q))
    return tuple(sections)


def bandpass_response(freqs, fs, f_low, f_high):
    """Complex gain of the bandpass placed after the programme source."""
    freqs = np.asarray(freqs, dtype=np.float64)
    sections = bandpass_sos(fs, f_low, f_high)
    if not sections:
        return np.ones(freqs.shape, dtype=np.complex128)
    # z^-1. At 0 Hz this is 1, and the highpass numerator is zero there.
    w = 2.0 * np.pi * freqs / float(fs)
    zm1 = np.exp(-1j * w)
    zm2 = zm1 * zm1
    h = np.ones(freqs.shape, dtype=np.complex128)
    for b0, b1, b2, a0, a1, a2 in sections:
        h *= (b0 + b1 * zm1 + b2 * zm2) / (a0 + a1 * zm1 + a2 * zm2)
    return h


def apply_bandpass(samples, fs, f_low, f_high):
    """Filter one periodic programme buffer and restore RMS to 1.

    Full-span cutoffs (20 Hz and 20 kHz) return the source unchanged, so the
    GB/T 6278 spectrum is not tilted by a filter parked at the band edges.
    Narrower cutoffs are applied to the source spectrum, then the result is
    scaled so the displayed level remains the RMS after the filter.
    """
    samples = np.asarray(samples, dtype=np.float64)
    f_low, f_high = normalize_band(f_low, f_high, fs)
    if band_is_full(f_low, f_high):
        rms = float(np.sqrt(np.mean(samples * samples)))
        if rms <= 0.0:
            raise RuntimeError("programme buffer is silent")
        return samples / rms
    n = samples.shape[0]
    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(n, d=1.0 / float(fs))
    spectrum *= bandpass_response(freqs, fs, f_low, f_high)
    filtered = np.fft.irfft(spectrum, n=n)
    rms = float(np.sqrt(np.mean(filtered * filtered)))
    if rms <= 0.0:
        raise RuntimeError("bandpass removed the programme signal")
    return filtered / rms


def synthesize(fs, n_pow=18, seed=6278):
    """One seamless period of programme noise, RMS normalised to 1.

    Magnitude of each FFT bin is |H(f)| / sqrt(f), the spectrum of pink noise
    through figure 2. Phase is random, so the signal is Gaussian and unclipped.
    The buffer repeats without a splice because it is one FFT period.
    """
    fs = int(fs)
    if fs < 4000:
        raise ValueError("sample rate is too low for a 20 Hz programme signal")
    n = 1 << int(n_pow)
    rng = np.random.default_rng(int(seed))
    k = np.arange(1, n // 2, dtype=np.float64)
    freq = k * (fs / float(n))
    amplitude = np.abs(analog_response(freq)) / np.sqrt(freq)
    phase = rng.uniform(0.0, 2.0 * np.pi, size=amplitude.shape[0])
    spectrum = np.zeros(n // 2 + 1, dtype=np.complex128)
    spectrum[1:-1] = amplitude * np.exp(1j * phase)
    samples = np.fft.irfft(spectrum, n=n)
    rms = float(np.sqrt(np.mean(samples * samples)))
    if rms <= 0.0:
        raise RuntimeError("programme synthesis produced silence")
    return samples / rms
