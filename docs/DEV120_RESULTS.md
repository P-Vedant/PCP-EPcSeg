# Larger development evidence

97 training /35validation proteins; 28exclusions from160requested structures. All official test results remain locked. Frozen MPNN succeeded132/132. Neural runs use20epochs and seeds17/23/47, best validation checkpoint.

| Mode | Seed | Macro AP | Formation pooled AP | Breakage pooled AP |
|---|---:|---:|---:|---:|
| regional | 17 | 0.248614 | 0.033412 | 0.033224 |
| regional | 23 | 0.261335 | 0.033562 | 0.033365 |
| regional | 47 | 0.256896 | 0.033732 | 0.034254 |
| auxiliary | 17 | 0.250165 | 0.032419 | 0.033439 |
| auxiliary | 23 | 0.261139 | 0.033428 | 0.034144 |
| auxiliary | 47 | 0.253882 | 0.033086 | 0.035310 |
| pocket | 17 | 0.241477 | 0.020147 | 0.015936 |
| pocket | 23 | 0.259738 | 0.017176 | 0.022701 |
| pocket | 47 | 0.245380 | 0.013070 | 0.017025 |

Mean macro AP by mode: `{"regional": 0.2556150247756422, "auxiliary": 0.2550621448465999, "pocket": 0.24886498536286916}`.

Official PocketMiner (adapted explicit atom mapping): macroAP 0.262020. Regional mean-seed AP minus PocketMiner on identical residue masks/proteins: -0.005872; paired protein bootstrap95% [-0.0502462223909968, 0.03933846334901852].

Regional minus ordinary auxiliary, by seed: [-0.0015513218050331734, 0.00019551812084012132, 0.003014443471320072]. The predeclared +.03 gain criterion over the strongest matched predictor is not met. No supported regional-mechanism novelty claim.

The interval samples proteins, not independent families, and averages each protein's AP over three seeds (not ensemble-probability AP). Nine train/validation sequence-similarity pairs exceed30%identity/80%coverage. No family-disjoint or independent-cohort inference is justified. Official model pretraining overlap remains unknown.

The model improves substantially over the simple geometry baseline on this larger development cohort, but that alone does not support the proposed CV contribution. More rigorous family/exposure audits, full eligible official training data, a strong sequence baseline and pocket-level localization metrics remain pending.
