# Architecture Diagram

This repository is a notebook-driven computer vision workflow for wildlife detection and species identification. It combines local image processing, MegaDetector, and BioCLIP-2 to turn camera-trap images into detection JSON, cropped subject images, and species prediction outputs.

## Application Architecture

<!-- mermaid-checked: no \n, no em-dash/en-dash, no {} in labels, subgraphs are id["label"], arrows are -->|"label"|, all subgraphs closed by end, ids unique -->
~~~mermaid
flowchart TD
    subgraph ClientLayer["Notebook Authoring"]
        VSCode["VS Code and Jupyter"]
    end
    subgraph RuntimeLayer["Python Runtime"]
        PyEnv["Python venv and scientific stack"]
        MDLocal["MegaDetector local checkout"]
        BCLocal["BioCLIP-2 local checkout"]
    end
    subgraph PipelineLayer["Notebook Pipelines"]
        SetupNB["Setup notebook"]
        DetectNB["Detection notebook"]
        SpeciesNB["Species notebook"]
    end
    subgraph DataLayer["Local Data"]
        ImageStore[("Camera trap image folder")]
        MDJson[("Detection results JSON")]
        CropStore[("Image crop folder")]
        OutputStore[("Prediction CSV files")]
    end
    subgraph ExternalLayer["External Services"]
        HuggingFace["Hugging Face Hub"]
    end

    VSCode -->|"runs notebooks"| SetupNB
    VSCode -->|"runs notebooks"| DetectNB
    VSCode -->|"runs notebooks"| SpeciesNB
    SetupNB -->|"prepares"| PyEnv
    DetectNB -->|"uses"| MDLocal
    SpeciesNB -->|"uses"| BCLocal
    DetectNB -->|"reads images"| ImageStore
    DetectNB -->|"writes detections"| MDJson
    SpeciesNB -->|"reads detections"| MDJson
    SpeciesNB -->|"writes crops"| CropStore
    SpeciesNB -->|"writes predictions"| OutputStore
    PyEnv -->|"downloads weights"| HuggingFace
    MDLocal -->|"fetches model assets"| HuggingFace
    BCLocal -->|"fetches model assets"| HuggingFace
~~~

### Technology Stack Summary

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Notebook and UI | Jupyter notebooks in VS Code | Notebook based | Interactive setup, inference, and review |
| Runtime | Python | 3.13.13 | Executes all notebooks and batch inference steps |
| Scientific stack | numpy, pandas, pillow, matplotlib | 2.5.2, 3.0.5, 12.3.0, 3.11.1 | Array handling, tabular results, image I and O, plots |
| ML runtime | torch, torchvision | 2.13.0, 0.28.0 | Deep learning runtime for model inference |
| Detection stage | MegaDetector | 10.0.24 | Animal candidate detection and blank frame filtering |
| Classification stage | pybioclip, open_clip_torch, timm, huggingface-hub | 2.1.6, 3.3.0, 1.0.28, 1.28.0 | BioCLIP-2 species identification and model loading |
| Local vendor code | third-party/eb_megadetector and third-party/bioclip-2 | Current checkout | Source checkouts used by the notebooks |

### Data Storage & External Services

Input images are read from the local camera-trap image folders referenced by the notebooks, and outputs are written under `/Volumes/BigMacX/ebio/project-id/outputs/`. MegaDetector writes detection JSON, BioCLIP-2 writes prediction CSVs, and cropped animal images are stored separately for follow-on classification. Model downloads and cached weights come from Hugging Face Hub and are stored locally in the user cache.

### Key Architectural Decisions

- Uses a two-stage pipeline: MegaDetector first, then BioCLIP-2 on full images or cropped detections.
- Keeps the workflow notebook-first so setup, batch inference, review, and visualization stay reproducible.
- Resolves third-party models through local checkouts and Hugging Face cached weights instead of a custom training service.

## Component Relationships

<!-- mermaid-checked: no \n, no em-dash/en-dash, no {} in labels, subgraphs are id["label"], arrows are -->|"label"|, all subgraphs closed by end, ids unique -->
~~~mermaid
flowchart LR
    subgraph PresentationLayer["Presentation"]
        cNB1["01 setup notebook"]
        cNB2["02 detection notebook"]
        cNB3["03 species notebook"]
    end
    subgraph BusinessLayer["Business Logic"]
        cSetup["Environment setup and path discovery"]
        cDetect["Image scan and MegaDetector run"]
        cCrop["Crop and filter animal detections"]
        cClassify["BioCLIP prediction and summarization"]
        cPreview["Result preview and plotting"]
    end
    subgraph DataLayer["Data Access"]
        cImg[("Local image folder")]
        cMdJson[("Detection results JSON")]
        cCropDir[("Crop output folder")]
        cCsv[("Prediction CSV files")]
    end
    subgraph InfraLayer["Infrastructure"]
        cEnv["Python venv and ipykernel"]
        cMD["MegaDetector package"]
        cBC["pybioclip package"]
        cHF[("Hugging Face cache")]
    end

    cNB1 -->|"sets up"| cSetup
    cNB2 -->|"orchestrates"| cDetect
    cNB3 -->|"orchestrates"| cClassify
    cSetup -->|"uses"| cEnv
    cDetect -->|"reads"| cImg
    cDetect -->|"uses"| cMD
    cDetect -->|"writes"| cMdJson
    cCrop -->|"reads"| cMdJson
    cCrop -->|"writes"| cCropDir
    cClassify -->|"uses"| cBC
    cClassify -->|"reads"| cCropDir
    cClassify -->|"writes"| cCsv
    cPreview -->|"reads"| cCsv
    cEnv -->|"downloads"| cHF
    cBC -->|"loads weights from"| cHF
~~~

### Component Inventory

| Component | Layer | Type | Responsibility |
|---|---|---|---|
| 01 setup notebook | Presentation | Notebook | Bootstraps the local MegaDetector environment and validates paths |
| 02 detection notebook | Presentation | Notebook | Discovers local images, runs MegaDetector, and summarizes detections |
| 03 species notebook | Presentation | Notebook | Loads BioCLIP-2, classifies images or crops, and writes summaries |
| Environment setup and path discovery | Business Logic | Workflow stage | Resolves repo paths and prepares the execution environment |
| Image scan and MegaDetector run | Business Logic | Workflow stage | Builds image lists and executes batch detection |
| Crop and filter animal detections | Business Logic | Workflow stage | Filters detections and saves crop images for classification |
| BioCLIP prediction and summarization | Business Logic | Workflow stage | Predicts species, ranks results, and produces CSV summaries |
| Result preview and plotting | Business Logic | Workflow stage | Renders inline visual checks of detection and classification results |
| Local image folder | Data Access | File store | Holds the source camera-trap images |
| Detection results JSON | Data Access | File store | Stores MegaDetector output for downstream use |
| Crop output folder | Data Access | File store | Stores cropped subject images for BioCLIP-2 |
| Prediction CSV files | Data Access | File store | Stores final species predictions and top-1 summaries |
| Python venv and ipykernel | Infrastructure | Runtime | Provides notebook execution and package isolation |
| MegaDetector package | Infrastructure | Third-party dependency | Supplies the animal detection model and batch inference entry point |
| pybioclip package | Infrastructure | Third-party dependency | Supplies the BioCLIP-2 inference wrapper and taxonomy predictions |
| Hugging Face cache | Infrastructure | Model cache | Stores downloaded BioCLIP-2 weights and label embeddings |
