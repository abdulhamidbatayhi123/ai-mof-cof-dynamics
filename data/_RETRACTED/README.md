# Retracted artifacts

Preserved, not deleted, so every retracted number stays reproducible.
Excluded from `validate.py` gates (which scan `data/*.pth`, not subdirectories).

| file | retraction | why |
|---|---|---|
| `pikan_weights_final.pth` | **A2** | 85,508 / 85,548 learnable parameters (100 %) are NaN. Training diverged; root cause was the unbounded van't Hoff factor with a sign-unconstrained `T*`. Produced no valid result. |
