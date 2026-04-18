# Install notes — 9 predictors

Detailed per-tool install notes. Update as each tool is installed.
Each subsection records: URL, version pinned, license, caveats.

## Install order

1. `00_bootstrap_micromamba.sh` → installs micromamba standalone (no sudo).
2. `01_apt_deps.sh` → one-time `sudo apt install` for Boost, GSL, libgd, xml2.
3. `10_viennarna.sh` → creates `nap-thermo` env with ViennaRNA.
4. `30_mxfold2.sh` → creates `nap-hybrid` env with PyTorch CUDA + MXfold2.
5. `20_contrafold.sh`, `21_eternafold.sh`, `22_mcfold.sh` → build C++ tools.
6. `11_nupack4.sh`, `12_rnastructure.sh`, `13_unafold.sh` → require academic registration first.
7. `31_vfold2d.sh` → standalone requires request to Chen Lab; otherwise web fallback.
8. `verify_all.sh` → smoke test.

## Manual registration URLs

| Tool | URL | What to download |
|---|---|---|
| NUPACK 4 | https://github.com/rwollman/NUPACK | auto-cloned by `11_nupack4.sh`; nupack.org is paywalled (academic plan paid). Mirror ships cp36-cp39 manylinux2014 wheels — we use cp39, hence `nap-thermo` is pinned to Python 3.9 |
| RNAstructure | https://rna.urmc.rochester.edu/RNAstructure.html | Already extracted under `tools/RNAstructure/` (user-supplied). Version 6.5 |
| mfold | ftp://rna.urmc.rochester.edu/pub/mfold/ | Already extracted under `tools/mfold-3.6/` (user-supplied). Occupies the slot historically called "UNAFold" in this pipeline |
| VFold2D | http://rna.physics.missouri.edu/vfold2D/ | Already extracted under `tools/VfoldPipeline_standalone/` (user-supplied). Only 2D module built |
| IPknot | https://github.com/satoken/ipknot | Already extracted under `tools/ipknot-master/` (user-supplied). Needs `sudo apt install libglpk-dev` |

## Tool versions (updated 2026-04-18)

| Tool | Version | Date installed | Binary path | Notes |
|---|---|---|---|---|
| ViennaRNA | 2.6.4 | 2026-04-18 | `envs/nap-thermo/bin/RNAfold` | bioconda; Python binding OK. **`nap-thermo` pinned to Python 3.9** to match the NUPACK cp39 wheel |
| NUPACK | 4.0.0.23 (rwollman mirror, 2021 snapshot) | 2026-04-18 | `envs/nap-thermo/lib/python3.9/site-packages/nupack/` | source: `tools/nupack/_source/` (cloned). No 4.0.1.x bugfixes — see project memory |
| RNAstructure | 6.5 (2024-06-14) | 2026-04-18 | `tools/RNAstructure/exe/Fold` + `ct2dot` | built with `make all`; wrapper sets `DATAPATH=tools/RNAstructure/data_tables` |
| mfold | 3.6 (slot formerly "UNAFold") | 2026-04-18 | `tools/mfold-3.6/install/bin/mfold` | autoconf build (gfortran); **nafold has `/usr/local/share/mfold/` hardcoded regardless of `--prefix`**, so the wrapper symlinks `*.dat` from `install/share/mfold/` into the CWD before running |
| CONTRAfold | 2.02 (csfoo-se) | 2026-04-18 | `tools/contrafold/bin/contrafold` | compiled against conda-forge Boost |
| EternaFold | github master | 2026-04-18 | `tools/eternafold/bin/eternafold` | built with `make all`, NOT `make multi` (MPI binary hangs without mpirun) |
| MC-Fold | web only | 2026-04-18 | — | `major-lab/MC-Fold-DP` is a private/non-existent repo. Wrapper POSTs to `https://www.major.iric.ca/cgi-bin/MC-Fold/mcfold.static.cgi` with `pass=lucy` (shared academic password). Parses rank-1 of the Top-50 response. Cached under `tools/mc-fold/cache/`. **Limitation**: enumeration is exponential — fine for ≤30 nt, times out around 50+ nt (e.g. 76 nt tRNA-Phe hits the 300s server cap) |
| MXfold2 | 0.1.2 | 2026-04-18 | `envs/nap-hybrid/bin/mxfold2` | installed from `git+https://github.com/mxfold/mxfold2.git` — the PyPI wheel ships a Python-3.8 `.so` that breaks on 3.10. Torch 1.13.1+cu117 (pinned by mxfold2), CUDA active on RTX 4090 |
| VFold2D | VfoldPipeline_standalone-v2 | 2026-04-18 | `tools/VfoldPipeline_standalone/Vfold2D/bin/vfold2D_cl.out` | Only the 2D module built (skipped 3D/LAMMPS/QRNAS). Wrapper exports `VfoldPipeline` env var and uses `-fast` mode |
| IPknot | 1.1.0 | 2026-04-18 | `tools/ipknot-master/build/ipknot` | CMake build; system deps `libglpk-dev` + `pkg-config`; links against ViennaRNA from `nap-thermo` (wrapper sets `LD_LIBRARY_PATH`). **Only predictor that emits pseudoknots** |

## Known gotchas

- **CONTRAfold + modern g++**: Older source may hit `-std=c++14` warnings. The csfoo fork patches this.
- **RNAstructure `DATAPATH`**: must be exported before running `Fold`. The Python wrapper sets it automatically.
- **MXfold2 CUDA arch**: if `torch.cuda.is_available()` is False after install, check `nvidia-smi` against the conda-forge pytorch-cuda version.
- **mfold-3.6 data path**: `./configure --prefix=` is NOT threaded into the Fortran `nafold` binary, which has `/usr/local/share/mfold/` hardcoded. Fallback is CWD, so the wrapper symlinks `*.dat` from `install/share/mfold/` into each run's tempdir. Don't delete those files.
- **MC-Fold web service**: respects a 5 s cooldown; expect slow batch jobs. Cache file reads must use `errors="replace"` (server emits `©` as latin-1 `0xa9`).
- **Non-UTF8 subprocess output**: `base._run` now decodes with `errors="replace"`. Needed for mfold (°) and MC-Fold (©) which emit non-UTF-8 glyphs.
- **VfoldPipeline 3D parts skipped**: The full `Install.sh` wants mpich + QRNAS + LAMMPS-3Mar20 (~5 min build). Skip it; our pipeline only needs `Vfold2D/src/make`. Vfold2D requires the env var `VfoldPipeline=<standalone root>` or the binary aborts.
- **IPknot ViennaRNA linkage**: `pkg_check_modules(VIENNARNA RNAlib2)` needs `PKG_CONFIG_PATH` pointing at nap-thermo's `lib/pkgconfig/`, and at runtime `LD_LIBRARY_PATH` must include `nap-thermo/lib/`.
