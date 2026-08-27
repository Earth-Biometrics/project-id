# Earth Biometrics — Biodiversity Monitoring

This repository is the starting point for a biodiversity monitoring system designed and validated in California, then adapted for deployment in Uganda (starting with Bwindi Impenetrable Forest).

## Project mission

Build a field-ready wildlife recognition pipeline for heavily wooded, low-light environments where visible-only images are often partial, occluded, or motion blurred.

The current architecture follows a two-stage approach:

1. **Stage 1 (Detection):** [MegaDetector](https://github.com/agentmorris/MegaDetector) for animal candidate detection and blank-frame filtering.
2. **Stage 2 (Classification):** [BioCLIP-2](https://github.com/Imageomics/bioclip-2) for species classification.
3. **Fusion direction:** align RGB + IR data and evolve toward a 4-channel fusion flow (RGB+IR) as the project matures.

## Syllabus alignment

This setup is based on the syllabus in [Project_Plan_Syllabus_2026_August.ipynb](/Users/elhorte/git/earth-biometrics/project-id/doc/Project_Plan_Syllabus_2026_August.ipynb), including:

- Reproducible environment setup and smoke tests.
- MegaDetector-first preprocessing pipeline.
- BioCLIP-based classification and later fusion experiments.
- California development with future Uganda domain adaptation.

## Repository layout

- [doc/](/Users/elhorte/git/earth-biometrics/project-id/doc) — project planning and syllabus notebooks.
- [notebooks/](/Users/elhorte/git/earth-biometrics/project-id/notebooks) — hands-on setup and experimentation notebooks.
- [third-party/](/Users/elhorte/git/earth-biometrics/project-id/third-party) — external dependencies/vendor code (ignored in git by default).
- [prompts/](/Users/elhorte/git/earth-biometrics/project-id/prompts) — prompt assets and related support content.

## Quick start

1. Review the syllabus notebook in [doc/](/Users/elhorte/git/earth-biometrics/project-id/doc).
2. Run the MegaDetector setup notebook:
   - [01_setup_megadetector.ipynb](/Users/elhorte/git/earth-biometrics/project-id/notebooks/01_setup_megadetector.ipynb)
3. Run the local image exercise notebook:
   - [02_megadetector_local_images.ipynb](/Users/elhorte/git/earth-biometrics/project-id/notebooks/02_megadetector_local_images.ipynb)
4. (Optional) Set up and run the SpeciesNet species classifier:
   - [04_setup_speciesnet.ipynb](/Users/elhorte/git/earth-biometrics/project-id/notebooks/04_setup_speciesnet.ipynb)
   - [05_speciesnet_local_images.ipynb](/Users/elhorte/git/earth-biometrics/project-id/notebooks/05_speciesnet_local_images.ipynb)

## Current assumptions

- Local image test folder: `/Users/elhorte/Pictures/project-id-tests`
- Third-party model code locations: `third-party/eb_MegaDetector_v6`, `third-party/eb_cameratrapai` (SpeciesNet), `third-party/bioclip-2`

## Notes

- The local image test folder may be empty at first; the exercise notebook is built to detect and report that state cleanly.
- As data collection grows, prioritize reproducibility (environment lock files) and validation artifacts (metrics, confusion matrices, and error analysis).
