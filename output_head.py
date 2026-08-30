"""Shared output parameterisation for every surrogate in the ladder.

ONE definition, imported everywhere. Six model classes previously carried their
own copy of this three-line head, and every copy had the same latent defect:

    T* = 1.0 + t* * raw_T          # unbounded

`raw_T` is a free network output, so `T*` can cross zero. The isotherm's van't
Hoff factor `exp(-dH/(R T))` then diverges, the forward pass returns inf, and
every downstream gradient becomes NaN. That is the documented root cause of the
first checkpoint in this project being 100 % NaN (retraction A2, defect B3).

Fixing it in PIKAN alone would have left the identical trap armed in DeepONet,
DeepOKAN, FNO, the WNO proxy and the MLP baseline — and it would have fired
during the ladder, arm by arm, looking like an architecture result.

The head enforces three things structurally rather than by penalty:

  c*, q* >= 0        softplus
  c*, q* = 0 at t=0  multiplication by the t* envelope
  T* bounded         T* = 1 + dT_max * tanh(t* * raw_T)

`dT_max` is in units of T_ref and is generous next to the adiabatic rise
(beta ~ 3), so it never binds on a physical solution — it only prevents the
pathological one.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F

DT_MAX_DEFAULT = 0.5


def apply_bounded_head(raw_c, raw_q, raw_T, dT_max: float = DT_MAX_DEFAULT):
    """Physically BOUNDED outputs. No time envelope; the IC is a loss term.

    The maximum principle for this system gives hard bounds that the softplus
    head throws away:

        0 <= c <= c_in     (nothing can exceed the feed concentration)
        0 <= q <= q_max    (nothing can exceed the saturation capacity)

    In normalised units both are [0, 1], so a sigmoid enforces them exactly. The
    softplus head is unbounded, and on temporal extrapolation it diverges to
    nRMSE ~26,000 (data-only) and ~6,000 (physics-informed) - errors thousands of
    times the data range, from a quantity that provably cannot exceed 1.

    The `t_star` envelope used by `apply_output_head` is also not the right IC.
    It forces c <= t everywhere, including at the inlet where c should reach c_in
    almost immediately. Boundedness and the initial condition are separate
    concerns and are separated here: the bound is architectural, the IC is a
    residual term the caller adds.
    """
    c_star = torch.sigmoid(raw_c)
    q_star = torch.sigmoid(raw_q)
    T_star = 1.0 + dT_max * torch.tanh(raw_T)
    return c_star, q_star, T_star


def apply_output_head(raw_c, raw_q, raw_T, t_star, dT_max: float = DT_MAX_DEFAULT):
    """Map raw network outputs to physical (c*, q*, T*).

    All four arguments broadcast together; shape is left to the caller so this
    works for point-wise models (N, 1), operator models (B, N, 1) and grid
    models (B, 1, Nz, Nt) alike.
    """
    c_star = t_star * F.softplus(raw_c)
    q_star = t_star * F.softplus(raw_q)
    T_star = 1.0 + dT_max * torch.tanh(t_star * raw_T)
    return c_star, q_star, T_star


def temperature_is_bounded(model_forward, n=4000, seed=0, device="cpu", **kwargs):
    """Return (lo, hi) of T* over random inputs. Used by validate.py.

    `model_forward` must be a zero-argument callable returning a tensor whose
    last-but-one or last axis holds (c, q, T); it is the caller's job to slice.
    """
    torch.manual_seed(seed)
    out = model_forward()
    return float(out.min()), float(out.max())
