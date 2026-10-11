# Correction work log — AI-assisted

## 11 October 2026: scope and implementation

- User requested a documented OULAD bin correction, training-only prediction baseline, bounded matched accumulated-KS comparison on the original V2 synthetic benchmark, and a verified claim/evidence freeze. These are user requests, not inferred mentor approvals.
- Inspected current Git state, configurations, source, raw results, model parameters and existing findings. Started clean branch `codex/subpsi-r3-corrections` at `27288575028181baae90f68d30d4e3dc5e363a53`. Inventoried all 3,011 existing tracked files for preservation checks.
- Checked only historical design count frequencies to choose the correction: 314 zero, 45 one, 12 two, one three. Recorded the 0/1/2+ rule and missing bin before computing corrected scores. Historical training labels independently fix the constant prediction to Pass/Distinction (438/757).
- Added a feature-specific count encoder, frozen-model restoration, training-majority predictor, exact original V2 stream reconstruction, shared-scheduler execution and historical PSI parity guards. Existing V1/V2/V3 source files remain unchanged.
- Initial full unit suite: **87 passed in 1.87 seconds**. Regression tests cover the known quantile collapse, invalid counts, future tail counts, baseline selection isolation, frozen model restoration and matched whole-batch support/KS invariance. Further run/export verification is recorded separately.

AI performed the implementation, tests, analysis and documentation. The student supplied scope and requested corrections. No entry represents an independently performed student experiment or an invented research-log event. All new analyses are explicitly retrospective/post-result. No novelty or superiority is presumed.
