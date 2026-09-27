# IntelliAssess

IntelliAssess is an AI-powered assessment platform that handles the entire workflow of question generation, validation, examination, evaluation, and personalized remediation.

## Features
- AI Question Generation (Ollama)
- Offline Question Paper generation (PDF)
- Interactive student examination module
- Answer Evaluation via AI
- Performance Analysis & Remedial Test Generation

## Tech Stack
- Frontend: React, Vite, Tailwind CSS, Zustand
- Backend: FastAPI, Motor (Async MongoDB), Ollama
- Database: MongoDB
- Deployment: Docker, AWS (Target)

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js (for local frontend dev)
- Python 3.10+ (for local backend dev)
- Ollama installed locally with `llama3` model

### Running Locally with Docker
```bash
docker-compose up --build
```

### Local Development
See `/frontend/README.md` and `/backend/README.md` for specific instructions.
