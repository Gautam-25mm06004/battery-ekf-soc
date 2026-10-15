"""Identify R0, R1, C1 from a pulse test by nonlinear least squares on the measured terminal voltage."""
import numpy as np
from scipy.optimize import least_squares
from .model import ocv


def predict_voltage(theta, current, dt, z0, Q):
    R0, R1, tau = theta
    a = np.exp(-dt / tau)
    z = z0 - np.concatenate([[0.0], np.cumsum(current[:-1])]) * dt / (3600 * Q)
    v1 = np.empty(len(current))
    vk = 0.0
    for k, i in enumerate(current):
        v1[k] = vk
        vk = a * vk + R1 * (1 - a) * i
    return ocv(z) - R0 * current - v1


def fit_rc(current, v_meas, dt, z0, Q, theta0=(0.01, 0.01, 10.0)):
    res = least_squares(lambda th: predict_voltage(th, current, dt, z0, Q) - v_meas, theta0,
                        bounds=([1e-4, 1e-4, 1.0], [0.2, 0.2, 500.0]))
    R0, R1, tau = res.x
    J = res.jac
    cov = np.linalg.inv(J.T @ J) * np.mean(res.fun ** 2)
    return {"R0": R0, "R1": R1, "C1": tau / R1, "tau": tau, "rmse_V": float(np.sqrt(np.mean(res.fun ** 2))),
            "se": np.sqrt(np.diag(cov)).tolist()}
