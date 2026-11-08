# Prior art and comparison status

Inspected author sources; this is an initial map, not an exhaustive novelty review.

| Method/source | Relevance | Current comparison status |
|---|---|---|
| [PocketMiner](https://github.com/Mickdub/gvp/tree/pocket_pred) | Single-structure cryptic prediction using GVP; official examples and model weights. README describes TensorFlow/UNIX environment and labels 0/1/2 with uncertain residues excluded. | Not executed; separate compatibility work required on Windows or partner Linux. |
| [CryptoBench](https://github.com/skrhakv/CryptoBench), [OSF data](https://osf.io/pz4a9/) | Official dataset, train/test folds and pLM benchmark. Author source links the [apolo implementation](https://github.com/skrhakv/apolo/tree/cryptobench-v2). | Metadata downloaded; initial development subset only; benchmark checkpoint execution pending. |
| [ProteinMPNN](https://github.com/dauparas/ProteinMPNN) | Frozen inverse-folding compatibility features; sequence likelihood is not force-field energy. | Cached adapter pending; no benefit claimed. |
| [PETIMOT](https://github.com/PhyloSofS-Team/PETIMOT) | Motion prediction is adjacent prior art. | Source located; detailed task/protocol review pending. No general motion novelty claim. |
| [OpenMM user guide](https://docs.openmm.org/latest/userguide/application/02_running_sims.html) | Whole-context force/energy descriptors with explicit preparation and force field. | Optional adapter pending; never infer thermodynamic opening probabilities from potential energy. |

dMaSIF, Seq2Pocket, FrustraPocket, AE-PocketMiner, DETANGO and UniSite are queued for detailed source review. A combined list of familiar components does not establish novelty. The decisive hypothesis is whether regional contact factorization and feedback improve localization over a matched ordinary auxiliary-contact model. Geometry baseline comparisons alone cannot establish competitiveness.

Execution update: official PocketMiner187062df3c94127e991669768009141a08fd5d8b code/weights ran under TensorFlow2.15.1 CPU with explicit author-order nm backbone tensors. Strict model-variable restore uses Checkpoint.read, matching author's write. Results and preprocessing deviations are in docs/DEV120_RESULTS.md. Frozen ProteinMPNN and OpenMM adapters also executed; prior table records the original inspection stage, not latest execution state.
