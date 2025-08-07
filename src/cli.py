#!/usr/bin/env python3
"""
Command-line interface for engineering design criteria extraction.
"""

import argparse
import os
import sys
from pathlib import Path
from loguru import logger

from .core.extractor import EngineeringCriteriaExtractor


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Extract engineering design criteria from PDF documents using Google Cloud Document AI"
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input PDF file or directory containing PDF files"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="data/output",
        help="Output directory for results (default: data/output)"
    )
    
    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID (default: from GOOGLE_CLOUD_PROJECT env var)"
    )
    
    parser.add_argument(
        "--processor-id",
        help="Document AI processor ID (default: from DOCUMENT_AI_PROCESSOR_ID env var)"
    )
    
    parser.add_argument(
        "--location",
        default="us",
        help="Document AI processor location (default: us)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    # Get configuration
    project_id = args.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    processor_id = args.processor_id or os.getenv("DOCUMENT_AI_PROCESSOR_ID")
    
    if not project_id or not processor_id:
        logger.error("Google Cloud configuration not found. Please provide --project-id and --processor-id or set GOOGLE_CLOUD_PROJECT and DOCUMENT_AI_PROCESSOR_ID environment variables.")
        sys.exit(1)
    
    # Initialize extractor
    try:
        extractor = EngineeringCriteriaExtractor(
            project_id=project_id,
            processor_id=processor_id,
            location=args.location
        )
        logger.info("Engineering Criteria Extractor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize extractor: {str(e)}")
        sys.exit(1)
    
    # Process input
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
    
    try:
        if input_path.is_file():
            # Process single file
            if not input_path.suffix.lower() == '.pdf':
                logger.error(f"Input file must be a PDF: {input_path}")
                sys.exit(1)
            
            logger.info(f"Processing single file: {input_path}")
            result = extractor.extract_from_file(str(input_path), str(output_path))
            
            if result.status == "completed":
                logger.info(f"Successfully processed {input_path.name}")
                logger.info(f"Results saved to: {output_path}")
            else:
                logger.error(f"Failed to process {input_path.name}: {result.error_message}")
                sys.exit(1)
                
        elif input_path.is_dir():
            # Process directory
            logger.info(f"Processing directory: {input_path}")
            results = extractor.extract_from_directory(str(input_path), str(output_path))
            
            successful = sum(1 for r in results.values() if r.status == "completed")
            failed = len(results) - successful
            
            logger.info(f"Processing complete: {successful} successful, {failed} failed")
            
            if failed > 0:
                logger.warning("Some files failed to process:")
                for filename, result in results.items():
                    if result.status != "completed":
                        logger.warning(f"  {filename}: {result.error_message}")
        
        else:
            logger.error(f"Input path is neither a file nor directory: {input_path}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 