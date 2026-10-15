import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from batt import CellParams, ocv, docv, simulate_cell, drive_cycle, hppc_profile, fit_rc, coulomb_count, ekf_soc  # noqa


class TestBattery(unittest.TestCase):
    def test_ocv_monotone_and_derivative(self):
        z = np.linspace(0.05, 0.95, 50)
        self.assertTrue(np.all(np.diff(ocv(z)) > 0))
        h = 1e-6
        np.testing.assert_allclose((ocv(z + h) - ocv(z - h)) / (2 * h), docv(z), rtol=1e-5)

    def test_coulomb_count_exact_without_noise(self):
        p = CellParams()
        I = drive_cycle(1800, 1.0, seed=1)
        m = simulate_cell(I, 1.0, p, z0=0.8, v_noise=0, i_noise=0)
        np.testing.assert_allclose(coulomb_count(m["i_meas"], 1.0, p.Q, 0.8), m["z"], atol=1e-12)

    def test_rest_voltage_equals_ocv(self):
        p = CellParams()
        m = simulate_cell(np.zeros(100), 1.0, p, z0=0.5, v_noise=0, i_noise=0)
        np.testing.assert_allclose(m["v_true"], ocv(0.5))

    def test_instant_drop_is_R0(self):
        p = CellParams()
        I = np.r_[np.zeros(5), np.full(5, 4.0)]
        m = simulate_cell(I, 1.0, p, z0=0.5, v_noise=0, i_noise=0)
        self.assertAlmostEqual(m["v_true"][4] - m["v_true"][5], 4.0 * p.R0 + (ocv(0.5) - ocv(0.5)), places=3)

    def test_identification_noise_free(self):
        p = CellParams()
        I = hppc_profile()
        m = simulate_cell(I, 1.0, p, z0=0.5, v_noise=0, i_noise=0)
        f = fit_rc(m["i_meas"], m["v_meas"], 1.0, 0.5, p.Q)
        self.assertAlmostEqual(f["R0"], p.R0, places=5)
        self.assertAlmostEqual(f["R1"], p.R1, places=4)
        self.assertAlmostEqual(f["tau"], p.R1 * p.C1, delta=0.5)

    def test_ekf_recovers_from_wrong_start(self):
        p = CellParams()
        I = drive_cycle(3600, 1.0, seed=4)
        m = simulate_cell(I, 1.0, p, z0=0.9, seed=4)
        z, _ = ekf_soc(m["i_meas"], m["v_meas"], 1.0, p, z0=0.5)
        self.assertLess(np.max(np.abs(z[900:] - m["z"][900:])), 0.03)


if __name__ == "__main__":
    unittest.main()
