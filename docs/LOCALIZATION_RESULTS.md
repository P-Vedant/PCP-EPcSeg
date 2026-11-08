# Development pocket localization proxy

This fixed protocol was declared after residue-ranking experiments, before inspecting localization results. It was not tuned. It is NOT ligand-center DCC or an independent test.

Candidates: top10% valid residue scores, connected at8A, score-weighted centroids ranked by mean score. Targets: official apo residue sets merged at Jaccard>=.5, unweighted centroids. Maximum one-to-one matching within4A. All methods share the exact same residue mask per protein.

| Method | Top1 protein hit | Top3 protein hit | Top3 macro pocket recall |
|---|---:|---:|---:|
| PocketMiner | 0.0286 | 0.0571 | 0.0571 |
| forest | 0.0000 | 0.0000 | 0.0000 |
| regional-s17 | 0.0286 | 0.0286 | 0.0143 |
| regional-s23 | 0.0000 | 0.0571 | 0.0286 |
| regional-s47 | 0.0000 | 0.0286 | 0.0286 |
| auxiliary-s17 | 0.0286 | 0.0286 | 0.0143 |
| auxiliary-s23 | 0.0000 | 0.0571 | 0.0286 |
| auxiliary-s47 | 0.0000 | 0.0286 | 0.0286 |
| pocket-s17 | 0.0000 | 0.0571 | 0.0571 |
| pocket-s23 | 0.0286 | 0.0857 | 0.0571 |
| pocket-s47 | 0.0286 | 0.0286 | 0.0286 |

Evaluated 35 proteins. Complete target/predicted centroids, membership and input hashes are saved in outputs/localization-dev120-v1.json. No family independence or physical pocket-geometry claim follows from this proxy.
