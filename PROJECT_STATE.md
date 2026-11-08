# Project state

Objective: apo-only cryptic-site segmentation coupled to regional contact formation/breakage prediction. Research hypothesis, not established novelty.

Checkout: `C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg`, branch `research/bootstrap`. Machine A is Windows, RTX 5070 **Laptop** GPU, 8,151 MiB, driver 592.27, 32 GB RAM. B is unavailable. No cloud compute used. Existing user-requested GitHub remote is public; only code, documentation, configs and numeric run records are pushed.

## Executed and verified

- Isolated Python 3.11.9 / torch 2.11.0+cu128; real CUDA forward/backward/AdamW passed on sm_120; pip dependency check passed.
- Official CryptoBench metadata downloaded from OSF: 1,107 apo IDs; 222 test and four disjoint training folds. MIT source/data metadata verified. Upstream Git SHA 9a3432f479325ca3c9fdc3b8612715ab5b6edecc.
- Initial development subset: 21 training / 8 validation proteins, 3 exclusions. No exact UniProt or >=30% identity / >=80% aligned coverage overlap between these selected train/validation chains. This does not establish family independence.
- User's prior 16 apo and paired chains saved in configs/prior_exposure.json. 3NX1 overlaps official test; 2W9T and 5NIA overlap official training. Official test results remain locked.
- Geometry logistic/random forest, pocket-only, ordinary auxiliary-contact, and regional/contact-feedback models all ran for matched 8-epoch neural configurations, seed 17. Saved models, per-residue/contact/region predictions, metrics and provenance.
- Four tests pass: rigid-motion invariance and apo-only schema; finite one-batch overfit and exact optimizer checkpoint next-step equivalence; identical-structure contact labels/missing-energy masking; archive path safety.
- GPU-trained checkpoint loaded for real apo-only CPU inference and CPU validation. Three-file transfer archive exported/imported and hashes verified. RTX 3070 portability remains unverified.
- 1,030,642 allocated model parameters. 20 warmed steps at N=128/284/532: ~0.0153-0.0159 sec/step; max allocated 227,280,384 bytes, reserved 308,281,344 bytes. This does not cover longer proteins or the partner GPU.
- Whole-context frozen ProteinMPNN features: 29/29 successful, ~14.05 sec extraction. Official code/checkpoint pinned to 8907e6671bfbfc92303b5f79c4b5e6ce47cdef57; hash-rich feature index saved.
- OpenMM 8.6.1 successfully computed whole-system potential and residue force magnitudes for 1A4U; pH7, Amber14/OBC2, explicit removal of 165 crystal waters, no cofactor deletion or heavy-atom repair. Initial water-template failure preserved. Coverage/usefulness not yet established.

## Evidence and decision

Small-subset validation macro AP: logistic .1375338; forest .1407221; pocket .1308283; ordinary auxiliary .1300634; regional .1302436. Regional gain over strongest measured baseline is negative. No novelty/performance promotion supported. Eight validation proteins and one seed are debugging evidence only.

Candidate formation coverage: 1,638 / 1,854 true resolved formed contacts (~88.35%). Omitted contacts cannot be predicted by this candidate set. Region attention does not identify functional domains or trajectories.

## Pending / running

See active-job.json (or active-jobs.json if present) and HANDOFF.md before starting jobs. Matched IF runs and energy coverage are the next stage. Expand official-training-only data after these checks; full benchmark and family-separated evaluation remain pending. External PocketMiner/pLM baselines, energy usefulness/missingness controls, additional seeds, pocket-level localization, family CIs, full prior-homolog/CATH audit, and cross-GPU loading are not completed. Candidate-state energy/surfaces are optional and unimplemented.

PowerShell execution policy blocks .ps1 launch on this device. Use Python launchers; system policy was not changed. Everything required to continue is on disk. Do not rerun existing run IDs or overwrite checkpoints.
