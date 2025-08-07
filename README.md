# Engineering Design Criteria Extractor

A comprehensive software system for automating the extraction of engineering design criteria from scanned legacy drawings and documents, specifically designed for maritime and civil infrastructure assets.

## Overview

This project leverages Google Cloud Document AI to extract structured engineering design criteria from legacy PDF documents, including:
- **Loads**: Dead loads, live loads, environmental loads
- **Seismic Forces**: Earthquake design parameters
- **Design Vehicles**: Vehicle specifications and requirements
- **Design Cranes**: Crane specifications and operational parameters
- **Tables and Images**: Structured data extraction from visual elements

## Features

- **Document AI Integration**: Uses Google Cloud Document AI for intelligent document processing
- **Custom Processors**: Built with Document AI Workbench for specialized engineering criteria extraction
- **Image and Table Extraction**: Intelligent cropping and processing of visual elements using Document AI Toolbox
- **Structured Output**: Generates organized reports for asset management decision-making
- **API Interface**: RESTful API for document processing
- **Web Application**: Flask-based web interface with drag-and-drop file upload
- **Real-time Updates**: Live status updates and progress tracking
- **Batch Processing**: Handle multiple documents efficiently

## Project Structure

```
engineering-design-extractor/
├── config/                 # Configuration files
├── data/                   # Data directories
│   ├── input/             # Input PDF documents
│   ├── output/            # Extracted results
│   └── processed/         # Processed documents
├── docs/                  # Documentation
├── examples/              # Example documents and usage
├── src/                   # Source code
│   ├── api/              # FastAPI application
│   ├── core/             # Core extraction logic
│   ├── models/           # Data models and schemas
│   ├── processors/       # Document AI processors
│   └── utils/            # Utility functions
├── tests/                # Test files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd engineering-design-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud Document AI**:
   - Follow the complete setup guide: [Google Cloud Document AI Configuration](config/google_cloud_setup.md)
   - Or use the quick setup below:

### Quick Google Cloud Setup

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable documentai.googleapis.com
gcloud services enable storage.googleapis.com

# Create service account
gcloud iam service-accounts create document-ai-extractor \
    --display-name="Document AI Extractor"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:document-ai-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser"

# Download service account key
gcloud iam service-accounts keys create ~/document-ai-key.json \
    --iam-account=document-ai-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. **Configure environment variables**:
   ```bash
   # Copy template
   cp env.template .env
   
   # Edit .env with your values
   nano .env
   ```

5. **Test configuration**:
   ```bash
   python3 examples/test_document_ai_config.py
   ```

## Usage

### Quick Start

1. **Set up Google Cloud Document AI**:
   - Enable the Document AI API in your Google Cloud project
   - Create a processor (you can use OCR_PROCESSOR or a custom processor)
   - Note your project ID and processor ID

2. **Configure the application**:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export DOCUMENT_AI_PROCESSOR_ID="your-processor-id"
   ```

3. **Process a single document**:
   ```bash
   python -m src.cli --input data/input/your_document.pdf --output data/output/
   ```

### Web Application

Start the Flask web application:
```bash
python -m src.webapp.run
```

The web app will be available at `http://localhost:5000` with a user-friendly interface for uploading documents and viewing results.

### API Server

Start the FastAPI server:
```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

### Command Line Interface

Process a single document:
```bash
python -m src.cli --input path/to/document.pdf --output results/
```

Process multiple documents:
```bash
python -m src.cli --input data/input/ --output data/output/
```

### Python API

```python
from src.core.extractor import EngineeringCriteriaExtractor

# Initialize extractor
extractor = EngineeringCriteriaExtractor(
    project_id="your-project-id",
    processor_id="your-processor-id",
    location="us"
)

# Extract criteria from a PDF
result = extractor.extract_from_file("path/to/document.pdf", "output/")

if result.status == "completed":
    print(f"Extracted {len(result.design_criteria.loads)} loads")
    print(f"Extracted {len(result.design_criteria.tables)} tables")
```

### Example Scripts

Run the basic extraction example:
```bash
python examples/simple_extraction.py
```

Run the image extraction demo:
```bash
python examples/image_extraction_demo.py
```

## Configuration

### Google Cloud Document AI Setup

1. **Enable Document AI API** in your Google Cloud project
2. **Create a processor**:
   - For basic OCR and text extraction: Use `OCR_PROCESSOR`
   - For custom entity extraction: Create a custom processor using Document AI Workbench
3. **Get your processor ID** from the Google Cloud Console
4. **Set up authentication**:
   - For local development: Use service account key file
   - For cloud deployment: Use default credentials

### Environment Variables

Create a `.env` file with the following variables:
```
GOOGLE_CLOUD_PROJECT=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
STORAGE_BUCKET=your-storage-bucket
```

## Web Application Features

- **File Upload**: Drag-and-drop PDF upload with file validation
- **Job Management**: View all processing jobs with status tracking
- **Real-time Updates**: Automatic page refresh for processing jobs
- **Results Visualization**: Interactive display of extracted criteria
- **Image Gallery**: View extracted images from engineering drawings
- **Download Results**: Export results as JSON files

## API Endpoints

- `POST /api/v1/extract` - Extract criteria from a single document
- `POST /api/v1/batch-extract` - Process multiple documents
- `GET /api/v1/status/{job_id}` - Check processing status
- `GET /api/v1/results/{job_id}` - Retrieve extraction results

## Data Models

### Engineering Design Criteria

```python
class DesignCriteria(BaseModel):
    loads: List[LoadSpecification]
    seismic_forces: List[SeismicForce]
    design_vehicles: List[DesignVehicle]
    design_cranes: List[DesignCrane]
    tables: List[TableData]
    images: List[ImageData]
    metadata: DocumentMetadata
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team. 