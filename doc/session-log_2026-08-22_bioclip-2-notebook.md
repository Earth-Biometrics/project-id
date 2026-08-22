# Session Log — BioCLIP-2 Species ID Notebook Setup

- **Date:** 2026-08-22
- **Repository:** Earth-Biometrics/project-id (branch `main`)
- **Working directory:** `/Users/elhorte/git/ebio/project-id`
- **Environment:** `.venv` (Python 3.13.13, macOS / Apple Silicon)
- **Assistant:** AI assistant using Copilot CLI runtime in VS Code

---

## 1. User Request

> I would like to bring up the bioclip-2 image identification ML at:
> `project-id/third-party/bioclip-2`. I have opened a blank notebook at:
> `project-id/notebooks/03_bioclip-2_species_ID`. Please build a set up and run
> series of steps similar to `project-id/notebooks/02_megadetector_local_images.ipynb`.
> A `.venv` environment is already in place, may need additional libraries.
> Please create a `requirements.txt` for the full project-id folder.

---

## 2. Investigation & Findings

### Existing reference notebook (`02_megadetector_local_images.ipynb`)
- Structure: markdown intro → define paths → discover images → build image list →
  run inference (subprocess) → summarize detections → visualize bounding boxes.
- Uses paths on `/Volumes/BigMacX/ebio/...` and writes outputs to
  `/Volumes/BigMacX/ebio/project-id/outputs/megadetector`.
- Notebook metadata kernel: `.venv (3.13.13.final.0)`, `nbformat` 4.

### Target placeholder (`notebooks/03_bioclip-2_species_ID`)
- Was a **0-byte extensionless file** (not valid notebook JSON) — needed to be
  created as a proper `.ipynb`.

### Third-party source (`third-party/bioclip-2`)
- This is the **BioCLIP 2 training / evaluation** repository (an OpenCLIP fork),
  not an inference package. Its own README notes BioCLIP 2 is the **default model
  in the `pybioclip` package**, which is the officially recommended inference path.

### Environment (`.venv`, Python 3.13)
- Already present: `torch 2.13.0`, `torchvision 0.28.0`, `pillow 12.3.0`,
  `pandas 3.0.5`, `numpy 2.5.2`, `megadetector 10.0.24`, `ipykernel 7.3.0`,
  `matplotlib 3.11.1`.
- Missing: any BioCLIP / open_clip inference package.

### Decision point (asked the user)
- **Question:** which engine should notebook 03 use?
- **User chose:** **`pybioclip`** (official inference wrapper) — full Tree-of-Life
  taxonomic prediction (kingdom → species) out of the box, same BioCLIP-2 weights
  (`hf-hub:imageomics/bioclip-2`).

### API verification (pybioclip 2.1.6)
- `TreeOfLifeClassifier(device=...)`, `.predict(images, rank=Rank.SPECIES, k=..., callback=...)`.
- Default model string resolves to `hf-hub:imageomics/bioclip-2` (TreeOfLife-200M labels).
- `predict()` returns a list of row dicts with keys:
  `file_name, kingdom, phylum, class, order, family, genus, species_epithet,
  species, common_name, score`.
- Also available: `CustomLabelsClassifier(cls_ary, device=...)` for a restricted
  candidate-label list.

---

## 3. Actions Taken

1. **Installed `pybioclip` into the existing `.venv`** (pulled in
   `open_clip_torch 3.3.0`, `timm 1.0.28`, `huggingface-hub 1.28.0`, `ftfy`,
   `safetensors`, `regex`, etc.).
2. **Removed** the stray 0-byte `notebooks/03_bioclip-2_species_ID` placeholder.
3. **Created** `notebooks/03_bioclip-2_species_ID.ipynb` (valid nbformat 4,
   20 cells), mirroring notebook 02's structure.
4. **Created** project-level `requirements.txt`, pinned to the working `.venv`.
5. **Validated** the notebook JSON and confirmed all code cells compile.
6. **Ran an end-to-end smoke test** (model download + one prediction) — passed.

---

## 4. Deliverables

### `notebooks/03_bioclip-2_species_ID.ipynb`
Step-by-step flow:

1. **Define paths** — repo root, `third-party/bioclip-2`, image dir
   (`/Volumes/BigMacX/ebio/Pictures`), output dir
   (`/Volumes/BigMacX/ebio/project-id/outputs/bioclip-2`).
2. **Install / verify engine** — auto-installs `pybioclip` if missing.
3. **Smoke-test imports + select device** — CPU default, optional `mps`.
4. **Check image folder contents** — recursive scan for common image extensions.
5. **Load BioCLIP-2** `TreeOfLifeClassifier` (notes one-time HF model download).
6. **Run species identification** — top-k predictions per image → CSV
   `bioclip2_species_predictions.csv`.
7. **Top-1 summary per image** → CSV `bioclip2_top1_summary.csv`.
8. **Visualize identifications** — inline previews captioned with species,
   common name, and score.
- **Optional cell** — `CustomLabelsClassifier` for a project-specific candidate
  species list.
- **Next steps** — chaining MegaDetector crops into BioCLIP-2 for best accuracy.

### `requirements.txt` (project-wide)
Pinned to the working `.venv` (Python 3.13):

```
ipykernel==7.3.0
matplotlib==3.11.1
numpy==2.5.2
pandas==3.0.5
pillow==12.3.0
torch==2.13.0
torchvision==0.28.0
megadetector==10.0.24
pybioclip==2.1.6
open_clip_torch==3.3.0
timm==1.0.28
huggingface-hub==1.28.0
```

---

## 5. Verification Results

- Notebook JSON validated; **all 20 cells compile** without syntax errors.
- **End-to-end smoke test passed**: BioCLIP-2 loaded
  (`hf-hub:imageomics/bioclip-2`) and returned predictions with exactly the
  columns the notebook consumes. Example output row for a synthetic test image:

  ```
  file_name: /tmp/bioclip_smoke.jpg
  kingdom: Animalia    phylum: Chordata     class: Aves
  order: Passeriformes family: Cisticolidae genus: Camaroptera
  species: Camaroptera chloronota  common_name: Olive-green camaroptera
  score: 0.0053
  ```
  (Low score expected — the smoke image was a flat synthetic color, not a real
  organism. Confirms the pipeline runs correctly.)

---

## 6. Notes & Follow-ups

- Image/output paths point at `/Volumes/BigMacX/...` to match notebook 02.
  These can be parameterized on request.
- The **first real run downloads** the BioCLIP-2 weights + TreeOfLife-200M
  embeddings (a few GB), cached under `~/.cache/huggingface` for later runs.
- Setting a `HF_TOKEN` avoids the unauthenticated-rate-limit warning and speeds
  up downloads (optional).
- Suggested enhancement: wire the MegaDetector → crop → BioCLIP-2 step so species
  ID runs on tight subject crops (BioCLIP-2 performs best on cropped subjects).

---

*Generated as a session log for record-keeping.*
