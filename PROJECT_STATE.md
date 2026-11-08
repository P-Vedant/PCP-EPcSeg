# Project state — current

Objective: reproduce and test apo-only cryptic-pocket localization with regional contact-change prediction. This is an ongoing research project, not a publication-ready result.

Checkout: C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg
Branch: research/bootstrap. Verified implementation revision: 169c2075476de808ae7242c770d75ed08f97ada3 (or later handoff commits).
Machine A: RTX5070 Laptop, 8151MiB, Windows, 32GB RAM; driver592.27, Python3.11.9, torch2.11.0+cu128. Partner B unavailable/unverified. No cloud compute used.

## Implemented, executed and validated

- Real CUDA forward/backward/optimizer; isolated dependency check; four meaningful core tests.
- Versioned mmCIF preparation, ligand identity checks, residue/sequence mapping, apo-only sparse edges, contact labels and formation-coverage audit. Official test evaluation is disabled.
- Four-layer width96 geometric model, 12 learned regions, region-pair contact formation/breakage and feedback; 1,030,642 allocated parameters. Baseline logistic/forest, pocket-only, ordinary auxiliary-contact comparisons.
- Train-only normalization/class weights; seeded runs; epoch/ten-minute checkpoints with optimizer/scheduler/scaler/RNG/sampler position; immutable manifests, model/feature/data hashes; no overwrite of existing runs.
- Frozen whole-context ProteinMPNN:29/29 small cohort,132/132 larger cohort. Apo-only inference automatically caches frozen features; CPU inference matches prepared-feature inference within1.2e-6 probability.
- OpenMM Amber14/OBC2 context adapter; explicit crystal-water replacement, no cofactor deletion;8/29 valid proteins. Bounded/concat/no-energy/missingness-only and IF-shuffle controls executed. Energy disabled in larger selected configs.
- Official PocketMiner frozen code/weights ran on8 and35validation proteins; all model variables verified; explicit mmCIF mapping and masks, author atom order/nm units. Isolated TensorFlow2.15.1 CPU environment.
- Nine larger neural runs:97training/35validation, seeds17/23/47,20epochs. Matched numeric evidence in docs/DEV120_RESULTS.md.
- GPU-trained checkpoint loaded on CPU; exact next optimizer step checkpoint equivalence tested; shuffled-feature evaluation replay reproduced metrics exactly. Cross-GPU loading remains pending.
- Complete139-file run/data transfer archive exported, SHA-256 verified on import. Checkpoint/transfer hashes in HANDOFF.md.
- Profiled20warmed steps at N59/275/831:0.0155–0.0182sec/step; max allocated349,337,088bytes, reserved392,167,424bytes. Not a partner-GPU guarantee.

## Findings and claim boundary

Larger mean validation macroAP: regional .255615, ordinary auxiliary .255062, pocket-only .248865. Official PocketMiner .262020. Identical-mask regional mean-seed minus PocketMiner: -.005872, paired-protein95%[-.050246,.039338]. Regional-vs-auxiliary gains are [-.001551,.000196,.003014]. The +.03 promotion gate is NOT met; no demonstrated regional-mechanism advantage or SOTA claim.

No family independence: nine larger train/validation pairs exceed30%identity/80%coverage. Prior16apo/paired chains and known CATH overlap are saved in configs/prior_exposure.json;3NX1 appears in official test. Official protocols and any new independent split must remain separate. All test performance remains locked.

## Current phase and pending work

Full eligible official-training preparation/audit is the next durable worker: scripts/prepare_full.py. It requests666training and219validation apo IDs from the official training pool, records exclusions, runs sequence audit, saves a handoff and pushes authorized status on completion. Check active-jobs.json and actual PID/logs; never duplicate a live job. Its final handoff is docs/FULL_DATA_PREP_HANDOFF.md.

Pending: full-data coverage; prior aliases/duplicate/full-sequence/homolog/CATH/SCOP audit; a strong sequence benchmark; pocket-level localization metrics; family-stratified uncertainty/controls; full-data final configuration freeze and locked evaluation; partner-GPU portability. Candidate-state energy and surfaces remain optional/unimplemented. Do not expand architecture to hide the failed regional ablation.

Data/cache/checkpoints/external code/environments remain ignored. Source/state commits are pushed to the user's existing origin. PowerShell .ps1 execution was blocked; Python launchers are used without changing system policy. Read HANDOFF.md for next commands.
