"""
Experiment 4: File Uploads and Backends

Goal: Understand file handling, storage backends, and upload workflows
"""

import asyncio
import os
from pathlib import Path
from pydantic_ai_backends import StateBackend, FilesystemBackend
from pydantic_deep import create_deep_agent, DeepAgentDeps, run_with_files


async def main():
    print("=== Experiment 4: File Uploads & Backends (GCP) ===\n")

    # Configure GCP Vertex AI
    key_path = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    os.environ["GOOGLE_CLOUD_PROJECT"] = "mailmind-ai-djbuw"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"
    os.environ["LOCATION"] = "us-central1"

    model_name = "google-vertex:gemini-2.5-flash"
    
    # Test 1: StateBackend (in-memory)
    print("Test 1: StateBackend (in-memory storage)")
    print("-" * 50)
    
    state_backend = StateBackend()
    agent = create_deep_agent(
        model=model_name,
        instructions="You are a file analysis assistant. Help users understand file contents.",
        retries=3,
    )
    
    deps = DeepAgentDeps(backend=state_backend)
    
    # Upload file directly to deps
    test_content = b"apple,banana,cherry\n1,2,3\n4,5,6"
    deps.upload_file("test.csv", test_content)
    
    result1 = await agent.run(
        "What files are available? Tell me about test.csv",
        deps=deps
    )
    print(f"Result: {result1.output}\n")
    
    # Test 2: FilesystemBackend (persistent)
    print("\nTest 2: FilesystemBackend (persistent storage)")
    print("-" * 50)
    
    output_path = Path("./outputs")
    output_path.mkdir(exist_ok=True)
    
    fs_backend = FilesystemBackend(str(output_path))
    deps_fs = DeepAgentDeps(backend=fs_backend)
    
    # Create a test file
    data_file = output_path / "data.txt"
    data_file.write_text("This is test data\nLine 2\nLine 3")
    
    result2 = await agent.run(
        "Read the contents of data.txt and count how many lines it has",
        deps=deps_fs
    )
    print(f"Result: {result2.output}\n")
    
    # Test 3: run_with_files helper
    print("\nTest 3: run_with_files helper (upload during run)")
    print("-" * 50)
    
    csv_data = b"name,age,city\nAlice,30,NYC\nBob,25,LA\nCharlie,35,Chicago"
    
    result3 = await run_with_files(
        agent,
        "Analyze this CSV data and tell me the average age and which cities are represented",
        deps_fs,
        files=[("people.csv", csv_data)]
    )
    print(f"Result: {result3}\n")
    
    # Test 4: Multiple files
    print("\nTest 4: Multiple file upload")
    print("-" * 50)
    
    file1 = b"Project goals:\n- Increase revenue\n- Improve UX"
    file2 = b"Q1 Metrics:\nRevenue: +15%\nUser satisfaction: 4.2/5"
    
    result4 = await run_with_files(
        agent,
        "Compare the goals from goals.txt with the metrics in metrics.txt. Did we meet our objectives?",
        deps_fs,
        files=[
            ("goals.txt", file1),
            ("metrics.txt", file2),
        ]
    )
    print(f"Result: {result4}\n")
    
    print("\n=== Key Learnings ===")
    print("1. StateBackend: In-memory, good for testing, not persistent")
    print("2. FilesystemBackend: Persistent, file-based storage")
    print("3. deps.upload_file(): Direct upload to backend")
    print("4. run_with_files(): Helper for uploading during run")
    print("5. Backend abstraction: Can swap without changing agent code")


if __name__ == "__main__":
    asyncio.run(main())
