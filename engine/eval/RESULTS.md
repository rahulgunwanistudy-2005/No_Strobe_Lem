# Evaluation results

The full S4 detection/mitigation evaluation has not run. No full-S4 verifier
pass rate, viewing-cost result, PEAT comparison or clean-film false-alarm rate
is claimed. S3 smoke-suite build measurements are reported separately below.

S2 detection validation passed the unchanged S1 smoke truth across five frame
rates and the documented Local/Kids policies. See [the S2 report](../../docs/S2_REPORT.md)
for synthetic accuracy, interval/property checks, tool gates and the unmet
20× throughput target. The approximately ten-minute CC-BY film benchmark and
unreviewed events are saved in [s2_benchmark.json](../../docs/s2_benchmark.json).
These build checks do not replace the broader S4 evaluation.

S1 build checks are recorded in [S1_REPORT.md](../../docs/S1_REPORT.md).

S3 mitigation build checks run the complete available smoke suite at five frame
rates and all three profiles, retaining S1/S2 expectations. Per-case viewing
cost and verifier outcomes are in [s3_synthetic.json](../../docs/s3_synthetic.json);
whole-film Broadcast measurements and limitations are in the
[Session 3 report](../../docs/S3_REPORT.md). These do not establish the broader
S4 evaluation gate or a clean-film false-alarm rate. The extended-warning
regression exercises an explicit unresolved Kids outcome under fixed timing.

S3 available-smoke results: 80 encoded clips, 240 profile checks, all verified at
-0.15/0/+0.15 s, zero unresolved smoke cases. Per-profile must-fail counts are
35/40/50 (Broadcast/Local/Kids); FN=0 and FP=0 against unchanged expectations.
All 45 Broadcast must-pass cases receive zero veils. Mean active-support opacity
on the must-fail sets is 0.4201/0.4295/0.4636; mean absolute luminance distortion
is 23.1552/24.9873/31.1950 cd/m². See the S3 report for denominators, warning
policy, the separately unresolved extended-warning regression and timing limits.

The approximately ten-minute Broadcast film pipeline completed in 3,015.374 s
with a warm cache (0.1978x real-time), but retained three unresolved segments,
including two residual failures after one retry. Publication was correctly
refused; only debug JSON and the numerical report were written. Film mitigation
and performance require further work. See s3_benchmark.json and the S3 report.
