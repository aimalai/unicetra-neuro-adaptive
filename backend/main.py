from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1 import api_router
from app.core.neo4j import neo4j_connector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the Neo4j connection pool
    neo4j_connector.connect()
    yield
    # Shutdown: Cleanly close the driver pool
    neo4j_connector.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="B2B Semantic Firewall and RAG Backend",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS to allow the SvelteKit frontend and Word Add-in to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://localhost:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the API router
app.include_router(api_router, prefix=settings.API_V1_STR)