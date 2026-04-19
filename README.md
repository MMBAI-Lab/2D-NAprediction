# 2D-NAprediction

> [Leer en español](README_ES.md)

Pipeline to compare predictors of **DNA/RNA aptamer secondary (2D) structure** from sequence. Wraps 10 tools behind a common Python interface and produces a CSV with predictions from each one against an input FASTA.

## Context

This project covers the **1D → 2D** step of the framework proposed in da Rosa, Dans et al. *WIREs Comp. Mol. Sci.* 2025 ("Aptamers Meet Structural Bioinformatics, Computational Chemistry, and Artificial Intelligence"): starting from sequences selected via SELEX/NGS, predict the 2D fold as input for downstream 3D modeling. Aptamers — 20–100 nt ssDNA/ssRNA — derive their binding affinity from their 3D shape, and that shape is built on the 2D scaffold of stems, loops, and junctions.

The four references in [papers/](papers/) frame the project:

- **da Rosa & Dans (WIREs 2025)** — the group's own review; establishes the 1D→2D→3D→4D+AI pipeline this repo plugs into.
- **Wayment-Steele, ..., Das (Nature Methods 2022)** — definitive benchmark of 2D packages against Eterna SHAPE data. Defines the rankings we use as reference (see *Das 2022 ranking*).
- **Kaushik et al. (2016)** — catalog of non-canonical DNA structures (G-quadruplex, i-motif, triplex, etc.). **Caveat**: the predictors in this repo assume Watson–Crick base pairing; for DNA aptamers with G4/i-motif character, dedicated tools (QGRS Mapper, G4Hunter) are required and not included here.
- **Opisna (2023)** — introductory Spanish-language text on aptamers and SELEX.

## Repository layout

| Folder | Contents |
|---|---|
| [scripts/predictors/](scripts/predictors/) | Python wrappers, one per predictor, all deriving from `Predictor` in [base.py](scripts/predictors/base.py) |
| [scripts/install/](scripts/install/) | Numbered install scripts (`00_` bootstrap → `31_` last predictor) |
| [scripts/run_all.py](scripts/run_all.py) | Orchestrator: FASTA in → `predictions.csv` out |
| [scripts/config.py](scripts/config.py) | Paths and env names |
| [envs/](envs/) | Micromamba env specs (`nap-thermo`, `nap-hybrid`, `nap-learning`) |
| [tools/](tools/) | Compiled binaries and sources for each predictor (not versioned) |
| [inputs/](inputs/) | Input sequences. Includes [smoke.fa](inputs/smoke.fa) (mini hairpin + tRNA-Phe) |
| [results/](results/) | Outputs — do not version large files |
| [papers/](papers/) | Reference PDFs |
| [docs/install-notes.md](docs/install-notes.md) | Detailed per-tool install notes |

## Installed predictors

All 10 are operational (verified in [results/smoke/rna/predictions.csv](results/smoke/rna/predictions.csv) on mini hairpin and yeast tRNA-Phe; DNA runs under [results/smoke/dna_as_rna/](results/smoke/dna_as_rna/) and [results/smoke/dna_native/](results/smoke/dna_native/)).

| Predictor | Version | Category | Key notes |
|---|---|---|---|
| ViennaRNA | 2.6.4 | Thermodynamic | `nap-thermo`; default 37°C (see *60°C*) |
| NUPACK | 4.0.0.23 | Thermodynamic | From the `rwollman/NUPACK` mirror (nupack.org is now paywalled). Python 3.9 required by the wheel |
| RNAstructure | 6.5 | Thermodynamic | Default 37°C (see *60°C*) |
| mfold | 3.6 | Thermodynamic | Zuker; occupies the slot originally intended for UNAFold. `nafold` has `/usr/local/share/mfold/` hardcoded, so the wrapper symlinks `.dat` files into the tempdir at each run |
| CONTRAfold | 2.02 (csfoo fork) | Statistical learning | **Top-ranked in Das 2022** (z-score 1.09) |
| EternaFold | master | Statistical learning (multitask) | Developed in Das 2022 on top of CONTRAfold. Trained on SHAPE + riboswitch data |
| MC-Fold | web-only | Statistical learning | Via CGI at `major.iric.ca` with `pass=lucy`. Exponential enumeration — times out above ~50 nt |
| MXfold2 | 0.1.2 | Hybrid (DL + thermo) | `nap-hybrid` with CUDA |
| VFold2D | standalone-v2 | Thermodynamic | Only the 2D module was built; the full 3D pipeline (LAMMPS + QRNAS) was skipped |
| IPknot | 1.1.0 | Integer programming | **Only predictor that handles pseudoknots** (emits `[]`, `{}`). Uses LinearPartition-CONTRAfold by default |

Full details (paths, flags, caveats) in [docs/install-notes.md](docs/install-notes.md).

## Das 2022 ranking (EternaBench)

Wayment-Steele et al. evaluate packages on two tasks that are sensitive to the structural **ensemble**, not just the MFE:

1. **Chemical mapping**: predict per-base P(unpaired) vs. experimental SHAPE. Dataset: EternaBench-ChemMapping, n = 12,711.
2. **Riboswitch affinity**: predict K_MS2 with/without ligand. Dataset: EternaBench-Switch, n = 7,228.

**Ranking averaged across both tasks** (higher z-score = better):

| Rank | Package | z-score |
|---|---|---|
| 1 | CONTRAfold 2 | **1.09** |
| 2 | Vienna 2, **60°C** | 0.89 |
| 3 | RNAsoft BL (no dangles) | 0.84 |
| 4 | RNAstructure, **60°C** | 0.78 |
| 5 | RNAsoft BLstar | 0.67 |
| … | | |
| — | ViennaRNA 2 (default 37°C) | 0.05 |
| — | RNAstructure (default 37°C) | −0.06 |
| — | NUPACK 1999, 60°C | **−1.42** |

Key takeaways:

- Statistical-learning packages (CONTRAfold, RNAsoft) outperform pure thermodynamic packages on ensemble-sensitive tasks.
- **EternaFold**, introduced in the same paper, retrains CONTRAfold in a multitask setting with chemical-mapping and riboswitch data; it generalizes better to external RNAs (viral genomes, in-cell mRNAs) — average z-score 1.21 across 31 external datasets (Table 2 of the paper).

### The 60°C recommendation — why, and for whom

**Central finding (Das 2022, p. 1235, col. 2):**

> *"Increasing the temperature from the default value of 37°C used in these packages to 60°C improved the correlation to experimental data for ViennaRNA (R=0.708(2)) and RNAstructure (R=0.707(2)), but not NUPACK (R=0.639(2))."*

**Rationale** (Discussion, p. 1240): the thermodynamic parameters of these packages were measured under specific ionic conditions that do not match typical experimental settings (EternaBench SHAPE was run at 24°C in 10 mM MgCl₂ + 50 mM Na-HEPES, pH 8.0). Raising the modeling temperature to 60°C "melts" over-stable predictions and moves the predicted ensemble closer to what is observed experimentally.

**Applies to:**

- ViennaRNA (`RNAfold -T 60`)
- RNAstructure (`Fold --temperature 333.15` in Kelvin, or the equivalent env var)
- **Not NUPACK** — its ranking *worsens* at 60°C (ends up at the bottom of the table). Keep NUPACK at 37°C.

**Does not apply** to CONTRAfold, EternaFold, or MXfold2 — their scores are not parameterized by physical temperature.

**Current repo status**: the [vienna.py](scripts/predictors/vienna.py) and [rnastructure.py](scripts/predictors/rnastructure.py) wrappers run at **default 37°C** — the 60°C variant is not implemented yet. See *Pending* below.

## Usage

### Environment setup

Dependencies live in isolated micromamba envs under `tools/envs/`. Initial bootstrap:

```bash
source .envrc                    # exports MAMBA_ROOT_PREFIX, MAMBA_EXE
bash scripts/install/00_bootstrap_micromamba.sh
sudo bash scripts/install/01_apt_deps.sh     # boost, gsl, libgd, xml2, libglpk-dev
bash scripts/install/10_viennarna.sh          # creates nap-thermo (Python 3.9)
bash scripts/install/11_nupack4.sh            # mirror clone + wheel install
bash scripts/install/12_rnastructure.sh
bash scripts/install/13_mfold.sh
bash scripts/install/20_contrafold.sh
bash scripts/install/21_eternafold.sh
bash scripts/install/22_mcfold.sh             # no-op (web-only)
bash scripts/install/23_ipknot.sh
bash scripts/install/30_mxfold2.sh            # creates nap-hybrid (+ CUDA)
bash scripts/install/31_vfold2d.sh
bash scripts/install/40_fornac.sh             # fornac visualizer (no build needed)
bash scripts/install/verify_all.sh
```

### Running the pipeline

```bash
source .envrc
micromamba run -n nap-thermo python scripts/run_all.py <input.fa> <outdir>
```

Example (smoke):

```bash
micromamba run -n nap-thermo python scripts/run_all.py inputs/smoke.fa results/smoke/rna
```

Useful flags:

- `--only ViennaRNA NUPACK4 RNAstructure` — restrict to a subset of predictors.
- `--na DNA` — switch to native DNA mode (uses each predictor's DNA thermodynamic parameters; MC-Fold, IPknot, and VFold2D are RNA-only and will error).
- `--dna-as-rna` — for DNA aptamers, transcribe T→U internally and submit every sequence as RNA, so that RNA-only predictors (MC-Fold, IPknot, VFold2D) can also run. The CSV records `na_type=DNA` (the parent), while stdout annotates each run with `[DNA->RNA]`. **Caveat**: bypasses native DNA thermo parameters — treat the prediction as an RNA-proxy model of the DNA fold.

The output `<outdir>/predictions.csv` has columns: `seq_id, tool, na_type, dot_bracket, mfe_kcal_mol, runtime_s, error`.

### Visualizing predictions

Every `run_all.py` invocation produces both `predictions.csv` and `structures.html` in the output directory. The HTML is a single self-contained page that renders every `(seq_id, tool)` prediction with a dot-bracket as a card in a grid, using [fornac](https://github.com/ViennaRNA/fornac) — force-directed layout, same as the public http://rna.tbi.univie.ac.at/forna/ frontend. `fornac.js` + `d3.v3.min.js` + `fornac.css` load from `tools/fornac/dist/` via a relative path, so the page works offline once the fornac bundle is installed.

The visualizer transcribes T→U internally so DNA inputs render correctly, and pseudoknot characters (`[]`, `{}`) are supported.

To skip the HTML step, pass `--no-visualize`:

```bash
micromamba run -n nap-thermo python scripts/run_all.py <input.fa> <outdir> --no-visualize
```

To render an HTML for an existing CSV (e.g. one produced before auto-visualize was wired in), call the visualizer directly:

```bash
micromamba run -n nap-thermo python scripts/visualize.py \
    results/APT-PF1/dna_as_rna/predictions.csv \
    --fasta /path/to/input.fa
```

Pass `-o path/to/custom.html` to write elsewhere than `<csv_dir>/structures.html`.

### DNA aptamer workflow

```bash
source .envrc
micromamba run -n nap-thermo python scripts/run_all.py \
    inputs/my_dna_aptamers.fa results/run1 --dna-as-rna
```

This runs all 10 predictors on T→U-transcribed sequences and reports the resulting dot-brackets tagged as DNA in the CSV.

### DNA support by tool

The 10 predictors fall into three tiers depending on how they handle DNA input.

**Native DNA (4)** — the wrapper forwards DNA thermodynamic parameters to the binary:

| Tool | How |
|---|---|
| ViennaRNA | `--paramFile=DNA` (Turner DNA parameters) ([vienna.py:27](scripts/predictors/vienna.py#L27)) |
| NUPACK | `material="dna"` (NUPACK 4 native DNA model) ([nupack.py:19](scripts/predictors/nupack.py#L19)) |
| RNAstructure | `--DNA` flag ([rnastructure.py:38](scripts/predictors/rnastructure.py#L38)) |
| mfold | `NA=DNA` (reads `.37` parameter files for DNA) ([mfold.py:93](scripts/predictors/mfold.py#L93)) |

**RNA-only — reject DNA (3)** — the wrapper explicitly returns an error when `na_type=DNA`:

| Tool | Error message |
|---|---|
| MC-Fold | `"MC-Fold is RNA-only"` |
| VFold2D | `"Vfold2D is RNA-only"` |
| IPknot | `"IPknot is RNA-only"` |

**Auto-transcribe DNA to RNA (3)** — these are RNA-trained and the wrappers unconditionally substitute T→U before submission, so the model never sees raw T characters. The `Prediction` object still carries the caller's `na_type` for CSV traceability:

| Tool | Rationale |
|---|---|
| CONTRAfold | Trained on (A, U, G, C); unknown bases would produce undefined scores. |
| EternaFold | Built on CONTRAfold — same parameter alphabet. |
| MXfold2 | Neural network trained on RNA; same constraint. |

**Practical recommendation:**

- For authentic DNA thermodynamics, use `--na DNA` combined with `--only ViennaRNA NUPACK4 RNAstructure mfold` to restrict to the native-4.
- For uniform coverage across all 10 tools on a DNA aptamer (at the cost of RNA-proxy accuracy in the RNA-trained tools), use `--dna-as-rna`: every sequence is transcribed T→U and submitted as RNA, the CSV labels them as DNA for traceability, and every predictor — including the RNA-only ones — produces a result.
- Calling `--na DNA` without `--only` is safe in the sense that CONTRAfold, EternaFold, and MXfold2 internally transcribe the input before scoring — but remember that those three are still RNA-proxy models of the DNA fold, not native DNA thermodynamics.

## Pending

- [ ] **60°C variants** of ViennaRNA and RNAstructure (Das 2022). Add a `temperature_c` parameter to `.predict()` or a second slot (`ViennaRNA_60C`) in [run_all.py](scripts/run_all.py).
- [ ] **Metrics against reference structures**: the pipeline currently only collects predictions; a scorer (base-pair F1, MCC) against known structures is missing.
- [ ] **G4/i-motif handling for DNA aptamers**: none of the 10 tools recognize these — they are Watson–Crick only. Kaushik 2016 documents the catalog; for screening, QGRS Mapper / G4Hunter would need to run upstream of the 2D step.
- [ ] **NUPACK** is pinned to 4.0.0.23 (the 2021 rwollman mirror snapshot) as long as nupack.org remains paywalled; no 4.0.1.x bugfixes.

## Licensing

Several tools ship under non-free or academic-only licenses:

| Tool | License | Caveat |
|---|---|---|
| NUPACK | Caltech academic (non-commercial) | Redistribution permitted, no commercial use |
| mfold | Academic (Zuker / RPI) | — |
| RNAstructure | GPL v2 | Free |
| UNAFold | Academic (non-free) | Not installed — replaced by mfold |
| VFold2D | Academic (Chen Lab) | — |
| ViennaRNA, MXfold2, CONTRAfold, EternaFold, IPknot | Open-source (mixed GPL/BSD/MIT) | — |

Before redistributing binaries or scripts that wrap these tools, verify each license.

## References

1. **Wayment-Steele, H.K., ..., Das, R.** (2022). *RNA secondary structure packages evaluated and improved by high-throughput experiments*. Nature Methods 19, 1234–1242. DOI: 10.1038/s41592-022-01605-0.
2. **da Rosa, G., de Castro, M., ..., Dans, P.D.** (2025). *Aptamers Meet Structural Bioinformatics, Computational Chemistry, and Artificial Intelligence*. WIREs Comp. Mol. Sci. 15:e70050.
3. **Kaushik, M. et al.** (2016). *A bouquet of DNA structures: Emerging diversity*. Biochem. Biophys. Rep. 5, 388–395.
4. **Opisna, J.** (2023). *Aptámeros: los nuevos anticuerpos*.

Per-tool references in [docs/install-notes.md](docs/install-notes.md).
