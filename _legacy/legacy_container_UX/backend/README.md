# My Tiny Data Collider - Backend

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688)
![License](https://img.shields.io/badge/license-MIT-green)

AI-powered data workbench backend built on FastAPI, PydanticAI, and Firestore. This service powers the "My Tiny Data Collider" application, handling AI agent orchestration, session management, and tool execution.

## Features
- **Universal Object Model (UOM):** Recursive container-based architecture.
- **AI Orchestration:** PydanticAI integration for agentic workflows.
- **Real-time State:** Redis-backed state management.
- **Cloud Native:** Google Cloud Run & Firestore ready.
- **MCP Support:** Model Context Protocol implementation.

## Installation

`ash
# Install dependencies
pip install -r requirements.txt
`

## Usage

`ash
# Start development server
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
`

## Configuration
Create a \.env\ file with the following keys:
- \ENVIRONMENT\
- \FIRESTORE_PROJECT_ID\
- \REDIS_URL\

## Contributing
See project guidelines.

## License
MIT License
