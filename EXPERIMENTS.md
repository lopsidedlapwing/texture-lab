# Experiment ledger

1. Eight-colour baseline, seed 42. Hypothesis: palette selection controls whether sparse rust flecks survive reduction. Held source, box filter and 64×64 resolution fixed. Crossed four palette methods with three mappings. Median cut with nearest mapping produced zero warm pixels by the a* threshold. Unweighted Lab k-means produced 7.0% and the lowest mean CIE76 error (2.00). Retain Lab k-means and libimagequant for the next comparison.
2. Warm-pixel weighting. Hypothesis: weighting warm observations during palette fitting preserves more mineral flecks. Holding nearest mapping fixed, fourfold weight raised warm coverage to 9.3% but reduced the L* span from 27.0 to 22.1. Keep weighting adjustable. Compare masks against source features before selecting an operating point.

Full settings, software versions, palette entries, frequencies and diagnostics are in [results.json](outputs/concrete/results.json).
