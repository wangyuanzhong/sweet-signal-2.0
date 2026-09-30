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

  function ifft(re, im) {
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
      const ang = (2 * Math.PI) / len;
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
    const scale = 1 / n;
    for (let i = 0; i < n; i++) {
      re[i] *= scale;
      im[i] *= scale;
    }
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
    ifft(re, im);
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

  return {
    analogMagnitude: analogMagnitude,
    synthesize: synthesize,
  };
});
