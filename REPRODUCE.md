# Reproducing the paper

Three tiers. Tier 0 needs no data and runs on a laptop in minutes; Tier 1 needs the deposited
dataset and about one to two CPU hours; Tier 2 is the full rerun. Every number in the
manuscript is a macro resolved from a results file under `results/` (see `paper/numbers.py`,
which names the file and the path of each one), so Tier 0 already rebuilds every number.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; on Linux or macOS: source .venv/bin/activate
pip install torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt pytest psutil
```

Python 3.12. Everything ran on CPU; nothing needs a GPU. To compile the PDFs, install
[tectonic](https://tectonic-typesetting.github.io) and put it on PATH.

## Tier 0: no data, minutes

```bash
python paper/numbers.py          # every number in the paper, from results/*.json -> paper/numbers.tex
python build_paper.py            # refuses any number in the manuscript that is not such a macro
python build_paper.py --pdf      # also compiles paper/manuscript.pdf (needs tectonic)
python validate.py --only solver     # the solver against four closed-form solutions, mass closure
python validate.py --only isotherm   # the isotherm gates
python validate.py --only residual   # the training residual is the solver's equation
```

Gates that need the field arrays report SKIP without them; that is expected in Tier 0.

| Figure or table | Command | Reads |
|---|---|---|
| Fig. 1 (schematic) | `python fig_schematic.py` | `results/schematic_sample.json`, `results/schematic_modes.json` |
| Fig. 2 (MOF-303 anchor) | `python compare_lassitter.py` (re-solves, about 2 min) | `refs/Lassitter2024_fig10_digitised.csv` |
| Fig. 3 (ladder) | `python fig_ladder.py` | the rung verdict files listed in its docstring |
| Basis against map | `python l5_mapterm_v2.py` (needs data, Tier 1) | writes `results/l5_mapterm_v2.json` |
| Coarse solve against surrogates | `python coarse_vs_surrogates.py` | `results/coarse_solver_baseline.json`, `results/l5_v2_results_24k.json`, `results/l1_v2_results.json` |
| Screening and named frameworks | `python dd_screening_frameworks.py analyse` | `results/dd_*.json` |
| Supplementary figures | `python fig_dataset_v2.py`, `fig_water_mofs.py`, `fig_operators.py`, `fig_warp.py`, `fig_rungs.py`, `fig_mechanism.py` | their docstrings |

## Tier 1: with the dataset, one to two CPU hours

Download the dataset record (DOI in the paper's data availability statement) into
`data/parametric_v2/` and check its SHA-256 sums (`sha256sums.txt` in the record). Then:

```bash
python l5_mapterm_v2.py --ps 8 128 --seeds 42          # basis and map terms, two basis sizes
python coarse_solver_baseline.py                       # coarse grids on one sample per material
python fitted_classical.py                             # the fitted closed forms
python dd_screening_frameworks.py b1                   # screening, out of fold (DeepONet takes longest)
```

Each script writes its results file; compare it with the tracked one. Floating-point
reduction order differs across BLAS builds, so agreement is to about three significant
figures, not bit for bit.

## Tier 2: everything

The full ladder took about 18 worker-hours to generate the data and several CPU days to
train every arm. The scripts are resumable and named by rung (`run_l1_v2.py`, `run_l2_v2.py`,
`run_l5_v2.py`, `run_l6_v2.py`, `run_l7_v2.py`, `chain_l4b_v3.sh` (which runs `run_l4b_v2.py` with
the corrected residual) and the generators
`gen_parametric_dataset.py --design v2`). `autorun.sh` is the sequence that was actually run.
