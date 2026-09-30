"""GB/T 6278-2012 simulated programme signal: spectrum shape and synthesis."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop_app"))

import programme_noise as pn


class ProgrammeSpectrumTest(unittest.TestCase):
    def test_analog_weighting_fits_gbt6278_tolerances(self):
        levels = pn.third_octave_levels_db()
        self.assertEqual(len(levels), len(pn.CENTER_HZ))
        ok, margin_db = pn.spectrum_fits_gbt6278(levels)
        self.assertTrue(ok, f"spectrum outside GB/T 6278 window, margin {margin_db}")
        self.assertGreater(margin_db, 0.05)

    def test_band_edges_are_the_standard_centres(self):
        self.assertEqual(pn.CENTER_HZ[0], 20.0)
        self.assertEqual(pn.CENTER_HZ[-1], 20000.0)
        self.assertIn(31.5, pn.CENTER_HZ)
        self.assertEqual(len(pn.CENTER_HZ), 31)

    def test_synthesis_is_unclipped_unit_rms_with_design_magnitude(self):
        fs = 48000
        n_pow = 16
        x = pn.synthesize(fs, n_pow=n_pow, seed=6278)
        n = x.shape[0]
        self.assertEqual(n, 1 << n_pow)
        rms = float(np.sqrt(np.mean(x * x)))
        self.assertAlmostEqual(rms, 1.0, places=5)
        crest = float(np.max(np.abs(x)) / rms)
        self.assertGreater(crest, 3.0)
        self.assertLess(crest, 12.0)
        self.assertTrue(np.all(np.isfinite(x)))

        spec = np.fft.rfft(x)
        k = np.arange(1, spec.shape[0] - 1)
        freq = k * (fs / n)
        design = np.abs(pn.analog_response(freq)) / np.sqrt(freq)
        got = np.abs(spec[1:-1])
        ratio = got / np.maximum(design, 1e-30)
        self.assertLess(float(np.max(ratio) / np.min(ratio) - 1.0), 1e-6)

    def test_sample_rates_used_by_playback_keep_full_band(self):
        for fs in (44100, 48000, 96000):
            x = pn.synthesize(fs, n_pow=14, seed=3)
            self.assertEqual(x.shape[0], 1 << 14)
            self.assertAlmostEqual(float(np.sqrt(np.mean(x * x))), 1.0, places=4)

    def test_full_span_bandpass_leaves_programme_unchanged(self):
        fs = 48000
        x = pn.synthesize(fs, n_pow=12, seed=1)
        y = pn.apply_bandpass(x, fs, 20, 20000)
        self.assertAlmostEqual(float(np.sqrt(np.mean(y * y))), 1.0, places=5)
        self.assertLess(float(np.max(np.abs(y - x))), 1e-8)

    def test_bandpass_is_fourth_order_butterworth_after_the_source(self):
        fs = 48000
        f_low, f_high = 2000.0, 8000.0
        freqs = np.array([200.0, 2000.0, 4000.0, 8000.0])
        got = 20.0 * np.log10(np.abs(pn.bandpass_response(freqs, fs, f_low, f_high)) + 1e-30)
        # One decade below a 24 dB/oct highpass is about -80 dB.
        self.assertLess(got[0], -70.0)
        self.assertGreater(got[0], -90.0)
        # Butterworth cutoff is -3 dB when the other edge is far away.
        self.assertAlmostEqual(got[1], -3.0, delta=0.4)
        self.assertGreater(got[2], -1.0)
        self.assertAlmostEqual(got[3], -3.0, delta=0.6)

    def test_filtered_period_keeps_unit_rms_and_cuts_bass(self):
        fs = 48000
        x = pn.synthesize(fs, n_pow=14, seed=9)
        y = pn.apply_bandpass(x, fs, 2000, 8000)
        self.assertAlmostEqual(float(np.sqrt(np.mean(y * y))), 1.0, places=4)
        spec_x = np.abs(np.fft.rfft(x))
        spec_y = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(x.shape[0], d=1.0 / fs)
        bass = (freqs > 150) & (freqs < 250)
        mid = (freqs > 3500) & (freqs < 4500)
        bass_drop = 20.0 * np.log10(np.mean(spec_y[bass]) / np.mean(spec_x[bass]))
        self.assertLess(bass_drop, -60.0)
        # Makeup restores total RMS, so the passband is louder than the full-band signal.
        mid_boost = 20.0 * np.log10(np.mean(spec_y[mid]) / np.mean(spec_x[mid]))
        self.assertGreater(mid_boost, 0.0)


if __name__ == "__main__":
    unittest.main()
