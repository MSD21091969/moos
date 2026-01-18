"""
Minimal test to verify Google GCP (Vertex AI) connectivity
"""

import asyncio
import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel

async def main():
    print("=== Testing GCP Vertex AI Connectivity ===\n")
    
    print("=== Testing GCP Vertex AI Connectivity ===\n")
    
    # Use discovered Service Account Key
    key_path = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    
    # Needs explicit project/location usually
    os.environ["GOOGLE_CLOUD_PROJECT"] = "mailmind-ai-djbuw"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"
    os.environ["LOCATION"] = "us-central1"
    
    print(f"Using credentials from: {key_path}")
    # print(f"Using Application Default Credentials (ADC)")
    print(f"Targeting Project: mailmind-ai-djbuw, Region: us-central1")
    
    # Try 1: Standard string (should work if env configured)
    # print("Attempt 1: Agent('google-vertex:gemini-1.5-flash')")
    # try:
    #     agent = Agent("google-vertex:gemini-1.5-flash")
    #     result = await agent.run("Hello Vertex!")
    #     print(f"✅ SUCCESS! Response: {result.data}\n")
    #     return
    # except Exception as e:
    #     print(f"❌ Failed: {e}\n")

    # Try 3: Versioned model (Likely to work)
    print("Attempt 3: Agent('google-vertex:gemini-2.5-flash')")
    try:
        agent = Agent("google-vertex:gemini-2.5-flash")
        result = await agent.run("Hello Vertex!")
        print(f"✅ SUCCESS! Response: {result.data}\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")

    print("\n=== DEBUG: Listing Available Models ===")
    try:
        from google.genai import Client
        client = Client(vertexai=True, location="us-central1", project="mailmind-ai-djbuw")
        
        # Pager over models
        print("Listing models directly via google-genai Client (Filtering for 'gemini')...")
        pager = client.models.list(config={"page_size": 100}) 
        count = 0
        found = 0
        for model in pager:
             if "gemini" in model.name:
                 print(f"FOUND: {model.name}")
                 found += 1
             count += 1
             if count >= 200: break
        
        if found == 0:
            print("WARNING: No 'gemini' models found in first 200 models!")
             
    except ImportError:
        print("google-genai not installed or import failed.")
    except Exception as e:
        print(f"List Models Failed: {e}")
        

if __name__ == "__main__":
    asyncio.run(main())
