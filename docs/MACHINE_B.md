# Partner B tasks (remote execution unverified)

No access to B was assumed. Verify its GPU/VRAM/OS with `python -m pcp hardware`; local A is actually an 8 GB RTX5070 Laptop. The same architecture/microbatch1 fits A's initial tested sizes, not a guarantee for B.

1. Pull research/bootstrap in the existing authorized checkout. Create a task branch for B; do not concurrently edit A's model/trainer/schema files.
2. Create isolated Python3.11 environment; install torch2.11.0+cu128 from official index, then `pip install -e .`; run `python -m pcp hardware` and `python -m unittest discover -s tests -v`. Commands were tested on A, not B.
3. Receive an explicitly selected transfer archive by the already authorized transfer method. `python -m pcp import --archive <archive> --destination <empty-dir>` verifies hashes and refuses overwrites. No transfer service or credentials were invented.
4. Validate the checkpoint on CUDA on B, using the same resolved sequence and apo mmCIF. Record GPU/driver/PyTorch and prediction differences relative to A. Do not claim this before executing.
5. Priority B task is an official external predictor: inspect PocketMiner's author TensorFlow environment or CryptoBench pLM checkpoint. Bound install debugging to45min. Save raw per-residue predictions with explicit residue mapping and official mask semantics. Follow docs/PRIOR_ART.md.
6. Optional IF extraction uses deterministic shards0-31. Proposed assignment A=0-15, B=16-31. Each writes its own `--output cache/B-shard-N` directory and own manifest checkout. `python -m pcp features --index <index> --output cache/B-shard-16 --shard 16`. Do not train from a partial feature index as if all rows have features; merge/validate completed shard indices first (merge tool pending).

Keep dataset/cache/checkpoint files out of ordinary Git. User's remote is already public; only authorized code/state changes are pushed. Do not create a new public dataset or cloud job. Record all remote execution evidence in your handoff.
