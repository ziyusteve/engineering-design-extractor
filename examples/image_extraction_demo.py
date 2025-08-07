#!/usr/bin/env python3
"""
Example script demonstrating image extraction using Google Cloud Document AI Toolbox.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processors.image_extractor import ImageExtractor
from core.extractor import EngineeringCriteriaExtractor
from loguru import logger


def main():
    """Demonstrate image extraction functionality."""
    
    # Configuration - replace with your actual values
    PROJECT_ID = "your-google-cloud-project-id"
    PROCESSOR_ID = "your-document-ai-processor-id"
    LOCATION = "us"
    
    # Input and output paths
    INPUT_FILE = "data/input/example_drawing.pdf"  # Replace with your PDF file
    OUTPUT_DIR = "data/output"
    IMAGE_OUTPUT_DIR = "data/extracted_images"
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.info("Please place a PDF file in the data/input directory and update the INPUT_FILE variable.")
        return
    
    try:
        # Initialize the engineering criteria extractor with image extraction enabled
        logger.info("Initializing Engineering Criteria Extractor with image extraction...")
        extractor = EngineeringCriteriaExtractor(
            project_id=PROJECT_ID,
            processor_id=PROCESSOR_ID,
            location=LOCATION
        )
        
        # Generate a job ID for organizing extracted images
        import uuid
        job_id = str(uuid.uuid4())
        
        # Process the document with image extraction
        logger.info(f"Processing document with image extraction: {INPUT_FILE}")
        result = extractor.extract_from_file(INPUT_FILE, OUTPUT_DIR)
        
        if result.status == "completed":
            logger.info("✅ Document processed successfully!")
            logger.info(f"Results saved to: {OUTPUT_DIR}")
            
            # Display extracted information
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
                
                # Show details about extracted images
                if criteria.images:
                    logger.info("\n🖼️ Extracted Images:")
                    for i, image in enumerate(criteria.images, 1):
                        logger.info(f"  {i}. Image on page {image.page_number}")
                        logger.info(f"     Confidence: {image.confidence:.2%}")
                        if image.file_path:
                            logger.info(f"     Saved to: {image.file_path}")
                        else:
                            logger.info(f"     No file path available")
                        logger.info(f"     Bounding box: {image.bounding_box}")
                        logger.info("")
                else:
                    logger.info("\n🖼️ No images were extracted from the document.")
                
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
        logger.info("4. Installed Document AI Toolbox: pip install google-cloud-documentai-toolbox")
        logger.info("5. Updated PROJECT_ID and PROCESSOR_ID in this script")


def demonstrate_image_extractor():
    """Demonstrate the ImageExtractor class directly."""
    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING IMAGE EXTRACTOR DIRECTLY")
    logger.info("="*60)
    
    # Example Document AI response file path
    # This would be the output from Document AI processing
    document_path = "data/output/example_document_ai_response.json"
    
    if not os.path.exists(document_path):
        logger.warning(f"Document AI response file not found: {document_path}")
        logger.info("This demo requires a Document AI response JSON file.")
        return
    
    try:
        # Initialize image extractor
        image_extractor = ImageExtractor(output_dir="data/extracted_images_demo")
        
        # Extract images with metadata
        job_id = "demo_job_123"
        result = image_extractor.extract_images_with_metadata(
            document_path=document_path,
            job_id=job_id,
            output_file_prefix="demo_image",
            output_file_extension="png"
        )
        
        logger.info(f"✅ Image extraction completed!")
        logger.info(f"📁 Output directory: {result['output_directory']}")
        logger.info(f"🖼️ Total images extracted: {result['total_images']}")
        logger.info(f"📄 Image metadata entries: {len(result['image_metadata'])}")
        
        # Show extracted file paths
        if result['extracted_files']:
            logger.info("\n📁 Extracted image files:")
            for file_path in result['extracted_files']:
                logger.info(f"  - {file_path}")
        
        # Show image metadata
        if result['image_metadata']:
            logger.info("\n📊 Image metadata:")
            for i, metadata in enumerate(result['image_metadata'][:3], 1):  # Show first 3
                logger.info(f"  {i}. Page {metadata['page_number']}, Index {metadata['image_index']}")
                logger.info(f"     Confidence: {metadata['confidence']:.2%}")
                logger.info(f"     Bounding box: {metadata['bounding_box']}")
                if 'mime_type' in metadata:
                    logger.info(f"     MIME type: {metadata['mime_type']}")
                logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error in image extraction demo: {str(e)}")


if __name__ == "__main__":
    # Run the main engineering criteria extraction with image extraction
    main()
    
    # Run the direct image extractor demonstration
    demonstrate_image_extractor() 