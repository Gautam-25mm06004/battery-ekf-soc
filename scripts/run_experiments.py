"""(1) Identify RC parameters from a noisy pulse test; (2) compare SOC estimators on a 2-hour drive cycle under
sensor bias, wrong initial SOC and capacity error. Writes results/results.json, results/summary.md, figures."""
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from batt import CellParams, ocv, simulate_cell, drive_cycle, hppc_profile, fit_rc, coulomb_count, ekf_soc  # noqa

OUT, FIG = ROOT / "results", ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
R = {}
true = CellParams()                                   # ideal cell: exactly the filter's model structure
real = CellParams(R2=0.008, C2=50000.0, ocv_err_mV=10.0)  # 'real' cell: extra 400 s RC branch + 10 mV OCV-table error
dt = 1.0

# 1) Parameter identification from HPPC pulses at 50% SOC, 20 noisy repetitions
ids = []
I_p = hppc_profile(dt)
for s in range(20):
    m = simulate_cell(I_p, dt, true, z0=0.5, v_noise=0.002, i_noise=0.005, seed=100 + s)
    ids.append(fit_rc(m["i_meas"], m["v_meas"], dt, 0.5, true.Q))
est = {k: (float(np.mean([d[k] for d in ids])), float(np.std([d[k] for d in ids], ddof=1))) for k in ("R0", "R1", "C1", "tau")}
R["identification"] = {k: {"true": getattr(true, k) if k != "tau" else true.R1 * true.C1, "mean": v[0], "sd": v[1],
                           "error_pct": 100 * (v[0] / (getattr(true, k) if k != "tau" else true.R1 * true.C1) - 1)} for k, v in est.items()}
R["identification"]["fit_rmse_mV"] = 1000 * float(np.mean([d["rmse_V"] for d in ids]))
ident = replace(true, R0=est["R0"][0], R1=est["R1"][0], C1=est["C1"][0])

# 2) SOC estimation scenarios, 10 drive-cycle seeds each (2 hours, 1 s samples, ~1.2 A mean -> ~95% -> ~0% SOC... capped)
def scenario(name, z0_guess, i_bias, q_model, cell, seeds=range(10)):
    rows = []
    for s in seeds:
        I = drive_cycle(7200, dt, seed=s, mean_a=1.0)
        m = simulate_cell(I, dt, cell, z0=0.95, v_noise=0.005, i_noise=0.02, i_bias=i_bias, seed=s)
        pm = replace(ident, Q=q_model)
        cc = coulomb_count(m["i_meas"], dt, q_model, z0_guess)
        ek, sd = ekf_soc(m["i_meas"], m["v_meas"], dt, pm, z0_guess)
        eb, _ = ekf_soc(m["i_meas"], m["v_meas"], dt, pm, z0_guess, estimate_bias=True)
        err = lambda e: (100 * float(np.sqrt(np.mean((e - m["z"]) ** 2))), 100 * float(np.max(np.abs(e[600:] - m["z"][600:]))), 100 * float(abs(e[-1] - m["z"][-1])))
        within = np.mean(np.abs(ek - m["z"]) <= 2 * sd)
        rows.append({"cc": err(cc), "ekf": err(ek), "ekf_bias": err(eb), "ekf_2sd_coverage": float(within), "z_end": float(m["z"][-1])})
    agg = {"scenario": name}
    for k in ("cc", "ekf", "ekf_bias"):
        agg[f"{k}_rmse_%"] = round(np.mean([r[k][0] for r in rows]), 2)
        agg[f"{k}_final_err_%"] = round(np.mean([r[k][2] for r in rows]), 2)
    agg["ekf_2sd_coverage"] = round(float(np.mean([r["ekf_2sd_coverage"] for r in rows])), 3)
    agg["mean_final_true_soc_%"] = round(100 * float(np.mean([r["z_end"] for r in rows])), 1)
    return agg

R["soc"] = []
for cell_name, cell in (("model-matched cell", true), ("cell with unmodelled dynamics", real)):
    R["soc"] += [
        scenario(f"{cell_name}: z0 known, unbiased sensor", 0.95, 0.0, true.Q, cell),
        scenario(f"{cell_name}: initial SOC guess 0.60 (true 0.95)", 0.60, 0.0, true.Q, cell),
        scenario(f"{cell_name}: current-sensor bias +50 mA", 0.95, 0.05, true.Q, cell),
        scenario(f"{cell_name}: bias +50 mA and wrong initial SOC", 0.60, 0.05, true.Q, cell),
        scenario(f"{cell_name}: capacity overestimated by 10%", 0.95, 0.0, 1.1 * true.Q, cell),
    ]

# Figure: one run of the hardest scenario
I = drive_cycle(7200, dt, seed=3, mean_a=1.0)
m = simulate_cell(I, dt, real, z0=0.95, v_noise=0.005, i_noise=0.02, i_bias=0.05, seed=3)
cc = coulomb_count(m["i_meas"], dt, true.Q, 0.6)
ek, sd = ekf_soc(m["i_meas"], m["v_meas"], dt, ident, 0.6)
eb, _ = ekf_soc(m["i_meas"], m["v_meas"], dt, ident, 0.6, estimate_bias=True)
t = np.arange(len(I)) / 60
fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
ax[0].plot(t, I, lw=0.4); ax[0].set_ylabel("current (A)")
ax[1].plot(t, m["v_meas"], lw=0.4); ax[1].set_ylabel("voltage (V)")
ax[2].plot(t, 100 * m["z"], "k", label="true"); ax[2].plot(t, 100 * cc, label="coulomb counting")
ax[2].plot(t, 100 * ek, label="EKF"); ax[2].plot(t, 100 * eb, label="EKF + bias state")
ax[2].fill_between(t, 100 * (ek - 2 * sd), 100 * (ek + 2 * sd), alpha=0.2, color="C1")
ax[2].set_ylabel("SOC (%)"); ax[2].set_xlabel("minutes"); ax[2].legend(fontsize=8)
ax[0].set_title("Cell with unmodelled dynamics, wrong initial SOC (60% vs 95%), +50 mA sensor bias")
fig.tight_layout(); fig.savefig(FIG / "soc_tracking.png", dpi=130); plt.close(fig)
zz = np.linspace(0.02, 0.98, 200)
fig, ax = plt.subplots(figsize=(5, 3.5)); ax.plot(100 * zz, ocv(zz)); ax.set_xlabel("SOC (%)"); ax.set_ylabel("OCV (V)")
fig.tight_layout(); fig.savefig(FIG / "ocv.png", dpi=130); plt.close(fig)

(OUT / "results.json").write_text(json.dumps(R, indent=2))
idr = R["identification"]
md = "# Results\n\n## Parameter identification (HPPC at 50% SOC, 2 mV / 5 mA noise, 20 repetitions)\n\n| parameter | true | estimate (mean ± sd) | error |\n|---|---|---|---|\n"
for k in ("R0", "R1", "C1", "tau"):
    md += f"| {k} | {idr[k]['true']:.4g} | {idr[k]['mean']:.4g} ± {idr[k]['sd']:.2g} | {idr[k]['error_pct']:+.2f}% |\n"
md += f"\nMean fit RMSE: {idr['fit_rmse_mV']:.2f} mV\n\n## SOC estimation (2-h drive cycle, 5 mV / 20 mA noise, mean of 10 cycles; errors in SOC percentage points)\n\n"
cols = list(R["soc"][0])
md += "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n" + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for r in R["soc"])
(OUT / "summary.md").write_text(md)
print(md)
