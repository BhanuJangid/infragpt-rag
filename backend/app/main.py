from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.llm import chat
from app.rag import index
from app.schemas import ChatRequest, ChatResponse, HealthResponse
from app.tools import TOOL_SPECS

app = FastAPI(
    title="InfraGPT",
    description="RAG chatbot for infra ops with mock vCenter / Nutanix tools.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    llm = settings.llm_model if settings.openai_api_key else "mock-offline"
    backend = "pgvector" if settings.database_url else "tfidf-local"
    return HealthResponse(
        status="ok",
        docs_indexed=index.size,
        vector_backend=backend,
        llm=llm,
    )


@app.get("/tools")
def tools() -> dict:
    return {"tools": TOOL_SPECS}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest) -> ChatResponse:
    return chat(req.message, req.history)
