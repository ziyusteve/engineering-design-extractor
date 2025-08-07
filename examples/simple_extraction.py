#!/usr/bin/env python3
"""
Simple example of using the Engineering Design Criteria Extractor.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.extractor import EngineeringCriteriaExtractor
from loguru import logger


def main():
    """Example usage of the engineering criteria extractor."""
    
    # Configuration - replace with your actual values
    PROJECT_ID = "your-google-cloud-project-id"
    PROCESSOR_ID = "your-document-ai-processor-id"
    LOCATION = "us"
    
    # Input and output paths
    INPUT_FILE = "data/input/example_drawing.pdf"  # Replace with your PDF file
    OUTPUT_DIR = "data/output"
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.info("Please place a PDF file in the data/input directory and update the INPUT_FILE variable.")
        return
    
    try:
        # Initialize the extractor
        logger.info("Initializing Engineering Criteria Extractor...")
        extractor = EngineeringCriteriaExtractor(
            project_id=PROJECT_ID,
            processor_id=PROCESSOR_ID,
            location=LOCATION
        )
        
        # Process the document
        logger.info(f"Processing document: {INPUT_FILE}")
        result = extractor.extract_from_file(INPUT_FILE, OUTPUT_DIR)
        
        if result.status == "completed":
            logger.info("✅ Document processed successfully!")
            logger.info(f"Results saved to: {OUTPUT_DIR}")
            
            # Display some extracted information
            if result.design_criteria:
                criteria = result.design_criteria
                logger.info(f"📄 Document: {criteria.metadata.filename}")
                logger.info(f"📊 Overall confidence: {criteria.confidence_score:.2%}")
                logger.info(f"📋 Loads extracted: {len(criteria.loads)}")
                logger.info(f"🌊 Seismic forces: {len(criteria.seismic_forces)}")
                logger.info(f"🚗 Design vehicles: {len(criteria.design_vehicles)}")
                logger.info(f"🏗️ Design cranes: {len(criteria.design_cranes)}")
                logger.info(f"📊 Tables: {len(criteria.tables)}")
                logger.info(f"🖼️ Images: {len(criteria.images)}")
                
                # Show some details about extracted loads
                if criteria.loads:
                    logger.info("\n📋 Extracted Loads:")
                    for i, load in enumerate(criteria.loads[:3], 1):  # Show first 3
                        logger.info(f"  {i}. {load.load_type.value}: {load.magnitude} {load.unit}")
                        if load.description:
                            logger.info(f"     Description: {load.description}")
                
                # Show some details about extracted tables
                if criteria.tables:
                    logger.info("\n📊 Extracted Tables:")
                    for i, table in enumerate(criteria.tables[:2], 1):  # Show first 2
                        logger.info(f"  {i}. Table on page {table.page_number} ({len(table.rows)} rows)")
                        if table.headers:
                            logger.info(f"     Headers: {', '.join(table.headers)}")
        else:
            logger.error(f"❌ Processing failed: {result.error_message}")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        logger.info("Make sure you have:")
        logger.info("1. Set up Google Cloud credentials")
        logger.info("2. Enabled Document AI API")
        logger.info("3. Created a Document AI processor")
        logger.info("4. Updated PROJECT_ID and PROCESSOR_ID in this script")


if __name__ == "__main__":
    main() 