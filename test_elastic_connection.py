"""
Quick test script to verify Elasticsearch Cloud connection
"""
from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

ELASTIC_URL = os.getenv("ELASTICSEARCH_URL")
ELASTIC_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")
ELASTIC_CLOUD_ID = os.getenv("ELASTICSEARCH_CLOUD_ID")  # Try Cloud ID if available

print(f"Testing connection...")
if ELASTIC_CLOUD_ID:
    print(f"Using Cloud ID: {ELASTIC_CLOUD_ID[:50]}...")
    client = Elasticsearch(
        cloud_id=ELASTIC_CLOUD_ID,
        api_key=ELASTIC_API_KEY,
        request_timeout=30
    )
else:
    print(f"Using URL: {ELASTIC_URL}")
    print(f"Using API key: {ELASTIC_API_KEY[:20]}..." if ELASTIC_API_KEY else "No API key")
    client = Elasticsearch(
        ELASTIC_URL,
        api_key=ELASTIC_API_KEY,
        request_timeout=30,
        verify_certs=True
    )

try:
    # Test ping
    if client.ping():
        print("✓ Ping successful!")
    else:
        print("✗ Ping failed")
        exit(1)
    
    # Try to create a simple test index
    test_index = "test_connection_index"
    print(f"\nTrying to create test index: {test_index}")
    
    # Delete if exists
    if client.indices.exists(index=test_index):
        client.indices.delete(index=test_index)
        print(f"  Deleted existing index")
    
    # Create simple index (without shards/replicas for serverless)
    client.indices.create(
        index=test_index,
        mappings={"properties": {"test_field": {"type": "text"}}}
    )
    print(f"✓ Successfully created index: {test_index}")
    
    # List indices
    indices = client.cat.indices(format="json")
    print(f"\n✓ Available indices:")
    for idx in indices:
        print(f"  - {idx['index']}")
    
    # Cleanup
    client.indices.delete(index=test_index)
    print(f"\n✓ Cleaned up test index")
    print("\n✓✓✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
    import traceback
    traceback.print_exc()
