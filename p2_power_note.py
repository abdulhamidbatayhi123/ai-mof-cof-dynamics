"""Power of the frozen Paper 2 decision rules, stated in the form a Registered-Report
journal asks for. Derived only from the FROZEN calibration (PREREG_P2 s.4.4): the boundary
estimator's SD is 0.089 decade (100 simulated datasets, 9 Da levels x 20 replicates), and
the prereg's convention is that a shift d is resolved at two-sided alpha = 0.05 with power
Phi(d/SD - z_{0.975}) (so 2.8 x SD = 0.25 decade at 80 % power).

Nothing here changes the design. It restates what the frozen design already implies:
  * the shift resolvable at 80 % and at 95 % power;
  * the power at the frozen MDE (0.25 decade) and at H2c's predicted factor 2 (log10 2).

    python p2_power_note.py      -> results/p2_power_note.json
"""
import json
import math
from statistics import NormalDist

SD = 0.089          # decade; PREREG_P2 s.4.4, tests/test_p2.py calibration docstring
ALPHA = 0.05
MDE_FROZEN = 0.25   # decade; PREREG_P2 s.4.4
OUT = "results/p2_power_note.json"

N = NormalDist()
z_a = N.inv_cdf(1 - ALPHA / 2)


def resolvable(power):
    return (z_a + N.inv_cdf(power)) * SD


def power_at(d):
    return N.cdf(d / SD - z_a)


res = {
    "source": "PREREG_P2_discoverability.md s.4.4 (frozen at d562f19): SD 0.089 decade, MDE 0.25 decade",
    "sd_decade": SD, "alpha_two_sided": ALPHA,
    "shift_resolvable_at_power_0.80_decade": round(resolvable(0.80), 4),
    "shift_resolvable_at_power_0.95_decade": round(resolvable(0.95), 4),
    "power_at_frozen_mde_0.25": round(power_at(MDE_FROZEN), 4),
    "power_at_factor_2_shift_log10_2": round(power_at(math.log10(2)), 4),
    "log10_2_decade": round(math.log10(2), 4),
}
# The prereg's convention uses the SD of ONE boundary estimate. H2b's gap and H2c's shift are
# differences of two estimated boundaries; if the two estimates were independent, the SD of
# the difference would be sqrt(2) x 0.089. Stated alongside, so the reader sees both.
SD_DIFF = math.sqrt(2) * SD
res.update({
    "sd_difference_if_independent_decade": round(SD_DIFF, 4),
    "difference_shift_resolvable_at_power_0.80_decade": round((z_a + N.inv_cdf(0.80)) * SD_DIFF, 4),
    "difference_shift_resolvable_at_power_0.95_decade": round((z_a + N.inv_cdf(0.95)) * SD_DIFF, 4),
    "difference_power_at_factor_2_shift": round(N.cdf(math.log10(2) / SD_DIFF - z_a), 4),
})
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
for k, v in res.items():
    print(f"{k}: {v}")
