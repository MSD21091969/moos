"""Integration tests for VectorDbServer (Numpy Implementation)."""

import asyncio
import shutil
import sys
from pathlib import Path
import pytest
import numpy as np

# Add project root and server directories to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_DB_SERVER_DIR = PROJECT_ROOT / "ColliderVectorDbServer"
GRAPH_TOOL_SERVER_DIR = PROJECT_ROOT / "ColliderGraphToolServer"

sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "proto"))
sys.path.append(str(VECTOR_DB_SERVER_DIR))
sys.path.append(str(GRAPH_TOOL_SERVER_DIR))

# Import VectorStore from VectorDbServer
from ColliderVectorDbServer.src.core.vector_store import VectorStore

TEST_DB_DIR = "./test_vector_data"

@pytest.fixture
def clean_db():
    # Setup
    if Path(TEST_DB_DIR).exists():
        shutil.rmtree(TEST_DB_DIR)
    
    yield TEST_DB_DIR
    
    # Teardown
    if Path(TEST_DB_DIR).exists():
        shutil.rmtree(TEST_DB_DIR)

@pytest.mark.asyncio
async def test_vector_store_indexing(clean_db):
    store = VectorStore(persist_directory=clean_db)
    
    # Test Indexing
    success = store.index_tool_full(
        tool_name="test-tool",
        description="A test tool",
        origin_node_id="node-1",
        owner_user_id="user-1",
        params_schema_json="{}"
    )
    
    assert success is True
    assert len(store.metadata) == 1
    assert store.vectors is not None
    assert store.vectors.shape[0] == 1

@pytest.mark.asyncio
async def test_vector_store_searching(clean_db):
    store = VectorStore(persist_directory=clean_db)
    
    # Index some tools
    store.index_tool_full("python", "Programming language", "n1", "u1", "{}")
    store.index_tool_full("banana", "A yellow fruit", "n2", "u1", "{}")
    
    # Search for "programming"
    results = store.search_tools("programming", limit=1)
    
    assert len(results) == 1
    assert results[0]["tool_name"] == "python"
    assert results[0]["score"] > 0.2 # Should be higher now

    # Search for "fruit"
    results = store.search_tools("fruit", limit=1)
    assert len(results) == 1
    assert results[0]["tool_name"] == "banana"

@pytest.mark.asyncio
async def test_vector_store_deletion(clean_db):
    store = VectorStore(persist_directory=clean_db)
    
    store.index_tool_full("t1", "desc", "n1", "u1", "{}")
    assert len(store.metadata) == 1
    
    # Delete match
    success = store.delete_tool("t1", origin_node_id="n1")
    assert success is True
    assert len(store.metadata) == 0
    assert store.vectors is None
    
    # Delete logic check
    store.index_tool_full("t2", "desc", "n1", "u1", "{}")
    store.index_tool_full("t3", "desc", "n1", "u1", "{}")
    assert len(store.metadata) == 2
    
    store.delete_tool("t2", origin_node_id="n1")
    assert len(store.metadata) == 1
    assert store.metadata[0]["tool_name"] == "t3"

@pytest.mark.asyncio
async def test_persistence(clean_db):
    # Create and save
    store = VectorStore(persist_directory=clean_db)
    store.index_tool_full("p1", "persistence test", "n1", "u1", "{}")
    
    # Reload new instance
    store2 = VectorStore(persist_directory=clean_db)
    assert len(store2.metadata) == 1
    assert store2.metadata[0]["tool_name"] == "p1"
    assert store2.vectors is not None
    assert store2.vectors.shape[0] == 1
