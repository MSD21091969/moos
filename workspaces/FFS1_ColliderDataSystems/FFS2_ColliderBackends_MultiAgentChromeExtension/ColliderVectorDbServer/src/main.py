"""Collider VectorDb Server Entry Point."""

import asyncio
import logging
import sys
from concurrent import futures
from pathlib import Path

# Add project root to path for proto imports
sys.path.append(str(Path(__file__).parent.parent.parent))

import grpc
from grpc_reflection.v1alpha import reflection

from proto import collider_vectordb_pb2
from proto import collider_vectordb_pb2_grpc
from src.handlers.grpc_servicer import ColliderVectorServicer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def serve():
    """Start the gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Register Servicer
    collider_vectordb_pb2_grpc.add_ColliderVectorDbServicer_to_server(
        ColliderVectorServicer(), server
    )
    
    # Enable reflection for debugging tools (e.g. grpcurl)
    SERVICE_NAMES = (
        collider_vectordb_pb2.DESCRIPTOR.services_by_name["ColliderVectorDb"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    # Listen on port 8002
    server.add_insecure_port("[::]:8002")
    logger.info("Collider VectorDb Server starting on port 8002...")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Server stopped.")
        await server.stop(0)

if __name__ == "__main__":
    asyncio.run(serve())
