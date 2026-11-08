# Tasks

| ID | Owner | Status | Dependencies | Files |
|---|---|---|---|---|
| T01 | A | active | none | environment, state files, configs |
| T02 | A | pending | T01 | data preparation, splits, audit |
| T03 | A | pending | T02 | baseline, metrics |
| T04 | A | pending | T02 | regional model, trainer, inference |
| T05 | B | unassigned | T02 | frozen ProteinMPNN adapter |
| T06 | B | unassigned | T02 | energy, established predictors |
| T07 | A | pending | T03-T06 | ablations, locked evaluation, transfer |

Shared schema changes are integrated by A. B is not connected; commands do not imply remote execution.
