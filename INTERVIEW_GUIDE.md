# Interview guide — Battery SOC estimation with an EKF

## 30-second version
"State of charge can't be measured, so a battery management system estimates it. I modelled a cell as an equivalent
circuit — open-circuit voltage, a series resistor and an RC pair — identified the resistances and time constant from a pulse
test to within 1%, and compared coulomb counting with an extended Kalman filter. Coulomb counting drifts with any sensor
bias or wrong start; the EKF uses the voltage to correct itself and stays around 1% SOC error even when the real cell has
dynamics the model doesn't include. I also found the EKF's confidence band is badly over-confident under model mismatch."

## Explain these
- **OCV curve**: at rest, voltage depends only on SOC. Steeper OCV → voltage tells you more about SOC.
- **R0**: instant voltage drop when current starts. **RC pair**: the slower relaxation (here τ = 25 s) from diffusion /
  charge transfer.
- **Coulomb counting**: SOC = SOC₀ − ∫I dt/Q. Exact in theory, but errors in SOC₀, Q or a current offset never go away.
- **EKF**: predict with the model, correct with the voltage measurement weighted by the Kalman gain; "extended" because
  OCV(z) is nonlinear, so we linearise with dOCV/dz.
- **Bias state**: add the current-sensor offset as a state so the filter can learn it.
- **Coverage**: if the filter says ±2σ, the truth should be inside ~95% of the time. 2–16% means over-confident.

## Likely questions
1. *Why does the EKF struggle in the flat part of the OCV curve?* dOCV/dz is small there, so voltage carries little SOC
   information; the filter relies more on the coulomb-counting prediction.
2. *How would you fix the over-confidence?* Increase process noise to account for model error, use a 2-RC model, or adapt
   Q/R online.
3. *EKF vs UKF?* UKF avoids explicit Jacobians and handles nonlinearity better; for this smooth model they perform similarly.
4. *How is this used in an EV?* The BMS runs this every second to show range, limit power and balance cells.
