"""
Batch processor for handling multiple engineering documents.
"""

import os
import time
import json
from typing import Dict, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from .extractor import EngineeringCriteriaExtractor
from ..models.schemas import ExtractionResult
from ..models.document_models import ProcessingStatus


class BatchProcessor:
    """
    Batch processor for extracting engineering criteria from multiple documents.
    """
    
    def __init__(self, project_id: str, processor_id: str, location: str = "us", max_workers: int = 4):
        """
        Initialize the batch processor.
        
        Args:
            project_id: Google Cloud project ID
            processor_id: Document AI processor ID
            location: Processor location
            max_workers: Maximum number of concurrent workers
        """
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        self.max_workers = max_workers
        
        # Initialize extractor
        self.extractor = EngineeringCriteriaExtractor(
            project_id=project_id,
            processor_id=processor_id,
            location=location
        )
        
        logger.info(f"Batch processor initialized with {max_workers} workers")
    
    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, ExtractionResult]:
        """
        Process all PDF files in a directory using parallel processing.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save results
            
        Returns:
            Dictionary mapping filenames to extraction results
        """
        # Find all PDF files
        pdf_files = list(Path(input_dir).glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return {}
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Process files in parallel
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file, str(pdf_file), output_dir): pdf_file.name
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                    results[filename] = result
                    
                    if result.status == ProcessingStatus.COMPLETED:
                        logger.info(f"✅ Completed: {filename}")
                    else:
                        logger.error(f"❌ Failed: {filename} - {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"❌ Exception processing {filename}: {str(e)}")
                    results[filename] = ExtractionResult(
                        job_id=str(uuid.uuid4()),
                        status=ProcessingStatus.FAILED,
                        error_message=str(e)
                    )
        
        # Generate summary
        total_time = time.time() - start_time
        successful = sum(1 for r in results.values() if r.status == ProcessingStatus.COMPLETED)
        failed = len(results) - successful
        
        logger.info(f"🎉 Batch processing complete!")
        logger.info(f"   Total files: {len(results)}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Total time: {total_time:.2f} seconds")
        logger.info(f"   Average time per file: {total_time/len(results):.2f} seconds")
        
        # Save batch summary
        self._save_batch_summary(results, output_dir, total_time)
        
        return results
    
    def _process_single_file(self, file_path: str, output_dir: str) -> ExtractionResult:
        """
        Process a single file (used by ThreadPoolExecutor).
        
        Args:
            file_path: Path to the PDF file
            output_dir: Output directory
            
        Returns:
            ExtractionResult
        """
        try:
            return self.extractor.extract_from_file(file_path, output_dir)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return ExtractionResult(
                job_id=str(uuid.uuid4()),
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
    
    def _save_batch_summary(self, results: Dict[str, ExtractionResult], output_dir: str, total_time: float):
        """
        Save a summary of batch processing results.
        
        Args:
            results: Dictionary of extraction results
            output_dir: Output directory
            total_time: Total processing time
        """
        summary = {
            "batch_summary": {
                "total_files": len(results),
                "successful": sum(1 for r in results.values() if r.status == ProcessingStatus.COMPLETED),
                "failed": sum(1 for r in results.values() if r.status == ProcessingStatus.FAILED),
                "total_time_seconds": total_time,
                "average_time_per_file": total_time / len(results) if results else 0
            },
            "file_results": {}
        }
        
        for filename, result in results.items():
            summary["file_results"][filename] = {
                "status": result.status,
                "processing_time": result.processing_time,
                "error_message": result.error_message,
                "confidence_score": result.design_criteria.confidence_score if result.design_criteria else None
            }
        
        # Save summary to JSON
        summary_file = os.path.join(output_dir, "batch_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save summary to text
        summary_text_file = os.path.join(output_dir, "batch_summary.txt")
        with open(summary_text_file, 'w') as f:
            f.write("BATCH PROCESSING SUMMARY\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"Total files processed: {summary['batch_summary']['total_files']}\n")
            f.write(f"Successful: {summary['batch_summary']['successful']}\n")
            f.write(f"Failed: {summary['batch_summary']['failed']}\n")
            f.write(f"Total time: {summary['batch_summary']['total_time_seconds']:.2f} seconds\n")
            f.write(f"Average time per file: {summary['batch_summary']['average_time_per_file']:.2f} seconds\n\n")
            
            f.write("FILE RESULTS:\n")
            f.write("-" * 20 + "\n")
            for filename, file_result in summary["file_results"].items():
                status_icon = "✅" if file_result["status"] == "completed" else "❌"
                f.write(f"{status_icon} {filename}\n")
                if file_result["error_message"]:
                    f.write(f"   Error: {file_result['error_message']}\n")
                if file_result["confidence_score"]:
                    f.write(f"   Confidence: {file_result['confidence_score']:.2%}\n")
                f.write("\n")
        
        logger.info(f"Batch summary saved to: {output_dir}")
    
    def get_processing_stats(self, results: Dict[str, ExtractionResult]) -> Dict[str, any]:
        """
        Get processing statistics from results.
        
        Args:
            results: Dictionary of extraction results
            
        Returns:
            Dictionary with processing statistics
        """
        total_files = len(results)
        successful = sum(1 for r in results.values() if r.status == ProcessingStatus.COMPLETED)
        failed = total_files - successful
        
        # Calculate confidence statistics
        confidence_scores = [
            r.design_criteria.confidence_score 
            for r in results.values() 
            if r.design_criteria and r.status == ProcessingStatus.COMPLETED
        ]
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        min_confidence = min(confidence_scores) if confidence_scores else 0
        max_confidence = max(confidence_scores) if confidence_scores else 0
        
        return {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_files if total_files > 0 else 0,
            "average_confidence": avg_confidence,
            "min_confidence": min_confidence,
            "max_confidence": max_confidence
        } 