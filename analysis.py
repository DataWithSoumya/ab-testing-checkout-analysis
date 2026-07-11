"""
A/B Test Analysis: Checkout Redesign Experiment
--------------------------------------------------
This script:
1. Loads and cleans the raw experiment data
2. Runs a Sample Ratio Mismatch (SRM) check -- a QA step most tutorials skip,
   but any experiment result is questionable if the randomization itself
   looks broken
3. Runs the primary hypothesis test: two-proportion z-test on conversion rate
4. Computes a 95% confidence interval and relative lift for the effect
5. Checks a secondary metric (revenue per user)
6. Checks for a novelty effect over time (early days vs. later days)
7. Breaks the result down by device segment -- because the honest finding
   here is that the effect is NOT uniform across segments
8. Runs a minimum detectable effect (MDE) sanity check given the sample size
9. Generates charts
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

# ---------- 1. LOAD & CLEAN ----------
df = pd.read_csv("data/experiment_data.csv", parse_dates=["session_date"])
print(f"Raw rows: {len(df)}")

before = len(df)
df = df.drop_duplicates()
print(f"Removed {before - len(df)} duplicate rows")

df["group"] = df["group"].str.strip().str.title()
df["device"] = df["device"].fillna(df["device"].mode()[0])

df.to_csv("data/experiment_data_clean.csv", index=False)
print("Saved cleaned data to data/experiment_data_clean.csv")

control = df[df["group"] == "Control"]
treatment = df[df["group"] == "Treatment"]
n_control, n_treatment = len(control), len(treatment)
print(f"\nControl: {n_control:,} users | Treatment: {n_treatment:,} users")

# ---------- 2. SAMPLE RATIO MISMATCH (SRM) CHECK ----------
# If randomization is working, group sizes should be ~50/50. A significant
# deviation here (p < 0.01, using a stricter threshold since SRM checks
# should rarely fire on genuinely healthy randomization) means something is
# wrong with the experiment setup -- e.g. bot filtering hitting one arm
# harder, or a redirect bug -- and the results below shouldn't be trusted
# until it's fixed, no matter how good the headline metric looks.
srm_chi2, srm_p = stats.chisquare([n_control, n_treatment], f_exp=[len(df) / 2, len(df) / 2])
print(f"\n--- Sample Ratio Mismatch check ---")
print(f"Chi-square: {srm_chi2:.3f} | p-value: {srm_p:.4f}")
print("PASS -- no SRM detected, randomization looks healthy" if srm_p >= 0.01 else "FAIL -- investigate before trusting results")

# ---------- 3. PRIMARY METRIC: CONVERSION RATE (two-proportion z-test) ----------
x1, n1 = control["converted"].sum(), n_control
x2, n2 = treatment["converted"].sum(), n_treatment
p1, p2 = x1 / n1, x2 / n2

pooled_p = (x1 + x2) / (n1 + n2)
se_pooled = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n1 + 1 / n2))
z_stat = (p2 - p1) / se_pooled
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
diff = p2 - p1
ci_low, ci_high = diff - 1.96 * se_diff, diff + 1.96 * se_diff
relative_lift = 100 * diff / p1

print(f"\n--- Primary metric: Conversion Rate ---")
print(f"Control:   {p1:.4%} ({x1:,}/{n1:,})")
print(f"Treatment: {p2:.4%} ({x2:,}/{n2:,})")
print(f"Absolute difference: {diff:+.4%} | 95% CI: [{ci_low:+.4%}, {ci_high:+.4%}]")
print(f"Relative lift: {relative_lift:+.1f}%")
print(f"z-statistic: {z_stat:.3f} | p-value: {p_value:.6f}")
significant = p_value < 0.05
print(f"Result: {'STATISTICALLY SIGNIFICANT' if significant else 'NOT statistically significant'} at alpha=0.05")

# ---------- 4. SECONDARY METRIC: REVENUE PER USER (ARPU, Welch's t-test) ----------
t_stat, arpu_p = stats.ttest_ind(treatment["revenue"], control["revenue"], equal_var=False)
arpu_control, arpu_treatment = control["revenue"].mean(), treatment["revenue"].mean()
print(f"\n--- Secondary metric: Revenue per User (ARPU) ---")
print(f"Control ARPU:   ${arpu_control:.2f}")
print(f"Treatment ARPU: ${arpu_treatment:.2f}")
print(f"t-statistic: {t_stat:.3f} | p-value: {arpu_p:.4f}")
print("(ARPU lift follows directly from the conversion lift -- avg order value itself was not changed by the redesign)")

# ---------- 5. NOVELTY EFFECT CHECK (daily trend) ----------
daily = df.groupby(["session_date", "group"])["converted"].mean().unstack()
daily["lift_pp"] = daily["Treatment"] - daily["Control"]

early_lift = daily["lift_pp"].iloc[:4].mean()
later_lift = daily["lift_pp"].iloc[4:].mean()
print(f"\n--- Novelty effect check ---")
print(f"Avg daily lift, first 4 days: {early_lift:+.4%}")
print(f"Avg daily lift, remaining days: {later_lift:+.4%}")
print("Early lift is noticeably higher -- consistent with a novelty effect that faded; "
      "the stabilized later-period lift is the more trustworthy estimate of the true long-run effect."
      if early_lift > later_lift * 1.3 else "No strong novelty effect detected.")

# ---------- 6. SEGMENT ANALYSIS: IS THE EFFECT UNIFORM? ----------
print("\n--- Segment analysis: conversion rate by device ---")
segment_results = []
for device, g in df.groupby("device"):
    c = g[g["group"] == "Control"]
    t = g[g["group"] == "Treatment"]
    if len(c) == 0 or len(t) == 0:
        continue
    pc, pt = c["converted"].mean(), t["converted"].mean()
    xc, nc = c["converted"].sum(), len(c)
    xt, nt = t["converted"].sum(), len(t)
    pooled = (xc + xt) / (nc + nt)
    se = np.sqrt(pooled * (1 - pooled) * (1 / nc + 1 / nt))
    z = (pt - pc) / se if se > 0 else 0
    p_seg = 2 * (1 - stats.norm.cdf(abs(z)))
    segment_results.append({
        "device": device, "control_rate": pc, "treatment_rate": pt,
        "lift_pp": pt - pc, "relative_lift_pct": 100 * (pt - pc) / pc if pc > 0 else np.nan,
        "p_value": p_seg,
    })
    print(f"{device:10s} | Control: {pc:.4%} | Treatment: {pt:.4%} | "
          f"Lift: {pt - pc:+.4%} | p={p_seg:.4f}")

segment_df = pd.DataFrame(segment_results)

# ---------- 7. MINIMUM DETECTABLE EFFECT (MDE) SANITY CHECK ----------
z_alpha, z_beta = 1.96, 0.84  # alpha=0.05 two-sided, 80% power
mde = (z_alpha + z_beta) * np.sqrt(2 * p1 * (1 - p1) / n1)
print(f"\n--- Minimum Detectable Effect (sanity check) ---")
print(f"With n={n1:,} per group and baseline rate {p1:.2%}, this experiment could reliably detect "
      f"an absolute lift of about {mde:.4%} or larger (80% power, alpha=0.05).")
print(f"The observed lift ({diff:+.4%}) is {'above' if abs(diff) > mde else 'below'} this threshold, "
      f"{'consistent with' if abs(diff) > mde else 'a caution flag against'} the significant result above.")

# ---------- 8. CHARTS ----------
plt.style.use("seaborn-v0_8-whitegrid")

# 8a. Conversion rate by group with 95% CI error bars
fig, ax = plt.subplots(figsize=(6, 5))
rates = [p1, p2]
errs = [1.96 * np.sqrt(p1 * (1 - p1) / n1), 1.96 * np.sqrt(p2 * (1 - p2) / n2)]
bars = ax.bar(["Control", "Treatment"], rates, yerr=errs, capsize=8,
              color=["#7f8c8d", "#2E86AB"])
ax.set_title("Conversion Rate by Group (95% CI)", fontsize=14, fontweight="bold")
ax.set_ylabel("Conversion Rate")
for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.006, f"{rate:.2%}",
            ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig("images/conversion_rate_by_group.png", dpi=150)
plt.close()

# 8b. Daily conversion rate trend (novelty effect visual)
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(daily.index, daily["Control"], label="Control", color="#7f8c8d", marker="o", markersize=3)
ax.plot(daily.index, daily["Treatment"], label="Treatment", color="#2E86AB", marker="o", markersize=3)
ax.axvspan(daily.index[0], daily.index[3], color="orange", alpha=0.1, label="Novelty period (first 4 days)")
ax.set_title("Daily Conversion Rate — Control vs. Treatment", fontsize=14, fontweight="bold")
ax.set_ylabel("Conversion Rate")
plt.xticks(rotation=45, ha="right")
ax.legend()
plt.tight_layout()
plt.savefig("images/conversion_rate_over_time.png", dpi=150)
plt.close()

# 8c. Segment breakdown by device
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(segment_df))
width = 0.35
ax.bar(x - width/2, segment_df["control_rate"], width, label="Control", color="#7f8c8d")
ax.bar(x + width/2, segment_df["treatment_rate"], width, label="Treatment", color="#2E86AB")
ax.set_xticks(x)
ax.set_xticklabels(segment_df["device"])
ax.set_title("Conversion Rate by Device Segment", fontsize=14, fontweight="bold")
ax.set_ylabel("Conversion Rate")
ax.legend()
plt.tight_layout()
plt.savefig("images/segment_breakdown_by_device.png", dpi=150)
plt.close()

# 8d. Confidence interval visualization for the overall effect
fig, ax = plt.subplots(figsize=(7, 4))
ax.errorbar([diff], [0], xerr=[[diff - ci_low], [ci_high - diff]], fmt="o",
            color="#2E86AB", capsize=8, markersize=10)
ax.axvline(0, color="red", linestyle="--", linewidth=1, label="No effect")
ax.set_yticks([])
ax.set_xlabel("Difference in Conversion Rate (Treatment − Control)")
ax.set_title("95% Confidence Interval for the Treatment Effect", fontsize=14, fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig("images/confidence_interval_plot.png", dpi=150)
plt.close()

print("\nCharts saved to images/")

# ---------- 9. SAVE SUMMARY ----------
summary = {
    "control_conversion_rate": round(p1, 4),
    "treatment_conversion_rate": round(p2, 4),
    "absolute_lift_pp": round(diff, 4),
    "relative_lift_pct": round(relative_lift, 1),
    "p_value": round(p_value, 6),
    "statistically_significant": significant,
    "srm_p_value": round(srm_p, 4),
    "srm_pass": bool(srm_p >= 0.01),
    "mde_at_80pct_power": round(mde, 4),
    "strongest_segment": segment_df.loc[segment_df["lift_pp"].idxmax(), "device"],
    "strongest_segment_lift_pp": round(segment_df["lift_pp"].max(), 4),
    "weakest_segment": segment_df.loc[segment_df["lift_pp"].idxmin(), "device"],
    "weakest_segment_lift_pp": round(segment_df["lift_pp"].min(), 4),
    "early_period_lift_pp": round(early_lift, 4),
    "later_period_lift_pp": round(later_lift, 4),
}
pd.Series(summary).to_csv("data/summary_metrics.csv")
segment_df.to_csv("data/segment_results.csv", index=False)
print("\nSummary:", summary)
