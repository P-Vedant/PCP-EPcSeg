# Two-day research build and master prompt for the IDE coding agent

Prepared November 7, 2026. Read this entire file, then start executing it in the current project.

## 1. Objective and honest scope

Build a reproducible research system for predicting cryptic protein binding sites from a single ligand-free structure and its sequence. A cryptic pocket is a binding cavity that becomes available after the protein changes shape.

Our proposed contribution is **learning coordinated regional contact rearrangements that support cryptic-pocket localization**, with frozen inverse-folding features and optional context-preserving energy information. The model must output pocket scores, predicted contacts that form or break, and region assignments. These are testable geometric predictions, not just a pocket heat map.

This is a proposed contribution, not an established novelty claim. Point clouds, equivariance, region pooling, inverse folding, energy features, and multi-task learning individually already exist. A combination alone is insufficient. We must demonstrate that the specific regional formulation fixes a measurable weakness of strong alternatives.

A complete runnable system in 48 hours is the engineering target. Competitive CVPR performance, scientific novelty, and acceptance cannot be promised on that schedule. Do not describe unfinished comparisons as state of the art. The approaching conference is CVPR 2027: registration November 10, 2026, full paper November 16, 2026, both Anywhere on Earth. Humans should handle enrollment; do not submit anything.

Use the existing CVPR_Cryptic_Pocket_Prototype.zip and feasibility report if available. The prior experiment used frozen ProteinMPNN features and simple classifiers. On 12 additional proteins, random-forest macro AP rose from about 0.2135 to 0.2773, but the exploratory confidence interval for the gain crossed zero and there were family-overlap concerns. All 16 previously inspected proteins are now development examples. These results justify investigation, not a competitive-performance claim.

## 2. What counts as progress

Implement all core stages: data audit, 3D representation, regional contact model, frozen inverse-folding features, training, matched baselines, ablations, reproducible evaluation, and portable checkpoints. Provide an operational energy adapter and measure its usefulness if preparation and coverage permit.

Keep the following distinctions explicit:

- Core: apo-only cryptic-site segmentation coupled to regional contact-change prediction.
- Supporting inputs: inverse-folding compatibility and energy/strain descriptors.
- Optional extension: candidate-state energy scoring and additional surface samples.
- Future work: thermodynamic opening probabilities, kinetic rates, validated collective variables, long molecular-dynamics sampling, mutation design, and general-purpose protein conformation generation.

Do not secretly replace the core with a toy classifier and call the task complete. Do not delay a working core to implement every optional idea. Record omissions and their consequences. No figures are required now; save numeric arrays and coordinate predictions needed to generate them later.

## 3. Hardware and simultaneous work

The two machines are separate:

| Machine | Expected GPU | Role |
|---|---|---|
| Naga / A | Desktop RTX 5070 Ti, normally 16 GB | Integration, main model training, larger batches |
| Partner / B | RTX 3070, normally 8 GB | Feature extraction, external baselines, ablations and additional seeds |

Verify actual GPU model, VRAM, OS, driver, CUDA availability, CPU, RAM and free disk. A laptop configuration may differ. Do not assume access to the other computer, pool VRAM, or use the obsolete L40S/5070 assumptions.

Use **independent jobs**, not synchronous multi-machine training, during this sprint. The same model and checkpoint must fit and run on the 3070. The 5070 Ti can use a larger microbatch, but adjust gradient accumulation to preserve effective batch size. Data-parallel training over a slow connection would add synchronization and setup costs without combining memory.

Use a current supported PyTorch CUDA build compatible with both Ampere and Blackwell. Check current official installation guidance and run a real forward/backward/optimizer CUDA test. Blackwell support appeared with CUDA 12.8 builds in PyTorch 2.7; do not interpret that as a requirement to install that old release. The old prototype's CPU-only dependency lock is unsuitable for this task.

Use portable PyTorch operations first. Avoid custom CUDA extensions and mandatory torch.compile. Use mixed precision only after finite-gradient checks. Keep numerically sensitive distances and losses in float32. Start with microbatch 1 and gradient accumulation.

Profile 20 warmed-up training steps on representative lengths, including optimizer state. Record peak allocated/reserved VRAM and seconds per step. Target roughly 6.5 GB or less on the 3070, leaving display/driver headroom; this is a design budget, not a measured guarantee. Adapt batch size/checkpointing before changing architecture.

Trainable network starting point: four sparse geometric message-passing layers, width 96, 8–16 learned regions, about 1–3 million trainable parameters as a target. Measure the actual count. Keep ProteinMPNN frozen and cache its features. Larger pretrained models may be used only for cached features if extraction fits; no foundation-model training.

## 4. Two-day schedule with explicit slack

These are planning budgets; replace runtime assumptions with measurements.

| Elapsed hours | Machine A | Machine B | Exit condition |
|---|---|---|---|
| 0–3 | Inspect repo, create project state and interfaces, GPU smoke test | GPU smoke test, inspect data sources and energy installation | Shared schema, source versions and runnable environments |
| 3–7 | Curate splits and implement data loader plus geometry baseline | Cache ProteinMPNN features; bounded energy feasibility check | Audited examples and first baseline evaluation |
| 7–13 | Implement regional/contact model and one complete training run | Implement an established predictor adapter; finish feature shards | End-to-end training/inference works; core code freezes |
| 13–16 | Fix integration, loss, memory and checkpoint issues | Verify energy coverage, baseline protocol and cross-machine checkpoint load | Stable training; optional modules explicitly enabled or disabled |
| 16–30 | Main configurations and validation-selected seeds | Matched baselines, ablations and remaining seeds | Comparable validation results and preserved checkpoints |
| 30–36 | Freeze configurations, run locked evaluation | Cross-check metrics, portability and independent-cohort evaluation if available | Evidence table, limitations and decision memo |
| 36–48 | Reserved for failures, incomplete training, critical reruns and handoff | Same; no architecture expansion | Reproducible deliverable with clear completed/pending status |

Start training as soon as the baseline works; do not wait for the energy branch. Reserve the final 12 hours rather than filling them with new features. Limit initial energy-adapter debugging to two hours and any one external-baseline installation to 45 minutes before documenting the blocker and choosing a viable alternative.

Use durable background processes with logs so training continues when an IDE agent session ends. Do not busy-poll. Estimate remaining work from measured throughput. If the full ablation matrix cannot finish, prioritize the strongest matched baseline, full model, no-regions/no-contact-coupling ablation, no-energy ablation, then additional seeds. Mark incomplete claims.

## 5. Repository, job ownership and transfer

Read existing AGENTS.md instructions, inspect git status, and preserve user changes. Use the existing project when suitable. Create a concise README and environment lock after a verified installation.

Required state files:

- PROJECT_STATE.md: objective, decisions, current phase, completed/pending work.
- HANDOFF.md: exact next actions and commands; always current.
- RUN_MANIFEST.jsonl: immutable records for each run.
- TASKS.md: task ID, owner A/B, status, dependencies and affected files.
- DATA_AUDIT.md and SPLITS.json: provenance, exclusions, leakage checks.
- CLAIMS.md: what evidence supports, what remains hypothetical.
- docs/PRIOR_ART.md: concise comparison to closest methods.

Create one stable configuration/schema interface before both people edit. A owns model/trainer/integration; B owns energy adapters/external baselines. Shared schema changes are proposed in TASKS.md and integrated by A. Use separate task branches; do not both edit the same file concurrently.

For code transfer, use an existing authorized private shared Git remote. If none is configured, prepare a Git bundle and copy instructions rather than creating a public repository. Never share accounts, credentials or API keys.

Keep datasets, cached features and checkpoints outside ordinary Git history. Implement export/import commands for a transfer archive containing only selected shards/checkpoints plus a SHA-256 manifest. Verify hashes on import. Use an existing authorized transfer method; do not invent a server or assume SSH access.

Give preprocessing shards deterministic IDs derived from SHA-256 of canonical protein IDs. Assign disjoint shards explicitly. Cache keys must include structure hash, preprocessing version, feature-model checkpoint hash and feature settings. Use temporary files plus atomic rename. Each machine writes its own run directories; do not concurrently edit a shared results CSV or use Git as a live job queue.

Log code commit, resolved config, split hash, feature hashes, hardware, seed, start/end times and metrics for every run. Checkpoints include model, optimizer, scheduler, scaler, epoch, best validation metric, RNG states and sampler state where supported. Save at least each epoch and roughly every ten minutes. A restart must not silently overwrite an earlier run.

## 6. Data, labels and leakage controls

Use author-maintained CryptoBench data/protocols and PocketMiner examples where accessible. Inspect licenses and actual contents. Aim for the full feasible official training split; an initial 100–300 eligible pairs can support debugging but is not automatically an adequate final benchmark.

Use official splits for published-protocol comparisons. Separately create and report a stricter family-separated analysis where metadata permits. Do not silently alter an official split and call it the same benchmark.

Keep all structures, chains, conformations and close homologs of a protein in one partition. Use sequence clustering plus available CATH/SCOP/family information. Report thresholds, coverage and unresolved family relationships. Audit overlap with pretrained-model training data when possible; mark unknown overlap honestly.

All prior 16 inspected proteins, aliases and overlapping family members must be treated as development exposure when constructing a new locked test. Do not reuse them as fresh independent evidence.

Handle chain IDs, insertion codes, alternate locations, missing residues/atoms, engineered mutations and sequence mapping explicitly. Use ligand HETATM records with an explicit curated ligand identity; never treat an entire holo protein file as ligand atoms. Preserve biologically relevant surrounding chains or document a consistent single-chain protocol. Maintain validity masks.

Apo means ligand-free input; holo means the ligand-associated structure used for supervision/evaluation. At inference, prohibit holo coordinates, holo-derived crop centers, ligand positions, true contact changes and paired inverse-folding differences. Test inference with an apo-only input object that cannot access these fields.

Use official pocket labels where available. For newly derived labels, predeclare the ligand heavy-atom contact threshold, such as 5 Å, and save residue mappings. Other residues are incompletely annotated background, not experimentally proven nonbinding sites.

Define contact supervision before evaluation: for example Cβ distance below 8 Å, Cα for glycine, excluding sequence neighbors with separation at most two. Mask unresolved/mismatched positions. Include both formation and breakage because pockets can also emerge during closing motions.

Build candidate edges only from apo information: sequence edges plus sparse spatial neighbors and a bounded radius rule. Report what fraction of true formed contacts fall inside this candidate set. Never add holo-neighbor edges as an inference shortcut.

Pair structures by sequence; use a documented alignment for displacement diagnostics. Contact changes are rigid-motion invariant and do not require a potentially misleading whole-protein displacement label.

## 7. Representation and model

Use a protein's residue coordinates as a 3D point cloud with a sparse graph, retaining atom/backbone information for descriptors. This is a legitimate geometric-vision representation; a point cloud does not require camera images. Do not spend time rendering 2D protein images.

Core node inputs: amino-acid identity, local backbone geometry, exposure/density descriptors, valid masks, and cached ProteinMPNN features. Core edges: relative distances, sequence separation and invariant geometric descriptors. Avoid unnormalized absolute coordinates in scalar predictions.

The frozen inverse-folding adapter should process the complete resolved protein context, then pool into regions. Extract native-residue negative log probability, entropy and optionally compact probability vectors. It must not interpret sequence likelihood as physical energy or direct evidence of deformation. Coordinate-noise sensitivity, if retained, is explicitly a robustness feature.

Surface samples are an optional extension: at most about 1,024–2,048 samples with normals/chemical attributes, mapped to residues. They must add measured value over the residue cloud. Do not make an external surface-meshing tool a mandatory day-one dependency. Never claim the residue-cloud model is a molecular-surface network if that branch is absent.

Implement the proposed geometric mechanism concretely:

1. Encode local geometry with an existing invariant/equivariant sparse backbone.
2. Predict soft region assignments from apo features; pool context into region embeddings. Use modest spatial-coherence and anti-collapse regularization, reporting the chosen formulation.
3. Predict formed/broken contact probabilities on the apo-defined candidate edges. Include both local edge evidence and region-to-region interaction evidence.
4. Feed the predicted rearrangement evidence back into the pocket decoder. This creates a testable relationship between structural reorganization and localization, rather than merely displaying an unrelated auxiliary head.
5. Apply supervised contact-change loss and pocket loss, with region regularization. Start with documented fixed weights; permit only a small validation-only search.
6. Add energy features through a masked, bounded learned adapter. Compare this with plain concatenation and with no energy.

Suggested regional factorization: soft assignments S pool node features; a small region-pair module produces formation/breakage scores B. For candidate residue pairs, combine local logits with the corresponding entries of S B S-transpose. Aggregate predicted incident contact changes back to nodes for the pocket head. Compute only candidate edges, not a dense residue-pair matrix.

This is an implementation hypothesis, not a claim that low-rank factorization is new. Compare against the same backbone/capacity with ordinary auxiliary contact prediction but no regional factorization or feedback. If that comparison removes the gain, the proposed CV mechanism is unsupported.

Do not equate attention maps or soft regions with experimentally established functional domains. Evaluate region/motion associations quantitatively. Do not claim that contact logits constitute a physically realized open conformation or that predicted couplings establish causality.

## 8. Segmented snapshots and existing energy models

Interpret segmented snapshots as 3D regions within protein conformations, not disconnected fragments. Cutting out a segment changes its interactions, boundaries and apparent energy. Keep the whole prepared protein or an explicitly documented environment during scoring.

Implement a common energy-adapter interface with provenance, units, masks and failure reasons. Preferred inexpensive starting point: OpenMM with a supported protein force field and consistently chosen solvent treatment. Existing licensed Rosetta/PyRosetta or validated frustration tools are alternatives only if already available and appropriate; do not let installation/licensing consume the sprint. Do not use a small-molecule energy model on proteins without validated coverage.

Standardize protonation assumptions, hydrogens, missing-atom repair, termini and retained cofactors. Record failures. Never silently delete essential metal sites/cofactors to make parameterization pass. Do not reconstruct long missing loops from the target holo structure.

First implement apo-context descriptors: clashes and geometry strain; if OpenMM succeeds, whole-system potential energy and atom-force magnitudes pooled into residue/region descriptors. Force magnitude is a strain proxy, not a local energy. Avoid pretending that a global force-field energy has a unique per-residue decomposition.

Then, only if profiling permits, score a small fixed set of apo-generated candidate snapshots:
- Use a documented low-frequency elastic-network or bounded local perturbation generator, independent of holo labels.
- Define candidate patches from apo geometry. Keep the rest of the protein present.
- Transfer movements to atoms consistently and apply short restrained cleanup with fixed limits. Preserve the intended movement rather than fully minimizing it away.
- Compare the same atom composition, protonation, force field and solvent settings against the same prepared apo reference.
- Record whole-system delta potential energy, changed-region size, clash change and preparation validity. If restraints were used for cleanup, exclude artificial restraint energy from the reported physical potential.
- Treat these as proposed perturbations; they are not equilibrium samples or a validated transition path.

Cache descriptors and aggregate the local candidate evidence into the learned regions. Cap the number of candidates and profile a small subset before scaling. No on-the-fly OpenMM call inside every training minibatch. No mandatory differentiation through a force field.

Use energy as an uncertain supporting signal, not an oracle: genuine cryptic states may be energetically disfavored without the ligand. Do not automatically reject every higher-energy candidate. Do not turn delta potential energy into an opening probability with a Boltzmann formula: entropy, sampling weights and state populations are missing.

Report energy preparation coverage by family/label and compare full/no-energy models on the same subset. Handle missing energy with masks fitted only from training data, plus an ablation to detect whether missingness itself predicts labels. If coverage or benefit is poor, keep the adapter working but disable it in the selected model.

Paired holo energy and inverse-folding changes may be retrospective analyses or training-only auxiliary targets, with a separate ablation. They are never inference inputs. Do not treat them as validated thermodynamic ground truth.

## 9. Baselines, training and scientific checks

Prioritize these comparisons, using the same examples and evaluation masks:

A. Geometry/identity logistic regression and random forest.
B. A strong available sequence-feature baseline, preferably the official CryptoBench or Seq2Pocket implementation/checkpoint when accessible.
C. The chosen geometric backbone with pocket loss only.
D. C plus inverse-folding/energy features by ordinary concatenation.
E. D plus ordinary contact-change auxiliary supervision.
F. Full regional contact-coupled model.
G. Full model without energy; full model without inverse folding.
H. Within-protein shuffled inverse-folding features as a diagnostic.

Run at least one relevant established pocket predictor using its official code/checkpoint where feasible, prioritizing PocketMiner and an accessible strong sequence baseline. Check AE-PocketMiner, DETANGO, FrustraPocket and UniSite as close prior art; implement additional comparisons only if resources allow. If a critical baseline is unavailable, state that the competitiveness claim remains unresolved.

For a claimed motion-method contribution, inspect PETIMOT and compare the relevant task or narrow the claim. General motion prediction with pretrained protein features and an equivariant graph is already prior art.

No test-set threshold tuning, checkpoint selection or architectural selection. Fit normalization and class weights on training data only. Use validation for early stopping and thresholds. Freeze choices before opening the final test results. Use three seeds for the decisive full-vs-strongest-baseline comparison if the measured budget permits.

Primary metric: mean per-protein average precision, with its exact definition. Also report pooled AP separately, per-protein AUROC where defined, recall at a fixed residue budget, and pocket-level top-k localization under a stated clustering/center protocol. Report contact formation and breakage AP separately; class imbalance makes raw accuracy misleading.

Report confidence intervals by protein or family, not by treating residues as independent. Include family-level results, failures and rigid-pocket/moving-nonpocket controls where labels permit. Treat calibration only as calibration of observed labels, not physical opening probability.

Meaningful implementation checks: apo-only inference isolation; split disjointness; chain/ligand mapping; rotation/translation invariance of scalar outputs; finite loss/gradients; one-batch overfit on training examples; checkpoint save/resume; cross-GPU checkpoint loading; missing-energy behavior. Do not spend time on trivial tests mirroring implementation.

## 10. Continuation gates and fallback decisions

Internal promotion criterion, chosen before inspecting the final test: target at least 0.03 absolute validation macro-AP gain over the strongest matched baseline, consistent direction across seeds/families, plus improved contact-change prediction. This is a resource-allocation heuristic, not statistical proof or a CVPR acceptance threshold.

- If memory fails: lower microbatch, enable activation checkpointing and reduce optional surface sampling. Keep a common model checkpoint compatible with both GPUs.
- If energy fails or adds no value: retain the adapter and report its ablation; train the regional model without it.
- If inverse folding adds no value: remove it from the selected configuration and preserve the negative result.
- If learned regions/contact feedback add no value over ordinary supervision: do not claim a new CV method. A simpler competitive predictor may still be useful, but its publication claim needs separate justification.
- If strong established predictors win: report the gap. Consider a rigorously supported efficiency/generalization contribution only if the measured tradeoff is substantial.
- If all novelty gates fail: preserve the reproducible benchmark and failure analysis; recommend a longer research cycle or appropriate workshop rather than relabeling an incremental model as a breakthrough.

Two apo/holo endpoints do not identify a trajectory, kinetics, energy barrier or validated collective variable. Keep those ambitions in a future-work section rather than making the current system appear to deliver them.

## 11. Deliverables and completion definition

Deliver working CLI commands for:
- environment/hardware check;
- data download/preparation and split audit;
- shardable feature extraction;
- baseline and full-model training;
- validation and locked evaluation;
- checkpoint resume;
- transfer-bundle export/import;
- inference from a new apo structure and sequence.

Provide configs for both machines with one common architecture. Save per-residue scores, contact probabilities, region assignments, evaluated residue IDs, metrics and provenance. These will support later figures.

A run is complete only if its data, code revision, resolved config, checkpoint and metrics can be linked. Provide measured training/inference time and peak memory, separating preprocessing from model inference and including energy costs in end-to-end comparisons.

Final report must distinguish implemented, executed, validated and pending. Include the best matched comparison, uncertainty, closest prior art, bottlenecks and whether the proposed contribution survived ablation. Do not fabricate results, plots, screenshots, logs or successful commands.

## 12. Mandatory session continuity and low-credit operation

Use bounded tool output, short logs and targeted searches. Do not repeatedly read whole repositories or re-download unchanged datasets. Do not spawn extra AI agents by default. Long training runs should execute as ordinary scripts without consuming continuous agent interaction.

After every completed task, before every long run, and at least every 15 minutes of active coding:
1. Update PROJECT_STATE.md, TASKS.md and HANDOFF.md.
2. Record the current commit or uncommitted patch status.
3. Record active process IDs, machine, logs, checkpoint paths and whether a job must remain running.
4. State the next three concrete actions with exact commands and expected outputs.
5. Give a brief user-facing summary: completed, evidence, blocker, next step.

Save proactively: do not rely on being able to detect the last token or an abrupt credit cutoff. A fresh account/session must be able to resume from disk without this chat history. Make meaningful local commits after coherent stages when consistent with repository instructions.

End each interactive response with a short copyable continuation block using this template, replacing placeholders with actual values:

~~~
Continue this project from the existing checkout; do not restart.
Read AGENTS.md, HANDOFF.md, PROJECT_STATE.md, TASKS.md and this master prompt.
Current machine/role: <A or B; verified GPU>.
Required code revision/branch: <actual hash and branch>.
Completed and verified: <brief facts>.
Running jobs: <run IDs, PIDs, logs; do not launch duplicates>.
Latest checkpoint and transfer manifest: <actual paths and hashes>.
Next task: <specific task ID>.
Run next: <exact command>.
Expected result: <file/metric/check that defines success>.
Known blocker or caveat: <actual issue or none>.
Preserve the locked test split and existing checkpoints.
After completion, update the handoff files and provide the next continuation block.
~~~

If the second machine is not available in this session, generate its exact task list and tested commands where possible; mark remote execution unverified. Continue useful local work. Do not claim that writing a command means it ran on the partner's GPU.

Begin now with repository inspection, hardware detection, the state files and the smallest end-to-end data/baseline run. Proceed autonomously within this scope. Use no paid cloud compute, public publication or destructive system changes.

## 13. Source starting points

These sources constrain the claims and implementation. Verify relevant details rather than treating this list as an exhaustive novelty review.

- CVPR 2027 dates: https://cvpr.thecvf.com/Conferences/2027/Dates
- NVIDIA RTX 5070 Ti specifications: https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/
- PyTorch Blackwell support background: https://pytorch.org/blog/pytorch-2-7/
- dMaSIF, CVPR 2021: https://openaccess.thecvf.com/content/CVPR2021/html/Sverrisson_Fast_End-to-End_Learning_on_Protein_Surfaces_CVPR_2021_paper.html
- PocketMiner paper: https://www.nature.com/articles/s41467-023-36699-3
- PocketMiner code/data: https://github.com/Mickdub/gvp/tree/pocket_pred
- CryptoBench: https://github.com/skrhakv/CryptoBench
- ProteinMPNN: https://github.com/dauparas/ProteinMPNN
- Seq2Pocket: https://academic.oup.com/bioinformatics/article/42/10/btag778/8931593
- FrustraPocket implementation: https://github.com/mariafreiberger/FrustraPocket
- PETIMOT paper: https://pubmed.ncbi.nlm.nih.gov/42473947/
- PETIMOT code: https://github.com/PhyloSofS-Team/PETIMOT
- DETANGO: https://github.com/luo-group/DETANGO
- UniSite: https://github.com/quanlin-wu/unisite
- AE-PocketMiner: https://pmc.ncbi.nlm.nih.gov/articles/PMC13228627/
- OpenMM force fields, solvent and minimization: https://docs.openmm.org/latest/userguide/application/02_running_sims.html
- Limits of cryptic-opening probability prediction: https://pubmed.ncbi.nlm.nih.gov/41945898/

