"""
FastAPI application for engineering design criteria extraction.
"""

import os
import tempfile
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from loguru import logger
import uuid

from ..core.extractor import EngineeringCriteriaExtractor
from ..models.schemas import ExtractionResult, DesignCriteria
from ..models.document_models import ProcessingStatus


# Initialize FastAPI app
app = FastAPI(
    title="Engineering Design Criteria Extractor",
    description="API for extracting engineering design criteria from PDF documents using Google Cloud Document AI",
    version="1.0.0"
)

# Global extractor instance
extractor: Optional[EngineeringCriteriaExtractor] = None

# In-memory storage for job results (in production, use a database)
job_results = {}


class ExtractionRequest(BaseModel):
    """Request model for extraction."""
    project_id: str
    processor_id: str
    location: str = "us"


class ExtractionResponse(BaseModel):
    """Response model for extraction."""
    job_id: str
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize the extractor on startup."""
    global extractor
    
    # Get configuration from environment variables
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
    location = os.getenv("DOCUMENT_AI_LOCATION", "us")
    
    if not project_id or not processor_id:
        logger.warning("Google Cloud configuration not found. Set GOOGLE_CLOUD_PROJECT and DOCUMENT_AI_PROCESSOR_ID environment variables.")
        return
    
    try:
        extractor = EngineeringCriteriaExtractor(
            project_id=project_id,
            processor_id=processor_id,
            location=location
        )
        logger.info("Engineering Criteria Extractor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize extractor: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Engineering Design Criteria Extractor API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "extractor_initialized": extractor is not None
    }


@app.post("/api/v1/extract", response_model=ExtractionResponse)
async def extract_criteria(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    processor_id: Optional[str] = None,
    location: str = "us"
):
    """
    Extract engineering design criteria from a PDF file.
    
    Args:
        file: PDF file to process
        project_id: Google Cloud project ID (optional, uses env var if not provided)
        processor_id: Document AI processor ID (optional, uses env var if not provided)
        location: Processor location
        
    Returns:
        ExtractionResponse with job ID and status
    """
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Use provided parameters or fall back to environment variables
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not processor_id:
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
    
    if not project_id or not processor_id:
        raise HTTPException(
            status_code=500, 
            detail="Google Cloud configuration not found. Please provide project_id and processor_id or set environment variables."
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    # Create extractor for this request
    request_extractor = EngineeringCriteriaExtractor(
        project_id=project_id,
        processor_id=processor_id,
        location=location
    )
    
    # Start background processing
    job_id = str(uuid.uuid4())
    job_results[job_id] = ExtractionResult(
        job_id=job_id,
        status=ProcessingStatus.PENDING
    )
    
    background_tasks.add_task(
        process_document_background,
        job_id,
        temp_file_path,
        request_extractor
    )
    
    return ExtractionResponse(
        job_id=job_id,
        status="pending",
        message="Document processing started"
    )


async def process_document_background(job_id: str, file_path: str, request_extractor: EngineeringCriteriaExtractor):
    """
    Background task to process a document.
    
    Args:
        job_id: Job identifier
        file_path: Path to the PDF file
        request_extractor: Extractor instance
    """
    try:
        # Update job status
        job_results[job_id].status = ProcessingStatus.PROCESSING
        
        # Process the document
        result = request_extractor.extract_from_file(file_path)
        
        # Update job results
        job_results[job_id] = result
        
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        job_results[job_id] = ExtractionResult(
            job_id=job_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass


@app.get("/api/v1/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a processing job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status and progress information
    """
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    result = job_results[job_id]
    
    return {
        "job_id": job_id,
        "status": result.status,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "processing_time": result.processing_time,
        "error_message": result.error_message
    }


@app.get("/api/v1/results/{job_id}")
async def get_job_results(job_id: str):
    """
    Get the results of a completed processing job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Extracted engineering design criteria
    """
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    result = job_results[job_id]
    
    if result.status == ProcessingStatus.FAILED:
        raise HTTPException(status_code=400, detail=f"Job failed: {result.error_message}")
    
    if result.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return {
        "job_id": job_id,
        "status": result.status,
        "design_criteria": result.design_criteria.dict() if result.design_criteria else None,
        "processing_time": result.processing_time,
        "created_at": result.created_at
    }


@app.get("/api/v1/processor/info")
async def get_processor_info():
    """
    Get information about the Document AI processor.
    
    Returns:
        Processor information
    """
    if not extractor:
        raise HTTPException(status_code=500, detail="Extractor not initialized")
    
    return extractor.get_processor_info()


@app.post("/api/v1/batch-extract")
async def batch_extract(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = None,
    processor_id: Optional[str] = None,
    location: str = "us"
):
    """
    Extract engineering design criteria from multiple PDF files.
    
    Args:
        files: List of PDF files to process
        project_id: Google Cloud project ID
        processor_id: Document AI processor ID
        location: Processor location
        
    Returns:
        List of job IDs for batch processing
    """
    # Validate files
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} must be a PDF")
    
    # Use provided parameters or fall back to environment variables
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not processor_id:
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
    
    if not project_id or not processor_id:
        raise HTTPException(
            status_code=500, 
            detail="Google Cloud configuration not found. Please provide project_id and processor_id or set environment variables."
        )
    
    job_ids = []
    
    for file in files:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Create extractor for this request
        request_extractor = EngineeringCriteriaExtractor(
            project_id=project_id,
            processor_id=processor_id,
            location=location
        )
        
        # Start background processing
        job_id = str(uuid.uuid4())
        job_results[job_id] = ExtractionResult(
            job_id=job_id,
            status=ProcessingStatus.PENDING
        )
        
        background_tasks.add_task(
            process_document_background,
            job_id,
            temp_file_path,
            request_extractor
        )
        
        job_ids.append(job_id)
    
    return {
        "message": f"Started processing {len(files)} documents",
        "job_ids": job_ids
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 