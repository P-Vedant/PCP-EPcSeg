# Project state

Objective: apo-only cryptic pocket localization with regional contact formation/breakage prediction.
Machine A: Windows, RTX 5070 Laptop GPU, 8151 MiB, driver 592.27. Partner B unavailable.
Phase: bootstrap. Existing checkout was clean at 9648717 on main. Remote: P-Vedant/PCP-EPcSeg.
Completed: prompt and repository inspection; GPU identification. Python 3.11.9 exists.
Pending: CUDA test, real data audit, baseline, regional model, scientific validation.
No scientific results, checkpoints or running research jobs yet. A Python environment inspection is pending.
No paid cloud work authorized. No public publication. Remote visibility must be verified before pushing.

User supplied prior 16 apo/paired chains: saved in configs/prior_exposure.json. Family/sequence audit remains mandatory. Torch 2.11.0+cu128 installed in isolated .venv; execution not yet verified. Stage T02 preparing real data; model code saved but unverified.

Verified: isolated torch 2.11.0+cu128 CUDA forward/backward/AdamW passed on sm_120; pip check passed. Four core tests passed (invariance/apo isolation, finite overfit/checkpoint, missing energy/contact identity, transfer path safety). First development index prepared; official test untouched. T03/T04 baseline and regional runs next.
