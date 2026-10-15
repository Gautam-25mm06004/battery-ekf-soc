"""First-order Thevenin equivalent circuit:  V = OCV(z) - R0 I - v1,   dv1/dt = -v1/(R1 C1) + I/C1,
dz/dt = -I / (3600 Q).  I > 0 is discharge. z = state of charge in [0, 1].

The OCV curve uses the 'combined model' form popular in battery state estimation (Plett 2004):
OCV(z) = K0 - K1/z - K2 z + K3 ln z + K4 ln(1 - z), with coefficients giving a typical NMC-like 3.0-4.2 V shape.
"""
from dataclasses import dataclass, replace
import numpy as np

K = (3.65, 0.012, -0.55, 0.20, -0.025)   # gives 3.13 V at 10% SOC, 3.78 V at 50%, 4.17 V at 90%; monotone


def ocv(z):
    z = np.clip(z, 0.01, 0.99)
    return K[0] - K[1] / z - K[2] * z + K[3] * np.log(z) + K[4] * np.log(1 - z)


def docv(z):
    z = np.clip(z, 0.01, 0.99)
    return K[1] / z ** 2 - K[2] + K[3] / z - K[4] / (1 - z)


@dataclass(frozen=True)
class CellParams:
    Q: float = 2.5        # Ah
    R0: float = 0.015     # ohm
    R1: float = 0.010     # ohm
    C1: float = 2500.0    # F  (time constant 25 s)
    # Extra physics present in the "real" cell but not in the filter's 1-RC model:
    R2: float = 0.0       # ohm, slow diffusion branch
    C2: float = 50000.0   # F
    ocv_err_mV: float = 0.0   # amplitude of the difference between the cell's true OCV and the OCV table


def simulate_cell(current, dt, p: CellParams, z0=0.9, v_noise=0.005, i_noise=0.01, i_bias=0.0, seed=0):
    """Exact discretisation of the RC branch(es). Returns true SOC, true terminal voltage and *measured* V, I."""
    rng = np.random.default_rng(seed)
    a = np.exp(-dt / (p.R1 * p.C1))
    a2 = np.exp(-dt / (p.R2 * p.C2)) if p.R2 > 0 else 0.0
    n = len(current)
    z, v1, v2 = np.empty(n), np.empty(n), np.empty(n)
    zk, vk, wk = z0, 0.0, 0.0
    for k in range(n):
        z[k], v1[k], v2[k] = zk, vk, wk
        zk = zk - current[k] * dt / (3600 * p.Q)
        vk = a * vk + p.R1 * (1 - a) * current[k]
        wk = a2 * wk + p.R2 * (1 - a2) * current[k]
    ocv_true = ocv(z) + 1e-3 * p.ocv_err_mV * np.sin(3 * np.pi * z)
    v = ocv_true - p.R0 * current - v1 - v2
    return {"z": z, "v_true": v,
            "v_meas": v + v_noise * rng.standard_normal(n),
            "i_meas": current + i_bias + i_noise * rng.standard_normal(n)}


def drive_cycle(duration_s, dt, seed=0, mean_a=1.2):
    """Random urban-style load: segments of 5-60 s with currents between -2.5 A (regeneration) and 7 A."""
    rng = np.random.default_rng(seed)
    n = int(duration_s / dt)
    i = np.empty(n)
    k = 0
    while k < n:
        seg = int(rng.uniform(5, 60) / dt)
        lvl = rng.choice([0.0, rng.uniform(0.5, 3), rng.uniform(3, 7), -rng.uniform(0.5, 2.5)], p=[0.2, 0.45, 0.2, 0.15])
        i[k:k + seg] = lvl
        k += seg
    return i * mean_a / max(i.mean(), 1e-6)


def hppc_profile(dt=1.0):
    """Hybrid-pulse test: 60 s rest, 10 s 5 A discharge, 120 s rest, 10 s 3.75 A charge, 120 s rest."""
    blocks = [(60, 0.0), (10, 5.0), (120, 0.0), (10, -3.75), (120, 0.0)]
    return np.concatenate([np.full(int(d / dt), a) for d, a in blocks])
