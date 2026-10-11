# Additions and concerns log

Updated during the task. Status describes actual scope, not promised successful findings.

| Item | Status / reason |
|---|---|
| Correct PSI normalization, tails, ties and missingness | Implemented; validation results recorded separately |
| Connect permutation tests to subgroup decisions | Implemented |
| Both-side sample gate; visible absent/new groups | Implemented |
| Fixed single attributes and one intersection pair | Implemented; no subgroup search |
| Fair statistical comparator | Aggregate and subgroup Holm comparisons implemented with distinct, explicit families |
| Realistic uncertainty | Run-level intervals and paired comparisons; no independent-window pseudo-replication |
| Public dataset licensing | UCI Adult, CC BY 4.0, exact citation and hashes recorded |
| Reproducible chart pack | Saved-run tables and manifests, PDF/SVG/300 dpi PNG |
| Input drift versus unfairness | Kept separate; S3 and S4 deliberately test the mismatch |
| Wider sample-size/share/magnitude grid | Still needed to generalize beyond the selected experimental settings |
| Less-exact cancellation | Still needed; present S2 is an intentionally strong constructed stress test |
| Numeric KS comparator | Still needed before attributing gains specifically to PSI rather than subgroup stratification |
| Independent empirical replication / realistic time dependence | Not evaluated |
| Public-data uncertainty | Conditional on the finite dataset/split; no present-day population generalization |
| Sensitive-group identity | Synthetic A/B are arbitrary; Adult uses recorded sex and age bands, with no identity inference |
| Outcome warning precision and localization | Store all alerts and subgroup errors; summary diagnostics generated from these; performance-change estimate is noisy |
| Outcome counts | TPR/FPR denominators saved; small labelled counts must be disclosed even when input n passes |
| General fairness guarantee | Not supported by input drift or a single TPR-gap metric |
| Adaptation/repair | Not evaluated; no result placeholders presented as evidence |
| Administrative approvals | No approvals were supplied or verified. User authorized computational work; dates/signatures remain for responsible people |
| Novelty claims | Full prior-work assessment still needed; no first-ever claim or commercial-tool aggregate-only claim |
| Paper/abstract/conclusions | Student-authored work retained as the student's responsibility; chart captions explain measurements only |

## Conditions that would undermine the idea

Report a problem if repeated no-change experiments show materially excessive error at the declared criterion; if subgroup monitoring offers no useful detection advantage in the tested settings after error correction; if coverage becomes too low for useful groups; if alerts fail to predict the declared outcome change; or if prior work leaves no defensible empirical contribution. A failure of outcome prediction restricts the bias-warning claim even if distribution-change detection works. Input-only monitoring inherently cannot detect every change in the outcome relationship.
