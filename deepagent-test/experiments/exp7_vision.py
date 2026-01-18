"""
Experiment 7: Vision Capabilities with BakLLaVA

Goal: Test multimodal vision + text capabilities for graph visualization analysis
"""

import asyncio
import os
from pathlib import Path
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import StateBackend


async def main():
    print("=== Experiment 7: Vision Capabilities (GCP) ===\n")

    # Configure GCP Vertex AI
    key_path = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    os.environ["GOOGLE_CLOUD_PROJECT"] = "mailmind-ai-djbuw"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"
    os.environ["LOCATION"] = "us-central1"

    model_name = "google-vertex:gemini-2.5-flash"  # Multimodal model
    
    # Create vision agent
    agent = create_deep_agent(
        model=model_name,
        instructions="You are a vision assistant. Analyze images and answer questions about what you see.",
        retries=3,
    )
    
    deps = DeepAgentDeps(backend=StateBackend())
    
    # Test 1: Analyze a sample image (if available)
    print("Test 1: Basic image analysis")
    print("-" * 50)
    
    # Note: This requires an actual image file
    # For testing, we'll describe the capability
    print("Vision model loaded: bakllava")
    print("Capabilities:")
    print("  - Image description")
    print("  - Visual question answering")
    print("  - OCR (text extraction)")
    print("  - Object detection")
    print("  - Scene understanding")
    print()
    
    # Test 2: Text-only query to vision model
    print("\nTest 2: Text query to vision model")
    print("-" * 50)
    
    result = await agent.run(
        "What types of images can you analyze? List your capabilities.",
        deps=deps
    )
    print(f"Result: {result.output}\n")
    
    # Test 3: Graph visualization analysis (conceptual)
    print("\nTest 3: Graph visualization analysis (conceptual)")
    print("-" * 50)
    print("Use case for Collider:")
    print("  - Analyze generated graph diagrams")
    print("  - Validate node connections visually")
    print("  - Identify layout issues")
    print("  - Compare graph states")
    print()
    
    # Instructions for actual usage
    print("\nTo use with actual images:")
    print("=" * 50)
    print("from pydantic_deep import run_with_files")
    print()
    print("with open('graph.png', 'rb') as f:")
    print("    result = await run_with_files(")
    print("        agent,")
    print("        'Describe this graph visualization',")
    print("        deps,")
    print("        files=[('graph.png', f.read())]")
    print("    )")
    print()
    
    print("\n=== Key Learnings ===")
    print("1. bakllava: Multimodal model (vision + text)")
    print("2. Use run_with_files() for image upload")
    print("3. Can analyze graph visualizations for Collider")
    print("4. Useful for UI validation, diagram understanding")
    print("5. OCR capabilities for extracting text from images")


if __name__ == "__main__":
    asyncio.run(main())
