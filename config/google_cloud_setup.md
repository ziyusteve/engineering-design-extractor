# Google Cloud Document AI Configuration Guide

## Prerequisites
- Google Cloud account
- Google Cloud project with billing enabled
- Python 3.8+ installed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable billing for the project
4. Note your **Project ID** (you'll need this later)

## Step 2: Enable Required APIs

Enable these APIs in your Google Cloud project:

```bash
# Enable Document AI API
gcloud services enable documentai.googleapis.com

# Enable Cloud Storage API (if using GCS)
gcloud services enable storage.googleapis.com

# Enable Vision API (for additional image processing)
gcloud services enable vision.googleapis.com
```

## Step 3: Create Document AI Processor

### Option A: Use Pre-trained Processors (Recommended)

Document AI provides several pre-trained processors that work well for engineering documents:

1. **Document OCR Processor** - For text extraction from scanned documents
2. **Form Parser** - For structured form data extraction
3. **Invoice Parser** - For invoice-like documents
4. **Expense Parser** - For expense-related documents

### Option B: Create Custom Processor (Advanced)

If you need specialized extraction for engineering criteria:

1. Go to [Document AI Workbench](https://console.cloud.google.com/ai/document-ai/workbench)
2. Create a new processor
3. Upload sample documents
4. Label entities (loads, seismic forces, design vehicles, etc.)
5. Train the model

## Step 4: Get Processor Information

For each processor you want to use, get these details:

```bash
# List available processors
gcloud ai document processors list --location=us

# Get processor details
gcloud ai document processors describe PROCESSOR_ID --location=us
```

## Step 5: Set Up Authentication

### Option A: Service Account (Recommended for Production)

1. Create a service account:
```bash
gcloud iam service-accounts create document-ai-extractor \
    --display-name="Document AI Extractor"
```

2. Grant necessary permissions:
```bash
# Grant Document AI permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:document-ai-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser"

# Grant Cloud Storage permissions (if using GCS)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:document-ai-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

3. Download the service account key:
```bash
gcloud iam service-accounts keys create ~/document-ai-key.json \
    --iam-account=document-ai-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Option B: Application Default Credentials (Development)

```bash
# Authenticate with your Google account
gcloud auth application-default login
```

## Step 6: Environment Configuration

Create a `.env` file in your project root:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Document AI Processors
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us

# Optional: Cloud Storage bucket (if using GCS)
GCS_BUCKET_NAME=your-bucket-name
```

## Step 7: Test Configuration

Run the test script to verify your setup:

```bash
python3 examples/test_document_ai_config.py
```

## Processor Recommendations for Engineering Documents

### For General Engineering Documents:
- **Document OCR Processor**: Best for scanned drawings and text extraction
- **Form Parser**: Good for structured engineering forms

### For Specific Engineering Criteria:
- **Invoice Parser**: Can be adapted for load specifications
- **Expense Parser**: Useful for cost-related engineering data

### Custom Processor Entities to Label:
- Load specifications (dead load, live load, wind load)
- Seismic force parameters
- Design vehicle specifications
- Crane specifications
- Material properties
- Safety factors

## Troubleshooting

### Common Issues:

1. **Authentication Errors**:
   - Verify service account key path
   - Check IAM permissions
   - Ensure billing is enabled

2. **Processor Not Found**:
   - Verify processor ID and location
   - Check if processor is enabled
   - Ensure you have access permissions

3. **API Quotas**:
   - Monitor usage in Google Cloud Console
   - Request quota increases if needed

### Useful Commands:

```bash
# Check authentication
gcloud auth list

# Test Document AI API
gcloud ai document processors list --location=us

# Monitor API usage
gcloud logging read "resource.type=documentai.googleapis.com/Processor"
```

## Next Steps

After configuration, you can:
1. Run the Flask webapp: `python3 -m src.webapp.run`
2. Upload PDF documents for processing
3. View extracted engineering criteria
4. Download structured results 