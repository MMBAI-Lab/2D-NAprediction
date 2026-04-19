from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
RESULTS = REPO_ROOT / "results"

MICROMAMBA = TOOLS / "micromamba" / "bin" / "micromamba"
MAMBA_ROOT = TOOLS / "envs"

ENV_THERMO = "nap-thermo"
ENV_LEARNING = "nap-learning"
ENV_HYBRID = "nap-hybrid"

CONTRAFOLD_BIN = TOOLS / "contrafold" / "bin" / "contrafold"
ETERNAFOLD_BIN = TOOLS / "eternafold" / "bin" / "eternafold"
ETERNAFOLD_PARAMS = TOOLS / "eternafold" / "parameters" / "EternaFoldParams.v1"
MCFOLD_BIN = TOOLS / "mc-fold" / "bin" / "mcfold-dp"

RNASTRUCTURE_DIR = TOOLS / "RNAstructure"
RNASTRUCTURE_BIN = RNASTRUCTURE_DIR / "exe" / "Fold"
RNASTRUCTURE_DATAPATH = RNASTRUCTURE_DIR / "data_tables"

# mfold-3.6 (Zuker) installs into $PREFIX/bin/mfold (script that calls Fortran)
# and $PREFIX/share/mfold/ for energy data tables. Slot historically called
# "UNAFold" in this pipeline; kept naming for back-compat in run_all.
MFOLD_DIR = TOOLS / "mfold-3.6"
MFOLD_PREFIX = MFOLD_DIR / "install"
MFOLD_BIN = MFOLD_PREFIX / "bin" / "mfold"
MFOLD_DATA = MFOLD_PREFIX / "share" / "mfold"

VFOLD2D_DIR = TOOLS / "VfoldPipeline_standalone" / "Vfold2D"
VFOLD2D_WEB = "http://rna.physics.missouri.edu/vfold2D"

IPKNOT_BIN = TOOLS / "ipknot-master" / "build" / "ipknot"

FORNAC_DIR = TOOLS / "fornac"
FORNAC_JS = FORNAC_DIR / "dist" / "fornac.js"
FORNAC_CSS = FORNAC_DIR / "dist" / "fornac.css"
FORNAC_D3 = FORNAC_DIR / "dist" / "d3.v3.min.js"

MCFOLD_WEB = "https://www.major.iric.ca/cgi-bin/MC-Fold/mcfold.static.cgi"
MCFOLD_WEB_PASS = "lucy"
