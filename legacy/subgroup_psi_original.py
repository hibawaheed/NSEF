"""
Subgroup-Decomposed PSI with Statistical Safeguards
-----------------------------------------------------
Core idea: standard PSI treats the whole population as one group,
which can hide bias concentrating in a specific demographic subgroup.
This module computes PSI both in aggregate AND decomposed by a
protected attribute, while guarding against two real failure modes:

1. Small-sample noise: smaller subgroups produce noisier PSI estimates
   purely from sampling variance, not real drift. We gate on minimum
   sample size and report bootstrapped confidence intervals so a
   jumpy small-sample PSI is visibly less trustworthy than a
   large-sample one.

2. Multiple comparisons: checking PSI across many subgroups/features
   at once means some will cross the alert threshold by chance alone,
   even with zero real drift. We apply a Benjamini-Hochberg correction
   to control the false-alarm rate.
"""

import numpy as np
import pandas as pd

MIN_SAMPLE_SIZE = 100   # don't trust PSI below this many rows
N_BOOTSTRAP = 500        # bootstrap resamples for confidence intervals
CI_LEVEL = 0.90


def calculate_psi(expected, actual, bins=10, epsilon=1e-4):
    """
    Core PSI calculation between a baseline ('expected') and
    live ('actual') distribution of a single feature.
    """
    expected = np.asarray(expected)
    actual = np.asarray(actual)

    # Bin edges are defined by the baseline distribution
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints[0] -= 1e-9
    breakpoints[-1] += 1e-9

    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    # epsilon guard: avoids log(0) / division by zero in empty bins
    expected_pct = np.clip(expected_pct, epsilon, None)
    actual_pct = np.clip(actual_pct, epsilon, None)

    psi_values = (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
    return float(np.sum(psi_values))


def bootstrap_psi_ci(expected, actual, bins=10, n_boot=N_BOOTSTRAP, ci=CI_LEVEL):
    """
    Bootstrap a confidence interval around a PSI estimate by
    resampling 'actual' with replacement n_boot times. A wide
    interval signals the point estimate is unreliable (likely a
    small-sample artifact); a tight interval signals a real signal.
    """
    boot_scores = []
    n = len(actual)
    for _ in range(n_boot):
        resample = np.random.choice(actual, size=n, replace=True)
        boot_scores.append(calculate_psi(expected, resample, bins=bins))

    lower = np.percentile(boot_scores, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_scores, (1 + ci) / 2 * 100)
    return lower, upper


def calculate_subgroup_psi(df_baseline, df_live, feature, group_col,
                            bins=10, min_n=MIN_SAMPLE_SIZE):
    """
    Compute PSI for a feature both in aggregate and decomposed by
    group_col (e.g. 'sex', 'age_band'). Subgroups below min_n are
    flagged as unreliable instead of silently reporting a noisy PSI.

    Returns a dict keyed by 'aggregate' and each group value, each
    containing the PSI estimate, confidence interval, sample size,
    and a reliability flag.
    """
    results = {}

    # Aggregate (the standard, single-population PSI)
    agg_psi = calculate_psi(df_baseline[feature], df_live[feature], bins=bins)
    agg_lo, agg_hi = bootstrap_psi_ci(df_baseline[feature], df_live[feature], bins=bins)
    results['aggregate'] = {
        'psi': agg_psi, 'ci_low': agg_lo, 'ci_high': agg_hi,
        'n': len(df_live), 'reliable': True
    }

    # Per-subgroup decomposition
    for group in df_live[group_col].unique():
        base_slice = df_baseline[df_baseline[group_col] == group][feature]
        live_slice = df_live[df_live[group_col] == group][feature]
        n = len(live_slice)

        if n < min_n:
            results[group] = {
                'psi': None, 'ci_low': None, 'ci_high': None,
                'n': n, 'reliable': False,
                'note': f'Sample size {n} < minimum {min_n}; PSI not reported'
            }
            continue

        psi = calculate_psi(base_slice, live_slice, bins=bins)
        lo, hi = bootstrap_psi_ci(base_slice, live_slice, bins=bins)
        results[group] = {
            'psi': psi, 'ci_low': lo, 'ci_high': hi,
            'n': n, 'reliable': True
        }

    return results


def psi_permutation_pvalue(expected, actual, observed_psi, bins=10, n_perm=500):
    """
    Approximate a p-value for an observed PSI via permutation testing:
    shuffle labels between expected/actual many times and measure how
    often a PSI this extreme occurs by chance alone. Use these
    p-values as input to apply_bh_correction() when testing many
    subgroups/features at once.
    """
    combined = np.concatenate([expected, actual])
    n_exp = len(expected)
    count = 0
    for _ in range(n_perm):
        np.random.shuffle(combined)
        perm_expected = combined[:n_exp]
        perm_actual = combined[n_exp:]
        perm_psi = calculate_psi(perm_expected, perm_actual, bins=bins)
        if perm_psi >= observed_psi:
            count += 1
    return count / n_perm


def apply_bh_correction(p_values, alpha=0.05):
    """
    Benjamini-Hochberg correction for multiple comparisons.
    Run this across the p-values from all your subgroup/feature PSI
    checks at once, so your false-alarm rate stays controlled instead
    of inflating with every extra slice you test.

    Returns a boolean array: True where the result remains
    significant after correction.
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = p_values[order]
    thresholds = (np.arange(1, n + 1) / n) * alpha

    below = ranked <= thresholds
    if not np.any(below):
        return np.zeros(n, dtype=bool)

    max_i = np.max(np.where(below))
    significant = np.zeros(n, dtype=bool)
    significant[order[:max_i + 1]] = True
    return significant


if __name__ == "__main__":
    # --- Example: drift injected ONLY into the female subgroup ---
    np.random.seed(42)

    n = 2000
    baseline = pd.DataFrame({
        'income': np.random.normal(50000, 10000, n),
        'sex': np.random.choice(['M', 'F'], n)
    })

    live = baseline.copy()
    female_mask = live['sex'] == 'F'
    live.loc[female_mask, 'income'] += np.random.normal(8000, 2000, female_mask.sum())

    results = calculate_subgroup_psi(baseline, live, feature='income', group_col='sex')

    print("Subgroup-decomposed PSI results:\n")
    for group, r in results.items():
        if r['reliable']:
            print(f"  {group}: PSI={r['psi']:.4f}  "
                  f"(90% CI: {r['ci_low']:.4f}-{r['ci_high']:.4f})  n={r['n']}")
        else:
            print(f"  {group}: {r['note']}")
