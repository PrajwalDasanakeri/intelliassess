# IntelliAssess Architecture

## Core Technologies
- **Frontend**: React (Vite) with TypeScript, Zustand for State Management, Tailwind CSS for Styling.
- **Backend**: Python (FastAPI), Async architecture with Motor for MongoDB interactions.
- **Database**: MongoDB for storing users, assessments, questions, and performance data.
- **LLM Provider**: Ollama (local) via provider abstraction layer to support future integrations.

## Directory Structure
- `/frontend`: React SPA
- `/backend`: FastAPI service
- `docker-compose.yml`: Local infrastructure setup

## Testing
- Pytest for backend testing aiming for >80% coverage on core AI and assessment modules.
- End-to-end scenarios covered in seed scripts and integration tests.

## Cloud Deployment
- Target: AWS ECS (Elastic Container Service) or EKS, with MongoDB Atlas.
