/* GB/T 6278-2012 simulated programme noise.
   Pink-noise magnitude 1/sqrt(f) times the figure-2 weighting network.
   Keep the analog coefficients identical to desktop_app/programme_noise.py. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    root.ProgrammeNoise = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ANALOG_B = [0, 0, 1138852028.0449145, 0, 0, 0];
  const ANALOG_A = [
    1,
    115323.33109599353,
    1821497859.3101158,
    997848351403.9052,
    138963679056551.78,
    4597229662083177,
  ];

  function cadd(a, b) {
    return [a[0] + b[0], a[1] + b[1]];
  }

  function cmul(a, b) {
    return [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
  }

  function polyval(coeff, s) {
    let y = [0, 0];
    for (let i = 0; i < coeff.length; i++) {
      y = cadd(cmul(y, s), [coeff[i], 0]);
    }
    return y;
  }

  function analogMagnitude(freq) {
    const s = [0, 2 * Math.PI * freq];
    const num = polyval(ANALOG_B, s);
    const den = polyval(ANALOG_A, s);
    const d2 = den[0] * den[0] + den[1] * den[1];
    const re = (num[0] * den[0] + num[1] * den[1]) / d2;
    const im = (num[1] * den[0] - num[0] * den[1]) / d2;
    return Math.hypot(re, im);
  }

  const BANDPASS_ORDER = 4;
  const BAND_MIN_HZ = 20;
  const BAND_MAX_HZ = 20000;
  const MIN_BAND_RATIO = Math.pow(2, 1 / 6);

  function sectionQ(sectionIndex) {
    return 1 / (2 * Math.sin(((2 * sectionIndex - 1) * Math.PI) / (2 * BANDPASS_ORDER)));
  }

  function normalizeBand(fLow, fHigh, fs) {
    const hiLim = Math.min(BAND_MAX_HZ, 0.98 * fs / 2);
    let lo = Number(fLow);
    let hi = Number(fHigh);
    if (!isFinite(lo)) lo = BAND_MIN_HZ;
    if (!isFinite(hi)) hi = hiLim;
    lo = Math.min(Math.max(lo, BAND_MIN_HZ), hiLim);
    hi = Math.min(Math.max(hi, BAND_MIN_HZ), hiLim);
    if (hi < lo * MIN_BAND_RATIO) {
      hi = Math.min(hiLim, lo * MIN_BAND_RATIO);
      if (hi < lo * MIN_BAND_RATIO) lo = Math.max(BAND_MIN_HZ, hi / MIN_BAND_RATIO);
    }
    return [lo, hi];
  }

  function bandIsFull(fLow, fHigh) {
    return fLow <= 20.5 && fHigh >= 19900;
  }

  function rbjSection(kind, f0, fs, q) {
    const w0 = 2 * Math.PI * f0 / fs;
    const cw = Math.cos(w0);
    const alpha = Math.sin(w0) / (2 * q);
    let b0;
    let b1;
    let b2;
    if (kind === "low") {
      b0 = (1 - cw) / 2;
      b1 = 1 - cw;
      b2 = (1 - cw) / 2;
    } else {
      b0 = (1 + cw) / 2;
      b1 = -(1 + cw);
      b2 = (1 + cw) / 2;
    }
    const a0 = 1 + alpha;
    return [b0 / a0, b1 / a0, b2 / a0, 1, (-2 * cw) / a0, (1 - alpha) / a0];
  }

  function bandpassSections(fs, fLow, fHigh) {
    const band = normalizeBand(fLow, fHigh, fs);
    if (bandIsFull(band[0], band[1])) return [];
    const sections = [];
    for (let k = 1; k <= 2; k++) {
      const q = sectionQ(k);
      sections.push(rbjSection("high", band[0], fs, q));
      sections.push(rbjSection("low", band[1], fs, q));
    }
    return sections;
  }

  function bandpassDb(freq, fs, fLow, fHigh) {
    const sections = bandpassSections(fs, fLow, fHigh);
    if (!sections.length) return 0;
    const w = 2 * Math.PI * freq / fs;
    const zm1 = [Math.cos(-w), Math.sin(-w)];
    const zm2 = cmul(zm1, zm1);
    let h = [1, 0];
    for (let i = 0; i < sections.length; i++) {
      const s = sections[i];
      const num = cadd(cadd([s[0], 0], cmul([s[1], 0], zm1)), cmul([s[2], 0], zm2));
      const den = cadd(cadd([s[3], 0], cmul([s[4], 0], zm1)), cmul([s[5], 0], zm2));
      const d2 = den[0] * den[0] + den[1] * den[1];
      const g = [(num[0] * den[0] + num[1] * den[1]) / d2, (num[1] * den[0] - num[0] * den[1]) / d2];
      h = cmul(h, g);
    }
    return 20 * Math.log10(Math.hypot(h[0], h[1]) + 1e-30);
  }

  function transform(re, im, inverse) {
    const n = re.length;
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        let tmp = re[i];
        re[i] = re[j];
        re[j] = tmp;
        tmp = im[i];
        im[i] = im[j];
        im[j] = tmp;
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = (inverse ? 2 : -2) * Math.PI / len;
      const wlenRe = Math.cos(ang);
      const wlenIm = Math.sin(ang);
      for (let i = 0; i < n; i += len) {
        let wRe = 1;
        let wIm = 0;
        const half = len >> 1;
        for (let j = 0; j < half; j++) {
          const idx = i + j + half;
          const vRe = re[idx] * wRe - im[idx] * wIm;
          const vIm = re[idx] * wIm + im[idx] * wRe;
          const uRe = re[i + j];
          const uIm = im[i + j];
          re[i + j] = uRe + vRe;
          im[i + j] = uIm + vIm;
          re[idx] = uRe - vRe;
          im[idx] = uIm - vIm;
          const nextRe = wRe * wlenRe - wIm * wlenIm;
          wIm = wRe * wlenIm + wIm * wlenRe;
          wRe = nextRe;
        }
      }
    }
    if (inverse) {
      const scale = 1 / n;
      for (let i = 0; i < n; i++) {
        re[i] *= scale;
        im[i] *= scale;
      }
    }
  }

  function bandpassGain(freq, fs, fLow, fHigh) {
    const sections = bandpassSections(fs, fLow, fHigh);
    if (!sections.length) return [1, 0];
    const w = (2 * Math.PI * freq) / fs;
    const zm1 = [Math.cos(-w), Math.sin(-w)];
    const zm2 = cmul(zm1, zm1);
    let h = [1, 0];
    for (let i = 0; i < sections.length; i++) {
      const s = sections[i];
      const num = cadd(cadd([s[0], 0], cmul([s[1], 0], zm1)), cmul([s[2], 0], zm2));
      const den = cadd(cadd([s[3], 0], cmul([s[4], 0], zm1)), cmul([s[5], 0], zm2));
      const d2 = den[0] * den[0] + den[1] * den[1];
      h = cmul(h, [
        (num[0] * den[0] + num[1] * den[1]) / d2,
        (num[1] * den[0] - num[0] * den[1]) / d2,
      ]);
    }
    return h;
  }

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function synthesize(sampleRate, nPow, seed) {
    const fs = sampleRate | 0;
    const pow = nPow == null ? 18 : nPow | 0;
    const n = 1 << pow;
    const re = new Float64Array(n);
    const im = new Float64Array(n);
    const rng = mulberry32(seed == null ? 6278 : seed | 0);
    const half = n >> 1;
    for (let k = 1; k < half; k++) {
      const freq = (k * fs) / n;
      const amp = analogMagnitude(freq) / Math.sqrt(freq);
      const phase = rng() * 2 * Math.PI;
      const cre = amp * Math.cos(phase);
      const cim = amp * Math.sin(phase);
      re[k] = cre;
      im[k] = cim;
      re[n - k] = cre;
      im[n - k] = -cim;
    }
    transform(re, im, true);
    let energy = 0;
    for (let i = 0; i < n; i++) energy += re[i] * re[i];
    const rms = Math.sqrt(energy / n);
    const out = new Float32Array(n);
    const inv = 1 / rms;
    let peak = 0;
    for (let i = 0; i < n; i++) {
      const v = re[i] * inv;
      out[i] = v;
      const a = v < 0 ? -v : v;
      if (a > peak) peak = a;
    }
    out.crestFactor = peak;
    return out;
  }

  function applyBandpass(samples, sampleRate, fLow, fHigh) {
    const fs = sampleRate | 0;
    const band = normalizeBand(fLow, fHigh, fs);
    if (bandIsFull(band[0], band[1])) return samples;
    const n = samples.length;
    const re = new Float64Array(n);
    const im = new Float64Array(n);
    for (let i = 0; i < n; i++) re[i] = samples[i];
    transform(re, im, false);
    const half = n >> 1;
    for (let k = 0; k <= half; k++) {
      const h = bandpassGain((k * fs) / n, fs, band[0], band[1]);
      const nr = re[k] * h[0] - im[k] * h[1];
      const ni = re[k] * h[1] + im[k] * h[0];
      re[k] = nr;
      im[k] = ni;
      if (k > 0 && k < half) {
        re[n - k] = nr;
        im[n - k] = -ni;
      }
    }
    transform(re, im, true);
    let energy = 0;
    for (let i = 0; i < n; i++) energy += re[i] * re[i];
    const inv = 1 / Math.sqrt(energy / n);
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) out[i] = re[i] * inv;
    return out;
  }

  return {
    analogMagnitude: analogMagnitude,
    synthesize: synthesize,
    normalizeBand: normalizeBand,
    bandIsFull: bandIsFull,
    bandpassDb: bandpassDb,
    applyBandpass: applyBandpass,
  };
});
