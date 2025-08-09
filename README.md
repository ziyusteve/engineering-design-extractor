# Engineering Design Criteria Extractor

A tool to extract engineering design criteria from PDF drawings using Google Cloud Document AI.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Google Cloud Document AI Key
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable Document AI API
- Create a service account with Document AI permissions
- Download the JSON key as `document-ai-key.json` and place it in the project root
- Set up your `.env` file:
  ```
  GOOGLE_APPLICATION_CREDENTIALS=document-ai-key.json
  GOOGLE_CLOUD_PROJECT=your-project-id
  DOCUMENT_AI_PROCESSOR_ID=your-processor-id
  ```

### 3. Run the Web App (development)
```bash
python -m src.webapp.run
```
Visit http://localhost:5000 to upload PDFs and view results.

### 4. Command Line Usage
```bash
python -m src.cli --input data/input/your_document.pdf --output data/output/
```

For more details, see the code or ask for help.

---

## Build a Windows EXE (PyInstaller)

1) Create a virtual environment (recommended):
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python -m pip install -r requirements.txt pyinstaller
```

2) Build using the provided spec file:
```powershell
.\.venv\Scripts\pyinstaller build.spec
```
The EXE will be at `dist/EngineeringDesignExtractor.exe`.

3) First run of the EXE:
- Place `.env` next to the EXE (same directory) with the variables shown above
- Place your `document-ai-key.json` next to the EXE or set `GOOGLE_APPLICATION_CREDENTIALS` to an absolute path
- Double-click the EXE or run in PowerShell:
```powershell
.\dist\EngineeringDesignExtractor.exe
```
The app prints the URL (default `http://0.0.0.0:5000`).

Notes:
- The EXE is self‑contained; it does not require the `.venv` to exist after building
- On first run, the app creates `data/uploads`, `data/output`, `data/extracted_images` next to the EXE

## Troubleshooting

- PowerShell blocks script activation
  - Symptom: cannot run `Activate.ps1` due to execution policy
  - Fix: either run commands without activating (use full path `..\\.venv\\Scripts\\python`) or temporarily allow scripts:
    ```powershell
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
    ```

- ModuleNotFoundError: flask (when running EXE)
  - Rebuild using `build.spec` which bundles Flask and templates

- Credentials error: “File document-ai-key.json was not found.”
  - Ensure `.env` contains `GOOGLE_APPLICATION_CREDENTIALS=document-ai-key.json`
  - Place the key file next to the EXE, or set an absolute path

- Google Cloud configuration missing
  - Ensure `.env` has `GOOGLE_CLOUD_PROJECT_ID` and `DOCUMENT_AI_PROCESSOR_ID`

- Rebuild after changing dependencies
  - Remove old build folders and rebuild:
    ```powershell
    if (Test-Path dist) { Remove-Item -Recurse -Force dist }
    if (Test-Path build) { Remove-Item -Recurse -Force build }
    .\.venv\Scripts\pyinstaller build.spec
    ```