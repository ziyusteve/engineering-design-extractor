#!/usr/bin/env python3
"""
Test script to verify Google Cloud Document AI configuration.
Run this script to check if your Document AI setup is working correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import documentai_v1
from google.api_core import client_options
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPIError

def test_authentication():
    """Test Google Cloud authentication."""
    print("🔐 Testing Google Cloud Authentication...")
    
    try:
        # Test if credentials are available
        from google.auth import default
        credentials, project = default()
        print(f"✅ Authentication successful!")
        print(f"   Project ID: {project}")
        return True
    except DefaultCredentialsError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please set up authentication using one of these methods:")
        print("   1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("   2. Run: gcloud auth application-default login")
        return False

def test_document_ai_api():
    """Test Document AI API access."""
    print("\n📄 Testing Document AI API Access...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
        
        if not project_id:
            print("❌ GOOGLE_CLOUD_PROJECT_ID not set in environment")
            return False
        
        # Initialize Document AI client
        opts = client_options.ClientOptions(
            api_endpoint=f"{location}-documentai.googleapis.com"
        )
        client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
        
        # List processors to test API access
        parent = f"projects/{project_id}/locations/{location}"
        request = documentai_v1.ListProcessorsRequest(parent=parent)
        
        page_result = client.list_processors(request=request)
        processors = list(page_result)
        
        print(f"✅ Document AI API access successful!")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")
        print(f"   Available processors: {len(processors)}")
        
        # Display available processors
        if processors:
            print("\n   Available Processors:")
            for processor in processors[:5]:  # Show first 5
                processor_id = processor.name.split('/')[-1]
                print(f"   - {processor_id}: {processor.display_name}")
            if len(processors) > 5:
                print(f"   ... and {len(processors) - 5} more")
        
        return True
        
    except GoogleAPIError as e:
        print(f"❌ Document AI API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_processor_access():
    """Test access to specific processor."""
    print("\n🔧 Testing Processor Access...")
    
    try:
        load_dotenv()
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
        location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
        
        if not processor_id:
            print("⚠️  DOCUMENT_AI_PROCESSOR_ID not set - skipping processor test")
            return True
        
        # Initialize client
        opts = client_options.ClientOptions(
            api_endpoint=f"{location}-documentai.googleapis.com"
        )
        client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
        
        # Get processor details
        processor_name = client.processor_path(project_id, location, processor_id)
        request = documentai_v1.GetProcessorRequest(name=processor_name)
        processor = client.get_processor(request=request)
        
        print(f"✅ Processor access successful!")
        print(f"   Processor ID: {processor_id}")
        print(f"   Display Name: {processor.display_name}")
        print(f"   Type: {processor.type_}")
        print(f"   State: {processor.state}")
        
        return True
        
    except GoogleAPIError as e:
        print(f"❌ Processor access error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_sample_document():
    """Test processing a sample document."""
    print("\n📋 Testing Sample Document Processing...")
    
    try:
        load_dotenv()
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
        location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
        
        if not processor_id:
            print("⚠️  DOCUMENT_AI_PROCESSOR_ID not set - skipping document test")
            return True
        
        # Check if sample document exists
        sample_doc_path = project_root / "examples" / "sample_document.pdf"
        if not sample_doc_path.exists():
            print("⚠️  Sample document not found - create examples/sample_document.pdf to test")
            return True
        
        # Initialize client
        opts = client_options.ClientOptions(
            api_endpoint=f"{location}-documentai.googleapis.com"
        )
        client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
        
        # Read sample document
        with open(sample_doc_path, "rb") as f:
            document_content = f.read()
        
        # Process document
        processor_name = client.processor_path(project_id, location, processor_id)
        raw_document = documentai_v1.RawDocument(
            content=document_content,
            mime_type="application/pdf"
        )
        
        request = documentai_v1.ProcessRequest(
            name=processor_name,
            raw_document=raw_document
        )
        
        result = client.process_document(request=request)
        document = result.document
        
        print(f"✅ Document processing successful!")
        print(f"   Text length: {len(document.text)} characters")
        print(f"   Pages: {len(document.pages)}")
        print(f"   Entities: {len(document.entities)}")
        
        return True
        
    except GoogleAPIError as e:
        print(f"❌ Document processing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all configuration tests."""
    print("🧪 Google Cloud Document AI Configuration Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    tests = [
        ("Authentication", test_authentication),
        ("Document AI API", test_document_ai_api),
        ("Processor Access", test_processor_access),
        ("Sample Document", test_sample_document)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your Document AI configuration is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration guide.")
        print("   See: config/google_cloud_setup.md")

if __name__ == "__main__":
    main() 