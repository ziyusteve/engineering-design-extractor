#!/usr/bin/env python3
"""
Debug script to check Document AI response structure
"""

import os
import json
from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1

def debug_document_ai_response():
    """Debug Document AI response structure"""
    
    # Configuration
    project_id = "780602690454"
    processor_id = "c705f988c0c92012"
    location = "us"
    file_path = "data/uploads/20250807_125428_Example_Drawing_Package_1A-1.pdf"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        # Set up Document AI client
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
        
        # Get processor reference
        full_processor_name = client.processor_path(project_id, location, processor_id)
        request = documentai_v1.GetProcessorRequest(name=full_processor_name)
        processor = client.get_processor(request=request)
        
        # Read the file into memory
        with open(file_path, "rb") as file:
            file_content = file.read()
        
        # Create raw document
        raw_document = documentai_v1.RawDocument(
            content=file_content,
            mime_type="application/pdf"
        )
        
        # Process document
        request = documentai_v1.ProcessRequest(
            name=processor.name, 
            raw_document=raw_document
        )
        
        result = client.process_document(request=request)
        document = result.document
        
        print(f"Document AI returned {len(document.entities)} entities")
        
        # Debug each entity
        for i, entity in enumerate(document.entities):
            print(f"\n=== Entity {i+1}: {entity.type_} ===")
            print(f"Text: {entity.mention_text[:100]}...")
            print(f"Confidence: {entity.confidence}")
            
            # Check page_anchor
            if hasattr(entity, 'page_anchor') and entity.page_anchor:
                print(f"Has page_anchor: True")
                print(f"Page anchor type: {type(entity.page_anchor)}")
                
                if hasattr(entity.page_anchor, 'page_refs') and entity.page_anchor.page_refs:
                    print(f"Has page_refs: True")
                    print(f"Page refs length: {len(entity.page_anchor.page_refs)}")
                    
                    page_ref = entity.page_anchor.page_refs[0]
                    print(f"Page ref type: {type(page_ref)}")
                    print(f"Page ref attributes: {dir(page_ref)}")
                    
                    if hasattr(page_ref, 'page'):
                        print(f"Page number: {page_ref.page}")
                    
                    if hasattr(page_ref, 'bounding_poly') and page_ref.bounding_poly:
                        print(f"Has bounding_poly: True")
                        print(f"Bounding poly type: {type(page_ref.bounding_poly)}")
                        print(f"Bounding poly attributes: {dir(page_ref.bounding_poly)}")
                        
                        if hasattr(page_ref.bounding_poly, 'vertices') and page_ref.bounding_poly.vertices:
                            print(f"Has vertices: True")
                            print(f"Vertices length: {len(page_ref.bounding_poly.vertices)}")
                            
                            for j, vertex in enumerate(page_ref.bounding_poly.vertices):
                                print(f"  Vertex {j}: x={vertex.x}, y={vertex.y}")
                        else:
                            print("No vertices found")
                        
                        # Check normalized_vertices
                        if hasattr(page_ref.bounding_poly, 'normalized_vertices') and page_ref.bounding_poly.normalized_vertices:
                            print(f"Has normalized_vertices: True")
                            print(f"Normalized vertices length: {len(page_ref.bounding_poly.normalized_vertices)}")
                            
                            for j, vertex in enumerate(page_ref.bounding_poly.normalized_vertices):
                                print(f"  Normalized vertex {j}: x={vertex.x}, y={vertex.y}")
                        else:
                            print("No normalized_vertices found")
                    else:
                        print("No bounding_poly found")
                else:
                    print("No page_refs found")
            else:
                print("No page_anchor found")
            
            # Check for other possible bounding box locations
            if hasattr(entity, 'layout') and entity.layout:
                print(f"Has layout: True")
                if hasattr(entity.layout, 'bounding_poly') and entity.layout.bounding_poly:
                    print(f"Layout has bounding_poly: True")
                    if hasattr(entity.layout.bounding_poly, 'vertices') and entity.layout.bounding_poly.vertices:
                        print(f"Layout vertices length: {len(entity.layout.bounding_poly.vertices)}")
                        for j, vertex in enumerate(entity.layout.bounding_poly.vertices):
                            print(f"  Layout vertex {j}: x={vertex.x}, y={vertex.y}")
        
        # Save raw response to JSON for inspection
        output_file = "debug_document_ai_response.json"
        with open(output_file, 'w') as f:
            # Convert document to dict-like structure
            doc_dict = {
                'text': document.text,
                'pages': [{'page_number': p.page_number} for p in document.pages],
                'entities': []
            }
            
            for entity in document.entities:
                entity_dict = {
                    'type': entity.type_,
                    'mention_text': entity.mention_text,
                    'confidence': entity.confidence
                }
                
                if hasattr(entity, 'page_anchor') and entity.page_anchor:
                    entity_dict['page_anchor'] = {
                        'page_refs': []
                    }
                    
                    if hasattr(entity.page_anchor, 'page_refs') and entity.page_anchor.page_refs:
                        for page_ref in entity.page_anchor.page_refs:
                            page_ref_dict = {
                                'page': getattr(page_ref, 'page', None)
                            }
                            
                            if hasattr(page_ref, 'bounding_poly') and page_ref.bounding_poly:
                                page_ref_dict['bounding_poly'] = {
                                    'vertices': []
                                }
                                
                                if hasattr(page_ref.bounding_poly, 'vertices') and page_ref.bounding_poly.vertices:
                                    for vertex in page_ref.bounding_poly.vertices:
                                        page_ref_dict['bounding_poly']['vertices'].append({
                                            'x': vertex.x,
                                            'y': vertex.y
                                        })
                            
                            entity_dict['page_anchor']['page_refs'].append(page_ref_dict)
                
                doc_dict['entities'].append(entity_dict)
            
            json.dump(doc_dict, f, indent=2)
        
        print(f"\nRaw response saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_document_ai_response() 