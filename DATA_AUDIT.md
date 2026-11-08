# Data audit

Author sources: https://github.com/skrhakv/CryptoBench and https://osf.io/pz4a9/. Inspected repository SHA 9a3432f479325ca3c9fdc3b8612715ab5b6edecc. OSF node license metadata identifies MIT; repo code also MIT. Raw metadata and structures remain local; no dataset redistribution via Git.

Official dataset has 1,107 apo IDs. folds.json contains test=222, train-0=219, train-1/2/3=222 each, disjoint by apo ID. Metadata SHA-256s are in each prepared index. Original folds are unchanged under data/raw/folds.json. SPLITS.json describes the current **development subset**, not a replacement official split.

First subset requested 24 train and 8 validation PDBs, sorted IDs, from official training folds only; eligible 21 train + 8 val. Excluded 1d7kA-B and 1g0sA-B (multichain IDs unsupported), 1f8aB (<80% valid matching resolved contact positions). Full failure/provenance records in data/prepared-24/index.json. Deterministic lexicographic subset may be unrepresentative; not a final benchmark.

No selected train/val UniProt overlap or >=30% identity over >=80% longer-chain aligned coverage was found. That check uses global alignment of resolved chains; it is not a full alias/family audit. CATH/SCOP coverage and pretraining overlap remain unknown. Family-independent uncertainty cannot yet be claimed.

All prior exposure supplied by user is preserved in configs/prior_exposure.json. Exact PDB intersections with official splits: test 3nx1; train-1 2w9t; train-3 5nia. None occur in the initial selected subset. Paired structures, aliases, duplicate sequences, close homologs and CATH topology 3.40.190 remain exposure controls for any **new** independent test. Do not alter official test and label it an official comparison. No official test performance has been computed.

Structure/label policies are detailed in docs/SCHEMA.md. Raw RCSB mmCIFs preserve full context. Core graph uses one standard resolved chain; MPNN uses all resolved standard protein chains. ProteinMPNN excludes unresolved backbone positions via masks. All selected curated holo ligands resolve uniquely by author chain/name/residue ID. No holo coordinates or ligand-derived crops enter inference. Official positive pocket annotations are unioned on the selected chain; background may contain unannotated positives. Contact supervision uses a deterministic main holo pair, exact sequence-match masks, C-beta/C-alpha and 8 A threshold, excluding polymer neighbors <=2.

Observed candidate formation coverage: 1,638/1,854 resolved true formed contacts (88.35%) across initial prepared data. This ceiling must be reported with contact metrics. Matched positions and unmapped positives are saved per protein.

Frozen MPNN code/checkpoint: 8907e6671bfbfc92303b5f79c4b5e6ce47cdef57, v_48_020, noise=0, unconditional structure-conditioned probabilities. 29/29 extracted. Structure/code/checkpoint/settings hashes and masks are in data/features-24/index.json and sidecars. Outputs are compatibility statistics, not physical energies.

Energy: Amber14/OBC2 implicit solvent, pH7, retained protein/ions/cofactors; remove only crystal waters explicitly with count. Hydrogens added, no missing-heavy-atom repair or minimization. Full 1A4U succeeded after water-policy correction. Multi-protein coverage and label/family bias are pending. Missing energy must remain masked; no cofactor deletion to force parameterization.
