# Results

## Parameter identification (HPPC at 50% SOC, 2 mV / 5 mA noise, 20 repetitions)

| parameter | true | estimate (mean ± sd) | error |
|---|---|---|---|
| R0 | 0.015 | 0.01502 ± 0.00012 | +0.14% |
| R1 | 0.01 | 0.01 ± 0.00019 | +0.02% |
| C1 | 2500 | 2519 ± 1.1e+02 | +0.77% |
| tau | 25 | 25.19 ± 1.1 | +0.78% |

Mean fit RMSE: 2.00 mV

## SOC estimation (2-h drive cycle, 5 mV / 20 mA noise, mean of 10 cycles; errors in SOC percentage points)

| scenario | cc_rmse_% | cc_final_err_% | ekf_rmse_% | ekf_final_err_% | ekf_bias_rmse_% | ekf_bias_final_err_% | ekf_2sd_coverage | mean_final_true_soc_% |
|---|---|---|---|---|---|---|---|---|
| model-matched cell: z0 known, unbiased sensor | 0.01 | 0.02 | 0.02 | 0.01 | 0.03 | 0.01 | 1.0 | 15.0 |
| model-matched cell: initial SOC guess 0.60 (true 0.95) | 35.0 | 35.01 | 0.03 | 0.01 | 0.03 | 0.01 | 1.0 | 15.0 |
| model-matched cell: current-sensor bias +50 mA | 2.31 | 4.01 | 0.66 | 0.62 | 0.03 | 0.01 | 0.13 | 15.0 |
| model-matched cell: bias +50 mA and wrong initial SOC | 37.02 | 39.01 | 0.66 | 0.62 | 0.03 | 0.01 | 0.128 | 15.0 |
| model-matched cell: capacity overestimated by 10% | 4.23 | 7.27 | 1.44 | 1.34 | 0.29 | 0.18 | 0.077 | 15.0 |
| cell with unmodelled dynamics: z0 known, unbiased sensor | 0.01 | 0.02 | 0.6 | 0.25 | 1.06 | 0.23 | 0.149 | 15.0 |
| cell with unmodelled dynamics: initial SOC guess 0.60 (true 0.95) | 35.0 | 35.01 | 0.6 | 0.25 | 1.06 | 0.23 | 0.155 | 15.0 |
| cell with unmodelled dynamics: current-sensor bias +50 mA | 2.31 | 4.01 | 1.22 | 0.85 | 1.06 | 0.23 | 0.134 | 15.0 |
| cell with unmodelled dynamics: bias +50 mA and wrong initial SOC | 37.02 | 39.01 | 1.22 | 0.85 | 1.06 | 0.23 | 0.141 | 15.0 |
| cell with unmodelled dynamics: capacity overestimated by 10% | 4.23 | 7.27 | 0.99 | 1.07 | 0.93 | 0.1 | 0.021 | 15.0 |
