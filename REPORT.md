# Equivalent-Circuit Identification and Kalman-Filter SOC Estimation under Model Mismatch

**Gautam Jain** — IIT Bhubaneswar

## Abstract
We identify a first-order Thevenin battery model from simulated hybrid-pulse data and compare three SOC estimators —
coulomb counting, an EKF and a bias-augmented EKF — on a cell whose true dynamics include an unmodelled slow RC branch and
OCV-table error. The EKF reduces SOC RMSE from 35–37 percentage points (coulomb counting with a wrong initial SOC) to
0.6–1.2 points; adding a current-bias state keeps the error at 1.06 points even with a +50 mA sensor offset. Under model
mismatch the EKF covariance is strongly over-confident (2σ coverage 2–16%).

## 1. Cell model
`V = OCV(z) − R0·I − v1`, `v1[k+1] = a·v1[k] + R1(1 − a)·I[k]` with `a = exp(−Δt/R1C1)`, `z[k+1] = z[k] − I[k]Δt/(3600Q)`.
OCV uses the combined model `K0 − K1/z − K2 z + K3 ln z + K4 ln(1 − z)` (Plett 2004), giving 3.13 V at 10% and 4.17 V at
90% SOC. Parameters: Q = 2.5 Ah, R0 = 15 mΩ, R1 = 10 mΩ, C1 = 2,500 F. The "real" cell adds R2 = 8 mΩ, C2 = 50,000 F
(τ = 400 s) and an OCV error of 10 mV·sin(3πz).

## 2. Identification
An HPPC-style profile (10 s, 5 A discharge; 10 s, 3.75 A charge; rests) is simulated with noise and the voltage residual is
minimised over (R0, R1, τ) with bounded least squares. Over 20 noisy repetitions the estimates are unbiased within 1%,
with R0 the best-determined parameter (it sets the instantaneous voltage step).

## 3. Estimators
- **Coulomb counting**: integrate measured current from an assumed initial SOC.
- **EKF**: state [z, v1]; the measurement Jacobian is `[dOCV/dz, −1]`; process noise q_z = 1e−10, q_v = 1e−6; measurement
  noise (5 mV)².
- **EKF + bias**: state [z, v1, b] with a random-walk current bias, which enters the SOC update, the RC update and
  the R0 drop.

## 4. Results
On a model-matched cell the EKF is essentially exact (RMSE ≤ 0.03 points) except with sensor bias (0.66) or a 10% capacity error (1.44). On the real cell,
the unmodelled 400 s branch and the OCV error set an error floor of about 0.6 points for the EKF. The bias-augmented EKF
has a slightly higher floor (1.06) because the extra state partly absorbs model error as "bias", but it is robust to real
sensor offsets and to a 10% capacity error. Coverage of the ±2σ band drops from 100% (matched, no bias) to 2–16% (mismatched),
because the filter believes its model.

## 5. Limitations and next steps
Simulation only, one temperature, no hysteresis. Next: validate on measured cycling data (e.g., NASA PCoE or CALCE
datasets), use a 2-RC filter model, tune process noise for calibrated covariance, and compare with an unscented Kalman filter.

## References
1. G. Plett. Extended Kalman filtering for battery management systems of LiPB-based HEV battery packs, Parts 1–3. *Journal of Power Sources* 134, 252–292, 2004.
2. H. He, R. Xiong, J. Fan. Evaluation of lithium-ion battery equivalent circuit models for state of charge estimation by an experimental approach. *Energies* 4(4), 582–598, 2011.
3. *Battery Test Manual for Plug-In Hybrid Electric Vehicles* (HPPC test), Idaho National Laboratory, 2010.
