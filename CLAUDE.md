# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Pipeline para predecir la **estructura secundaria (2D)** de aptámeros de ADN/ARN a partir de la secuencia. El repo integra y compara múltiples predictores; la instalación de cada paquete se hace de forma incremental.

Predictores a integrar:

- **Statistical learning**: EternaFold, CONTRAfold, MC-Fold
- **Thermodynamics-based**: ViennaRNA, RNAstructure, NUPACK (v3.2+), UNAFold
- **Hybrid**: MXfold2, VFold2D

Lenguaje del pipeline: **Python** (con shell auxiliar cuando haga falta invocar binarios externos).

## Repository layout

- [scripts/](scripts/) — código del pipeline (wrappers por predictor, orquestación, parsers de salida).
- [inputs/](inputs/) — secuencias de entrada, estructuras de referencia, parámetros, datos que consumen los predictores.
- [results/](results/) — salidas de cada predictor + comparaciones. No versionar outputs grandes.
- [papers/](papers/) — literatura de referencia (PDFs) sobre cada predictor y benchmarks.
- [docs/](docs/) — notas de instalación por herramienta, decisiones de diseño, protocolos.

El repo está vacío salvo por esas carpetas — no hay aún código, README, ni sistema de build. A medida que se vayan instalando herramientas, documentar en `docs/install-<herramienta>.md` (ruta de binarios, versión, flags no-obvios, licencia si aplica).

## Working-directory notes

- Existe un directorio hermano [../aptameritos.Chik/](../aptameritos.Chik/) de un proyecto previo de aptámeros — puede contener secuencias o estructuras reutilizables como referencia/benchmark.
- El agente tiene acceso adicional a `/home/gdarosa/mini-mini/inputs/` (input decks de CURVES/CANION/cpptraj) — material de análisis 3D, probablemente **no** relevante para la parte 2D de este pipeline salvo validación posterior.

## Licensing caveats al integrar predictores

Varios de los paquetes listados tienen licencias no-libres o registro obligatorio (RNAstructure, UNAFold académico, NUPACK). Antes de distribuir binarios o scripts que los empaqueten, verificar los términos de cada licencia.

## Documentación: README bilingüe

- [README.md](README.md) es la versión canónica en **inglés**.
- [README_ES.md](README_ES.md) es el espejo en **español**.
- Ambos deben actualizarse **en el mismo commit** cuando cambie cualquiera de los dos — nunca dejar uno desincronizado.
- Otros archivos `.md` (`docs/*.md`, etc.) van solo en inglés. Este CLAUDE.md queda en español.
