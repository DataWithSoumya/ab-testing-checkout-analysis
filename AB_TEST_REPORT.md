# A/B Test Report: Checkout Redesign

## Experiment Summary

| | |
|---|---|
| **Hypothesis** | The redesigned checkout flow will increase conversion rate vs. the existing checkout |
| **Metric** | Conversion rate (primary), Revenue per user / ARPU (secondary) |
| **Duration** | 30 days |
| **Sample size** | 12,831 Control / 12,728 Treatment (25,559 total) |
| **Randomization QA** | Passed — no Sample Ratio Mismatch detected (p = 0.52) |

## Result

**Ship it.** The treatment (new checkout) produced a statistically significant
lift in conversion rate.

| Metric | Control | Treatment | Absolute Diff | Relative Lift | p-value |
|---|---|---|---|---|---|
| Conversion Rate | 7.61% | 9.08% | +1.48pp | **+19.4%** | 0.00002 |
| ARPU | $5.45 | $6.68 | +$1.23 | +22.6% | <0.0001 |

95% confidence interval for the conversion rate lift: **[+0.80pp, +2.15pp]** —
entirely above zero, so we can be confident this is a real effect, not noise.

## Before Trusting This Result: The QA Checks That Matter

A lot of A/B test writeups skip straight to "p < 0.05, ship it." Two checks
that should always happen first:

1. **Sample Ratio Mismatch (SRM):** if the randomization itself is broken
   (e.g., a redirect bug excludes more bot traffic from one arm), the
   headline result is meaningless no matter how significant it looks. Group
   sizes here were 12,831 vs. 12,728 — a chi-square test confirms this is
   consistent with true 50/50 randomization (p = 0.52).

2. **Minimum Detectable Effect (MDE):** with ~12,800 users per group and a
   7.6% baseline rate, this experiment had enough power to reliably detect
   an absolute lift of ~0.93pp or larger. The observed lift (1.48pp) clears
   that bar, so the significant result isn't just a lucky small-sample fluke.

## The Result Is Not Uniform — And That's the Real Finding

Breaking the effect down by device tells a more useful story than the
headline number alone:

| Device | Control | Treatment | Lift | p-value | Significant? |
|---|---|---|---|---|---|
| Mobile | 6.99% | 9.06% | +2.07pp | <0.0001 | **Yes** |
| Tablet | 6.09% | 7.53% | +1.44pp | 0.149 | No |
| Desktop | 9.06% | 9.56% | +0.51pp | 0.415 | No |

**The entire effect is coming from mobile users.** Desktop and Tablet show
small, statistically insignificant differences — consistent with noise, not
a real effect. This makes sense in hindsight (checkout friction is usually
worse on mobile, so a redesign targeting that has more room to help) but it
matters for the rollout decision: shipping this to 100% of traffic captures
the win, but a team that only reads the aggregate number would miss that
**where** the win is concentrated — useful for prioritizing what to test
next.

## Novelty Effect: Checked, Not Found

It's good practice to check whether an early spike fades over time (users
excited by something new, not because it's actually better long-term). The
daily trend was checked here, and there's no clear novelty pattern in this
data — the lift held up through the full 30-day window rather than shrinking.
Worth re-checking on a longer run if this ships, since 30 days is a
reasonable but not huge window.

## Recommendation

1. **Ship the new checkout flow to 100% of traffic** — the overall effect is
   real, significant, and large enough to matter economically (+19.4%
   relative lift in conversion, +22.6% in revenue per user)
2. **Investigate why Desktop/Tablet didn't benefit** — before assuming mobile
   is "done," look at qualitative feedback or session recordings from
   desktop users to see if there's a desktop-specific friction point the
   redesign didn't address
3. **Consider a follow-up test targeted at Desktop/Tablet checkout** — since
   the current redesign didn't move the needle there, a separate,
   device-specific experiment may be a better next step than assuming one
   design fits all devices

## Caveats

- This is a single 30-day experiment; seasonal effects (e.g. holiday
  shopping behavior) aren't captured and could change results if re-run at
  a different time of year
- Revenue lift here is driven entirely by the conversion lift — average
  order value among converters was not meaningfully different between
  groups, so this redesign should be understood as a "more people complete
  checkout" win, not a "people spend more per order" win

---
*Note: Dataset is synthetically generated for portfolio/demonstration purposes and does not represent a real business or product.*
