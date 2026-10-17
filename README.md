# Occo AI - Human-in-the-Loop Steerable RAG Framework

## Quickstart (Reviewer Execution Guide - Docker)

This repository is fully containerized. Manual installation of Python, Node.js, or Neo4j is not required to evaluate this artifact.

**Prerequisites:**
Ensure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed and running on your machine.

**Step 1: Clone the repository**

```bash
git clone [https://github.com/](https://github.com/)[your-github-username]/unicetra-neuro-adaptive.git
cd unicetra-neuro-adaptive

```

**Step 2: Build and deploy the system**

```bash
docker-compose up --build

```

_(Note: The initial build will execute environment downloads and dependency resolution)._

**Step 3: Access the applications**
Once the terminal indicates that the containers are running, navigate to the following endpoints:

- **Occo AI Visual Trust Layer (Frontend):** [http://localhost:5173](http://localhost:5173)
- **Occo Middleware API (Backend Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Neo4j Graph Database Browser:** [http://localhost:7474](http://localhost:7474) _(Username: `neo4j` | Password: `password`)_

---

## Manual Local Setup (Development Environment)

For active development or ablation testing, the system can be executed locally bypassing the Docker containers.

**1. Backend Execution (FastAPI)**
Open Terminal 1:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload

```

**2. Frontend Execution (Svelte)**
Open Terminal 2:

```powershell
cd frontend
npm run dev

```

```

```
