# 2D-NAprediction

> [Read in English](README.md)

Pipeline para comparar predictores de **estructura secundaria (2D) de aptámeros de ADN/ARN** a partir de la secuencia. Encapsula 10 herramientas bajo una interfaz Python común y produce un CSV con las predicciones de cada una contra un FASTA de entrada.

## Contexto

El proyecto cubre el paso **1D → 2D** del marco propuesto en da Rosa, Dans et al. *WIREs Comp. Mol. Sci.* 2025 ("Aptamers Meet Structural Bioinformatics, Computational Chemistry, and Artificial Intelligence"): a partir de secuencias seleccionadas por SELEX/NGS, predecir el fold 2D como insumo para el modelado 3D posterior. Los aptámeros — ssDNA/ssRNA de 20-100 nt — derivan su afinidad de la forma 3D, y esa forma se construye sobre el andamio 2D de stems, loops y junctions.

Las cuatro referencias en [papers/](papers/) enmarcan el proyecto:

- **da Rosa & Dans (WIREs 2025)** — review propia del grupo; establece el pipeline 1D→2D→3D→4D+AI en el que se inserta este repo.
- **Wayment-Steele, ..., Das (Nature Methods 2022)** — benchmark definitivo de los packages 2D contra datos SHAPE de Eterna. Define los rankings que usamos como referencia (ver *Ranking de Das 2022*).
- **Kaushik et al. (2016)** — catálogo de estructuras no canónicas de ADN (G-quadruplex, i-motif, triplex, etc.). **Caveat**: los predictores del repo asumen apareamiento Watson–Crick; para aptámeros ADN con carácter G4/i-motif hay que usar herramientas específicas (QGRS Mapper, G4Hunter), no incluidas.
- **Opisna (2023)** — texto introductorio en español sobre aptámeros y SELEX.

## Layout del repo

| Carpeta | Contenido |
|---|---|
| [scripts/predictors/](scripts/predictors/) | Wrappers Python por predictor, todos derivan de `Predictor` en [base.py](scripts/predictors/base.py) |
| [scripts/install/](scripts/install/) | Scripts de instalación numerados (`00_` bootstrap → `31_` último predictor) |
| [scripts/run_all.py](scripts/run_all.py) | Orquestador: FASTA in → `predictions.csv` out |
| [scripts/config.py](scripts/config.py) | Paths y nombres de envs |
| [envs/](envs/) | Specs de los micromamba envs (`nap-thermo`, `nap-hybrid`, `nap-learning`) |
| [tools/](tools/) | Binarios y sources compilados de cada predictor (no versionado) |
| [resources/](resources/) | Secuencias de entrada. Incluye [smoke.fa](resources/smoke.fa) (mini hairpin + tRNA-Phe) |
| [results/](results/) | Outputs — no versionar archivos grandes |
| [papers/](papers/) | PDFs de referencia |
| [docs/install-notes.md](docs/install-notes.md) | Notas detalladas de instalación por herramienta |

## Predictores instalados

Los 10 están operativos (verificados en [results/smoke/rna/predictions.csv](results/smoke/rna/predictions.csv) sobre mini hairpin y tRNA-Phe de levadura; corridas de ADN bajo [results/smoke/dna_as_rna/](results/smoke/dna_as_rna/) y [results/smoke/dna_native/](results/smoke/dna_native/)).

| Predictor | Versión | Categoría | Notas clave |
|---|---|---|---|
| ViennaRNA | 2.6.4 | Termodinámico | `nap-thermo`; default 37°C (ver *60°C*) |
| NUPACK | 4.0.0.23 | Termodinámico | Desde el mirror `rwollman/NUPACK` (nupack.org ahora es de pago). Python 3.9 obligado por el wheel |
| RNAstructure | 6.5 | Termodinámico | Default 37°C (ver *60°C*) |
| mfold | 3.6 | Termodinámico | Zuker; ocupa el slot que originalmente iba a ser UNAFold. `nafold` tiene `/usr/local/share/mfold/` hardcodeado, por lo que el wrapper symlinkea los `.dat` al tempdir en cada corrida |
| CONTRAfold | 2.02 (csfoo fork) | Statistical learning | **Mejor ranking en Das 2022** (z-score 1.09) |
| EternaFold | master | Statistical learning (multitask) | Desarrollado en Das 2022 sobre CONTRAfold. Entrenado con datos SHAPE + riboswitch |
| MC-Fold | solo web | Statistical learning | Vía CGI en `major.iric.ca` con `pass=lucy`. Enumeración exponencial — timeout por encima de ~50 nt |
| MXfold2 | 0.1.2 | Híbrido (DL + termodinámico) | `nap-hybrid` con CUDA |
| VFold2D | standalone-v2 | Termodinámico | Solo se compiló el módulo 2D; se salteó el pipeline 3D completo (LAMMPS + QRNAS) |
| IPknot | 1.1.0 | Integer programming | **Único predictor que maneja pseudonudos** (emite `[]`, `{}`). Usa LinearPartition-CONTRAfold por default |

Detalle completo (paths, flags, caveats) en [docs/install-notes.md](docs/install-notes.md).

## Ranking de Das 2022 (EternaBench)

Wayment-Steele et al. evalúan los packages en dos tareas sensibles al **ensamble** de estructuras, no solo a la MFE:

1. **Chemical mapping**: predecir P(unpaired) por base vs. SHAPE experimental. Dataset: EternaBench-ChemMapping, n = 12,711.
2. **Riboswitch affinity**: predecir K_MS2 con/sin ligando. Dataset: EternaBench-Switch, n = 7,228.

**Ranking promediado sobre ambas tareas** (z-score alto = mejor):

| Puesto | Package | z-score |
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

Lecturas clave:

- Los packages *statistical learning* (CONTRAfold, RNAsoft) superan a los termodinámicos puros en tareas ensamble-dependientes.
- **EternaFold**, introducido en el mismo paper, reentrena CONTRAfold en multitask con datos de chemical mapping y riboswitches; generaliza mejor a RNAs externos (genomas virales, mRNAs en célula) — z-score promedio 1.21 en 31 datasets externos (Table 2 del paper).

### La recomendación de 60°C — por qué y para quién

**Hallazgo central (Das 2022, pág. 1235, col. 2):**

> *"Increasing the temperature from the default value of 37°C used in these packages to 60°C improved the correlation to experimental data for ViennaRNA (R=0.708(2)) and RNAstructure (R=0.707(2)), but not NUPACK (R=0.639(2))."*

**Racional** (Discussion, pág. 1240): los parámetros termodinámicos de estos packages fueron medidos en condiciones iónicas específicas que no coinciden con las experimentales típicas (el SHAPE de EternaBench se hizo a 24°C en 10 mM MgCl₂ + 50 mM Na-HEPES, pH 8.0). Subir la temperatura de modelado a 60°C "derrite" predicciones sobrestables y acerca el ensamble predicho al observado experimentalmente.

**Aplica a:**

- ViennaRNA (`RNAfold -T 60`)
- RNAstructure (`Fold --temperature 333.15` en Kelvin, o la env var equivalente)
- **No a NUPACK** — su ranking *empeora* a 60°C (queda al fondo de la tabla). Dejar NUPACK en 37°C.

**No aplica** a CONTRAfold, EternaFold ni MXfold2 — sus scores no están parametrizados por temperatura física.

**Estado actual del repo**: los wrappers [vienna.py](scripts/predictors/vienna.py) y [rnastructure.py](scripts/predictors/rnastructure.py) corren a **37°C por default** — la variante 60°C todavía no está implementada. Ver *Pendientes*.

## Uso

### Preparación del entorno

Las dependencias viven en micromamba envs aislados bajo `tools/envs/`. Bootstrap inicial:

```bash
source .envrc                    # exporta MAMBA_ROOT_PREFIX, MAMBA_EXE
bash scripts/install/00_bootstrap_micromamba.sh
sudo bash scripts/install/01_apt_deps.sh     # boost, gsl, libgd, xml2, libglpk-dev
bash scripts/install/10_viennarna.sh          # crea nap-thermo (Python 3.9)
bash scripts/install/11_nupack4.sh            # clone del mirror + install del wheel
bash scripts/install/12_rnastructure.sh
bash scripts/install/13_mfold.sh
bash scripts/install/20_contrafold.sh
bash scripts/install/21_eternafold.sh
bash scripts/install/22_mcfold.sh             # no-op (solo web)
bash scripts/install/23_ipknot.sh
bash scripts/install/30_mxfold2.sh            # crea nap-hybrid (+ CUDA)
bash scripts/install/31_vfold2d.sh
bash scripts/install/verify_all.sh
```

### Correr el pipeline

```bash
source .envrc
micromamba run -n nap-thermo python scripts/run_all.py <input.fa> <outdir>
```

Ejemplo (smoke):

```bash
micromamba run -n nap-thermo python scripts/run_all.py resources/smoke.fa results/smoke/rna
```

Flags útiles:

- `--only ViennaRNA NUPACK4 RNAstructure` — restringir a un subset de predictores.
- `--na DNA` — modo ADN nativo (usa los parámetros termodinámicos de ADN de cada predictor; MC-Fold, IPknot y VFold2D son RNA-only y van a errorar).
- `--dna-as-rna` — para aptámeros de ADN, transcribe T→U internamente y somete toda secuencia como ARN, de modo que los predictores RNA-only (MC-Fold, IPknot, VFold2D) también corren. El CSV registra `na_type=DNA` (el parent), mientras que stdout anota cada corrida con `[DNA->RNA]`. **Caveat**: bypasea los parámetros termodinámicos nativos de ADN — tratar la predicción como un modelo RNA-proxy del fold de ADN.

La salida `<outdir>/predictions.csv` tiene columnas: `seq_id, tool, na_type, dot_bracket, mfe_kcal_mol, runtime_s, error`.

### Workflow para aptámeros de ADN

```bash
source .envrc
micromamba run -n nap-thermo python scripts/run_all.py \
    resources/my_dna_aptamers.fa results/run1 --dna-as-rna
```

Corre los 10 predictores sobre secuencias T→U-transcriptas y reporta los dot-brackets resultantes etiquetados como DNA en el CSV.

### Soporte de ADN por herramienta

Los 10 predictores caen en tres niveles según cómo manejan input de ADN.

**ADN nativo (4)** — el wrapper pasa parámetros termodinámicos de ADN al binario:

| Tool | Cómo |
|---|---|
| ViennaRNA | `--paramFile=DNA` (parámetros Turner-DNA) ([vienna.py:27](scripts/predictors/vienna.py#L27)) |
| NUPACK | `material="dna"` (modelo ADN nativo en NUPACK 4) ([nupack.py:19](scripts/predictors/nupack.py#L19)) |
| RNAstructure | flag `--DNA` ([rnastructure.py:38](scripts/predictors/rnastructure.py#L38)) |
| mfold | `NA=DNA` (lee archivos `.37` con parámetros de ADN) ([mfold.py:93](scripts/predictors/mfold.py#L93)) |

**RNA-only — rechazan ADN (3)** — el wrapper devuelve error explícito cuando `na_type=DNA`:

| Tool | Mensaje de error |
|---|---|
| MC-Fold | `"MC-Fold is RNA-only"` |
| VFold2D | `"Vfold2D is RNA-only"` |
| IPknot | `"IPknot is RNA-only"` |

**Auto-transcriben ADN a ARN (3)** — están entrenados en ARN y los wrappers sustituyen T→U incondicionalmente antes de someter la secuencia, de modo que el modelo nunca ve T crudos. El objeto `Prediction` conserva el `na_type` del caller para trazabilidad en el CSV:

| Tool | Racional |
|---|---|
| CONTRAfold | Entrenado con (A, U, G, C); bases desconocidas producirían scores indefinidos. |
| EternaFold | Construido sobre CONTRAfold — mismo alfabeto de parámetros. |
| MXfold2 | Red neuronal entrenada en ARN; misma restricción. |

**Recomendación práctica:**

- Para termodinámica auténtica de ADN, usar `--na DNA` combinado con `--only ViennaRNA NUPACK4 RNAstructure mfold` para restringir a los native-4.
- Para cobertura uniforme de las 10 herramientas sobre un aptámero de ADN (al costo de accuracy RNA-proxy en las RNA-trained), usar `--dna-as-rna`: cada secuencia se transcribe T→U y se somete como ARN, el CSV las etiqueta como DNA para trazabilidad, y cada predictor — incluidos los RNA-only — produce resultado.
- Llamar `--na DNA` sin `--only` es seguro en el sentido de que CONTRAfold, EternaFold y MXfold2 transcriben internamente el input antes de scorear — pero recordá que esos tres siguen siendo modelos RNA-proxy del fold de ADN, no termodinámica nativa.

## Pendientes

- [ ] **Variantes a 60°C** de ViennaRNA y RNAstructure (Das 2022). Agregar parámetro `temperature_c` a `.predict()` o un segundo slot (`ViennaRNA_60C`) en [run_all.py](scripts/run_all.py).
- [ ] **Métricas vs. estructuras de referencia**: el pipeline hoy solo recolecta predicciones; falta un scorer (base-pair F1, MCC) contra estructuras conocidas.
- [ ] **Manejo de G4/i-motif para aptámeros de ADN**: ninguna de las 10 herramientas los reconoce — son Watson–Crick puro. Kaushik 2016 documenta el catálogo; para screening habría que correr QGRS Mapper / G4Hunter upstream del paso 2D.
- [ ] **NUPACK** queda pineado a 4.0.0.23 (el snapshot del mirror rwollman de 2021) mientras nupack.org siga siendo de pago; sin bugfixes 4.0.1.x.

## Licencias

Varias herramientas vienen bajo licencias no-libres o de uso académico:

| Tool | Licencia | Caveat |
|---|---|---|
| NUPACK | Caltech académica (no comercial) | Redistribución permitida, no uso comercial |
| mfold | Académica (Zuker / RPI) | — |
| RNAstructure | GPL v2 | Libre |
| UNAFold | Académica (no-libre) | No instalada — reemplazada por mfold |
| VFold2D | Académica (Chen Lab) | — |
| ViennaRNA, MXfold2, CONTRAfold, EternaFold, IPknot | Open-source (mix GPL/BSD/MIT) | — |

Antes de redistribuir binarios o scripts que envuelvan estas herramientas, verificar cada licencia.

## Referencias

1. **Wayment-Steele, H.K., ..., Das, R.** (2022). *RNA secondary structure packages evaluated and improved by high-throughput experiments*. Nature Methods 19, 1234–1242. DOI: 10.1038/s41592-022-01605-0.
2. **da Rosa, G., de Castro, M., ..., Dans, P.D.** (2025). *Aptamers Meet Structural Bioinformatics, Computational Chemistry, and Artificial Intelligence*. WIREs Comp. Mol. Sci. 15:e70050.
3. **Kaushik, M. et al.** (2016). *A bouquet of DNA structures: Emerging diversity*. Biochem. Biophys. Rep. 5, 388–395.
4. **Opisna, J.** (2023). *Aptámeros: los nuevos anticuerpos*.

Referencias por herramienta en [docs/install-notes.md](docs/install-notes.md).
