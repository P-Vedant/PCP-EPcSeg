# Executed development results

Regenerate: `.venv\Scripts\python.exe scripts/summarize_dev.py`.

21 training / 8 validation proteins, seed17; neural runs8 epochs. Official test untouched. These are debugging comparisons, not a competitive benchmark.

| Method | Macro AP | Pooled AP | Proteins |
|---|---:|---:|---:|
| dev24-auxiliary-s17 | 0.130063 | 0.121479 | 8 |
| dev24-baseline-s17/logistic | 0.137534 | 0.129989 | 8 |
| dev24-baseline-s17/forest | 0.140722 | 0.129206 | 8 |
| dev24-energy-bounded-s17 | 0.132236 | 0.126974 | 8 |
| dev24-energy-concat-s17 | 0.138354 | 0.136884 | 8 |
| dev24-energy-mask-only-s17 | 0.133367 | 0.127541 | 8 |
| dev24-if-auxiliary-s17 | 0.134135 | 0.126582 | 8 |
| dev24-if-pocket-s17 | 0.135684 | 0.127716 | 8 |
| dev24-if-regional-s17 | 0.133514 | 0.126550 | 8 |
| dev24-if-shuffled-s17 | 0.119062 | 0.111892 | 8 |
| dev24-pocket-s17 | 0.130828 | 0.121990 | 8 |
| dev24-regional-s17 | 0.130244 | 0.121650 | 8 |

Regional minus forest: -0.010478; paired protein bootstrap95% interval [-0.029131165775608085, 0.009650430370878293]. Family dependence remains unresolved.

Energy preparation coverage: 8/29. Validation valid IDs: ['1byiA', '1dqzA', '1e5lB']. Same-successful-subset comparisons: `{"if-regional": {"n": 3, "macro_ap": 0.17348189860343963}, "energy-bounded": {"n": 3, "macro_ap": 0.1727998110627945}, "energy-concat": {"n": 3, "macro_ap": 0.18764606016466678}, "energy-mask-only": {"n": 3, "macro_ap": 0.17480842979941102}}`.

Energy bounded/concat/mask-only runs use the same full prepared rows and masks. A mask-only improvement would suggest missingness confounding. Energy feature3 is reserved zero; active descriptors are log1p clash counts and log1p force magnitude. The whole-system potential is reported separately and never decomposed into local energies.

PocketMiner uses official frozen code/weights, strict checkpoint variable matching and explicit mmCIF atom mapping; all baseline/model scores must be compared on the adapter's same residue mask. Consult its metrics.json matched table. Pretraining overlap is unknown. No exact published-protocol reproduction claim.

The +.03 validation gain promotion gate is not met by the initial regional-vs-forest comparison. Larger data, matched seeds and family analysis are required; do not relabel this as a new proven CV method.
