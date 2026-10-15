"""SOC estimators: coulomb counting and an extended Kalman filter on the state x = [z, v1] (optionally + current bias b)."""
import numpy as np
from .model import ocv, docv


def coulomb_count(i_meas, dt, Q, z0):
    return z0 - np.concatenate([[0.0], np.cumsum(i_meas[:-1])]) * dt / (3600 * Q)


def ekf_soc(i_meas, v_meas, dt, p, z0, P0=None, q_z=1e-10, q_v=1e-6, r_v=0.005 ** 2, estimate_bias=False, q_b=1e-10):
    """Discrete EKF.  State: [z, v1] or [z, v1, b] where b is a slowly varying current-sensor bias.
    Process:   z+ = z - (I - b) dt / 3600Q,   v1+ = a v1 + R1 (1 - a)(I - b),   b+ = b
    Measure:   V = OCV(z) - R0 (I - b) - v1
    """
    a = np.exp(-dt / (p.R1 * p.C1))
    nx = 3 if estimate_bias else 2
    x = np.zeros(nx); x[0] = z0
    P = np.diag([0.1 ** 2, 1e-4] + ([0.1 ** 2] if estimate_bias else [])) if P0 is None else P0.copy()
    Qn = np.diag([q_z, q_v] + ([q_b] if estimate_bias else []))
    out_z, out_sd = np.empty(len(i_meas)), np.empty(len(i_meas))
    for k, (i, v) in enumerate(zip(i_meas, v_meas)):
        b = x[2] if estimate_bias else 0.0
        ie = i - b
        # measurement update with the current sample
        H = np.zeros(nx); H[0] = docv(x[0]); H[1] = -1.0
        if estimate_bias:
            H[2] = p.R0
        yhat = ocv(x[0]) - p.R0 * ie - x[1]
        S = H @ P @ H + r_v
        Kg = P @ H / S
        x = x + Kg * (v - yhat)
        P = (np.eye(nx) - np.outer(Kg, H)) @ P
        out_z[k], out_sd[k] = x[0], np.sqrt(P[0, 0])
        # time update to k+1
        b = x[2] if estimate_bias else 0.0
        ie = i - b
        F = np.eye(nx); F[1, 1] = a
        if estimate_bias:
            F[0, 2] = dt / (3600 * p.Q); F[1, 2] = -p.R1 * (1 - a)
        x = x.copy()
        x[0] = x[0] - ie * dt / (3600 * p.Q)
        x[1] = a * x[1] + p.R1 * (1 - a) * ie
        P = F @ P @ F.T + Qn
    return out_z, out_sd
