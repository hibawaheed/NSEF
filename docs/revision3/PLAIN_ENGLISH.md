# What changed, in basic English

AI-assisted learning notes,11 October 2026. This is an explanation for the student, not a final submission written in the student's voice.

**Subgrouping remains the project.** We compare old and later data for everyone, then for each recorded demographic category and each pair of categories. The groups are fixed beforehand; we do not hunt for whichever group gives the most dramatic graph.

**PSI** puts values into bins fixed using old design data and compares the proportions. **KS** compares the cumulative distributions of numeric or meaningfully ordered values. A larger score means the two samples look more different under that score. Their raw score scales are different, so PSI0.2 is not directly “twice as much drift” as KS0.1. Missingness is kept visible.

**Why a shared collection rule matters:** suppose a group has200 reference records, and three incoming batches contain 30, 40 and 35 group records. With a100 record accumulation minimum, neither statistic tests after 30 or 70. Both test the same 105 records after the third batch, then start a new collection. Neither is allowed to choose only favorable records. The waiting time is two delivery intervals from the first batch. This arithmetic is a teaching example, not observed human data.

Now suppose the historical reference has only 20 group records. Even after collecting 105 new records, both methods remain unassessable. The rule needs enough on **both** sides. Waiting longer cannot create missing historical evidence. “Not assessable” does not mean “unchanged.”

**What the new chart shows:** the left grid lists every ACS sex×race intersection. Columns are the proposed 2016 reference and three later survey years. The right grid lists every OULAD gender×disability intersection in the two October cohorts. Numbers are actual records after the proposed role split, not national population sizes. Grey is zero, orange 1–49, yellow 50–99, teal 100 or more. Read the reference cell as well as the later cell. All aggregate and single-attribute counts are also saved in source tables.

**What it proves:** some planned comparisons have enough records under the declared count rule, while others do not. **What it does not prove:** actual drift, prediction failure, unfairness, a better algorithm, or suitability for every population. No main new drift/accuracy study has run yet.

The three simulation replays check that the revised code still gives the same accumulated-PSI answers as v2 and that KS sees exactly the same records. They do not establish a detection rate from three runs. Synthetic people remain mathematical simulations. The ACS and OULAD source records were collected by their original organizations, not by the student or this assistant.

For later natural-data charts, we can say “these recorded distributions differ by this amount.” We cannot say “the detector correctly found 80% of real changes” when nobody knows the true changes or when they began. Separate constructed controls can have a known intervention because the sampling rule is deliberately changed; their x-axis must say “constructed delivery block.”

Prediction audit: **TPR** is the fraction of actual positive cases predicted positive; **FPR** is the fraction of actual negative cases predicted positive; **accuracy** is the fraction of all cases predicted correctly. Each has a different denominator. A group gap already present in the reference is different from a gap that changes later. None of these alone proves causation or discrimination.

Questions to practice before presenting: Why can everyone look stable while groups change? Why might KS beat PSI? Why does collecting more current records fail when the reference is tiny? Why are survey weights and household dependence relevant? What does a negative or tied result teach? Which parts were written/tested by AI, and which choices and explanations has the student actually checked?
