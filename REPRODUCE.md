# Reproducing the paper

Three tiers. Tier 0 needs no data and runs on a laptop in minutes; Tier 1 needs the deposited
dataset and a few CPU hours; Tier 2 is the full rerun. Every number in the manuscript is a macro
resolved from a results file under `results/` (see `paper/numbers.py`, which names the file and
the entry of each one), so Tier 0 already rebuilds every number.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; on Linux or macOS: source .venv/bin/activate
pip install torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Python 3.12. Everything ran on CPU; nothing needs a GPU. To compile the PDFs, install
[Tectonic](https://tectonic-typesetting.github.io) 0.17.0 and put it on PATH.

## Tier 0: no data, minutes

```bash
python paper/numbers.py          # every number in the paper, from results/*.json -> paper/numbers.tex
python build_paper.py            # refuses any number in the manuscript that is not such a macro
python build_paper.py --pdf      # also compiles paper/manuscript.pdf (needs tectonic)
python make_si.py                # Supplementary S2, its references resolved against the main text
python validate.py --only solver     # the solver against four closed-form solutions, mass closure
python validate.py --only isotherm   # the isotherm gates
python validate.py --only residual   # the training residual is the solver's equation
```

Gates that need the field arrays report SKIP without them; that is expected in Tier 0.

| Figure or table | Script (Tier 0, from results files) | Results it reads | Written by (Tier 1/2) |
|---|---|---|---|
| Fig. 1 (workflow and worked example) | `fig_workflow.py` | `results/dataset_summary.json`, `dataset_summary_v3.json`, `workflow_example_v3.json` | `dataset_summary.py`, `workflow_example.py` (needs the v3 fields, about 2 min) |
| Fig. 2 (MOF-303 anchor) | `compare_lassitter.py` (re-solves, about 2 min) | `refs/Lassitter2024_fig10_digitised.csv` | itself |
| Fig. 3 (ladder) | `fig_ladder.py` | the rung verdict files in its docstring | the rung runners |
| Fig. 4 (basis against map, both designs) | `fig_basismap.py` | `results/l5_mapterm_v2.json`, `l5_mapterm_v3.json`, `dd_v3a1_deeponet.json`, `dd_v3_verdict.json`, `dd_v3a1_verdict.json`, `learning_curve_v2_verdict.json` | `l5_mapterm_v2.py`, `dd_v3.py`, `dd_v3a1.py` |
| Fig. 5 (screening, both metrics) | `fig_screening.py` | `results/dd_v3a1_verdict.json` | `dd_v3a1.py analyse` |
| Table 2 (named frameworks) | `paper/numbers.py` | `results/dd_additions_verdict*.json`, `dd_seed_robustness.json` | as above |
| Table of contents graphic | `fig_toc.py` | `results/dd_v3a1_verdict.json`, `dd_additions_verdict.json`, `dd_additions_verdict_v3.json` | `dd_v3a1.py analyse`, `dd_screening_frameworks.py analyse` |
| Verdicts of PREREG_DD_ADDITIONS | `dd_screening_frameworks.py analyse` | `results/dd_b1_predictions.json`, `dd_coarse_all.json`, `dd_b2_frameworks.json` | its other phases |
| Verdicts of PREREG_DD_V3 | `dd_v3.py analyse` | the files above, both designs | `run_dd_v3.sh` |
| Verdicts of PREREG_DD_V3 amendment A1 | `dd_v3a1.py analyse` | `results/dd_v3a1_deeponet.json`, `dd_v3a1_hgb.json`, `dd_v3a1_coarse_v*.json`, `dd_v3a1_fw*.json`, and the V3 files | `run_dd_v3a1.sh` |
| Supplementary figures | `fig_dataset_v2.py`, `fig_water_mofs.py`, `fig_operators.py`, `fig_warp.py`, `fig_rungs.py`, `fig_mechanism.py` | their docstrings | the rung runners |

## Tier 1: with the dataset, a few CPU hours

Download the dataset record (Zenodo, doi:10.5281/zenodo.23683358) and check its
SHA-256 sums (`sha256sums.txt`). Unzip the fields into place, unzip `manifests.zip` (it
creates `manifests/`) and copy each manifest next to its fields under the name the scripts
read:

| In the record | Put it at |
|---|---|
| `ai-mof-ladder-v2-fields-128.zip` | `data/parametric_v2/*.npy` |
| `manifests/manifest_v2.json` | `data/parametric_v2/manifest.json` |
| `ai-mof-ladder-v3-fields-128.zip` | `data/parametric_v3/*.npy` |
| `manifests/manifest_v3.json` | `data/parametric_v3/manifest.json` |
| `manifests/l6_v2_folds.json`, `manifests/v3_folds.json` | `results/` |
| `named-frameworks-v2-fields-128.zip`, `named-frameworks-v3-fields-128.zip` | `results/dd_b2_fields/`, `results/dd_b2_fields_v3/` |

The deposited fields are already at the 128 x 128 resolution every script scores at; the loader
recognises them. Then, for example:

```bash
python l5_mapterm_v2.py --ps 8 128 --seeds 42                   # basis and map terms (smooth design)
python dd_screening_frameworks.py coarse                        # coarse solve of every sample (minutes, 5 workers)
python dd_screening_frameworks.py b1                            # screening arms, out of fold (DeepONet: ~20 min per fold)
python dd_screening_frameworks.py b2solve                       # the six named frameworks, production + coarse solves
python dd_screening_frameworks.py b2fit                         # surrogates refit on all materials
python dd_screening_frameworks.py analyse
python dd_seed_robustness.py b2 && python dd_seed_robustness.py b1 && python dd_seed_robustness.py summary
bash run_dd_v3.sh                                               # the whole MOF-like design (PREREG_DD_V3)
bash run_dd_v3a1.sh                                             # amendment A1: own floors, t90, frameworks (two streams)
```

The DeepONet checkpoints of amendment A1 are in the record as `deeponet-checkpoints.zip`;
unzip it to `models/` and `python dd_v3.py deeponet --data v2 --p 16 --seed 42 --from-checkpoint`
(and likewise for any other cell) rescores a cell, own floor included, in minutes instead of
retraining it. `python -m pytest tests` runs the unit tests (the solver for DeepONet's own
floor, the share statistic, the verdict rule and the refusal on missing cells).

Each script writes its results file; compare it with the tracked one. Floating-point reduction
order differs across BLAS builds, so agreement is to about three significant figures, not bit
for bit.

## Tier 2: everything

Generating the smooth design took about 18 worker-hours and the MOF-like design about five hours
on six workers (`gen_parametric_dataset.py --design v2` / `--design v3`, with `ADS_STORE_NZ=256`);
training every arm of the ladder took several CPU days. The scripts are resumable and named by
rung (`run_l1_v2.py`, `run_l2_v2.py`, `run_l5_v2.py`, `run_l6_v2.py`, `run_l7_v2.py`,
`chain_l4b_v3.sh`, which runs `run_l4b_v2.py` with the corrected residual). `autorun.sh`,
`run_dd_v3.sh` and `run_dd_v3a1.sh` are the sequences that were actually run; A1 was
interrupted twice (ledger B90 and a worker-import guard), and `run_dd_v3a1_rest.sh`,
`run_dd_v3a1_b2.sh` and `run_dd_v3a1_final.sh` are the resumptions, which skip finished cells.
