"""
Main engineering criteria extractor using Google Cloud Document AI.
"""

import os
import json
import uuid
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from ..processors.document_ai_processor import DocumentAIProcessor
from ..models.schemas import DesignCriteria, ExtractionResult
from ..models.document_models import ProcessingStatus


class EngineeringCriteriaExtractor:
    """
    Main class for extracting engineering design criteria from PDF documents.
    """
    
    def __init__(self, project_id: str, processor_id: str, location: str = "us"):
        """
        Initialize the extractor.
        
        Args:
            project_id: Google Cloud project ID
            processor_id: Document AI processor ID
            location: Processor location
        """
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        
        # Initialize Document AI processor
        self.doc_ai_processor = DocumentAIProcessor(
            project_id=project_id,
            processor_id=processor_id,
            location=location
        )
        
        logger.info("Engineering Criteria Extractor initialized")
    
    def extract_from_file(self, file_path: str, output_dir: Optional[str] = None) -> ExtractionResult:
        """
        Extract engineering criteria from a single PDF file.
        
        Args:
            file_path: Path to the PDF file
            output_dir: Directory to save results (optional)
            
        Returns:
            ExtractionResult with extracted criteria
        """
        job_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting extraction for file: {file_path}")
            
            # Validate file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.lower().endswith('.pdf'):
                raise ValueError(f"File must be a PDF: {file_path}")
            
            # Extract criteria using Document AI
            design_criteria = self.doc_ai_processor.extract_engineering_criteria(file_path, job_id)
            
            # Save results if output directory specified
            if output_dir:
                self._save_results(design_criteria, output_dir, job_id)
            
            return ExtractionResult(
                job_id=job_id,
                status=ProcessingStatus.COMPLETED,
                design_criteria=design_criteria,
                processing_time=design_criteria.metadata.processing_date.timestamp()
            )
            
        except Exception as e:
            logger.error(f"Error extracting criteria from {file_path}: {str(e)}")
            return ExtractionResult(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
    
    def extract_from_directory(self, input_dir: str, output_dir: str) -> Dict[str, ExtractionResult]:
        """
        Extract engineering criteria from all PDF files in a directory.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save results
            
        Returns:
            Dictionary mapping filenames to extraction results
        """
        results = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(Path(input_dir).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return results
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                result = self.extract_from_file(str(pdf_file), output_dir)
                results[pdf_file.name] = result
                
                if result.status == ProcessingStatus.COMPLETED:
                    logger.info(f"Successfully processed: {pdf_file.name}")
                else:
                    logger.error(f"Failed to process: {pdf_file.name} - {result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {str(e)}")
                results[pdf_file.name] = ExtractionResult(
                    job_id=str(uuid.uuid4()),
                    status=ProcessingStatus.FAILED,
                    error_message=str(e)
                )
        
        return results
    
    def _save_results(self, design_criteria: DesignCriteria, output_dir: str, job_id: str):
        """
        Save extraction results to files.
        
        Args:
            design_criteria: Extracted design criteria
            output_dir: Output directory
            job_id: Job identifier
        """
        # Create job-specific output directory
        job_output_dir = os.path.join(output_dir, job_id)
        os.makedirs(job_output_dir, exist_ok=True)
        
        # Save JSON results
        json_file = os.path.join(job_output_dir, "extraction_results.json")
        with open(json_file, 'w') as f:
            json.dump(design_criteria.dict(), f, indent=2, default=str)
        
        # Save raw text
        if design_criteria.raw_text:
            text_file = os.path.join(job_output_dir, "extracted_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(design_criteria.raw_text)
        
        # Save summary report
        summary_file = os.path.join(job_output_dir, "summary_report.txt")
        self._generate_summary_report(design_criteria, summary_file)
        
        logger.info(f"Results saved to: {job_output_dir}")
    
    def _generate_summary_report(self, design_criteria: DesignCriteria, output_file: str):
        """
        Generate a human-readable summary report.
        
        Args:
            design_criteria: Extracted design criteria
            output_file: Path to save the report
        """
        with open(output_file, 'w') as f:
            f.write("ENGINEERING DESIGN CRITERIA EXTRACTION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Document metadata
            f.write("DOCUMENT INFORMATION:\n")
            f.write(f"Filename: {design_criteria.metadata.filename}\n")
            f.write(f"File Size: {design_criteria.metadata.file_size:,} bytes\n")
            f.write(f"Pages: {design_criteria.metadata.page_count}\n")
            f.write(f"Processing Date: {design_criteria.metadata.processing_date}\n")
            f.write(f"Overall Confidence: {design_criteria.confidence_score:.2%}\n\n")
            
            # Loads
            f.write(f"LOADS EXTRACTED: {len(design_criteria.loads)}\n")
            for i, load in enumerate(design_criteria.loads, 1):
                f.write(f"  {i}. {load.load_type.value}: {load.magnitude} {load.unit}\n")
                if load.description:
                    f.write(f"     Description: {load.description}\n")
                f.write(f"     Confidence: {load.confidence:.2%}\n\n")
            
            # Seismic forces
            f.write(f"SEISMIC FORCES EXTRACTED: {len(design_criteria.seismic_forces)}\n")
            for i, seismic in enumerate(design_criteria.seismic_forces, 1):
                f.write(f"  {i}. {seismic.description}\n")
                f.write(f"     Confidence: {seismic.confidence:.2%}\n\n")
            
            # Design vehicles
            f.write(f"DESIGN VEHICLES EXTRACTED: {len(design_criteria.design_vehicles)}\n")
            for i, vehicle in enumerate(design_criteria.design_vehicles, 1):
                f.write(f"  {i}. {vehicle.vehicle_type.value}\n")
                f.write(f"     Total Weight: {vehicle.total_weight} {vehicle.unit}\n")
                f.write(f"     Confidence: {vehicle.confidence:.2%}\n\n")
            
            # Design cranes
            f.write(f"DESIGN CRANES EXTRACTED: {len(design_criteria.design_cranes)}\n")
            for i, crane in enumerate(design_criteria.design_cranes, 1):
                f.write(f"  {i}. {crane.crane_type.value}\n")
                f.write(f"     Capacity: {crane.capacity} {crane.unit}\n")
                f.write(f"     Confidence: {crane.confidence:.2%}\n\n")
            
            # Tables
            f.write(f"TABLES EXTRACTED: {len(design_criteria.tables)}\n")
            for i, table in enumerate(design_criteria.tables, 1):
                f.write(f"  {i}. Table on page {table.page_number}\n")
                f.write(f"     Rows: {len(table.rows)}\n")
                f.write(f"     Confidence: {table.confidence:.2%}\n\n")
            
            # Images
            f.write(f"IMAGES EXTRACTED: {len(design_criteria.images)}\n")
            for i, image in enumerate(design_criteria.images, 1):
                f.write(f"  {i}. Image on page {image.page_number}\n")
                f.write(f"     Confidence: {image.confidence:.2%}\n\n")
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about the Document AI processor.
        
        Returns:
            Dictionary with processor information
        """
        return {
            "project_id": self.project_id,
            "processor_id": self.processor_id,
            "location": self.location,
            "processor_name": self.doc_ai_processor.processor.name,
            "processor_type": self.doc_ai_processor.processor.type_,
            "processor_version": self.doc_ai_processor.processor.processor_version
        } 