from fastapi import APIRouter
from datetime import datetime
from app.core.dependencies import get_agent
import json

router = APIRouter(tags=["Health"])

@router.get("/", summary="API Root", description="Welcome endpoint with API information and documentation links")
async def root():
    """
    Welcome to the AICOS AI Assistant API.
    
    This endpoint provides information about the API and links to documentation.
    """
    return {
        "message": "AICOS AI Assistant API",
        "version": "2.0.0",
        "status": "active",
        "documentation": {
            "interactive": "/docs",
            "alternative": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "main_endpoints": {
            "health_check": "/health",
            "content_generation": "/content/generate",
            "ask_question": "/api/ask-question",
            "generate_affirmations": "/generate-affirmations",
            "create_visual_post": "/create-visual-post",
            "instagram_posts": "/instagram-posts",
            "workflows": "/api/workflows"
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "aicos-backend",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/qa-health")
async def qa_health():
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        return {"status": "error", "message": "QA Agent not initialized"}
    
    try:
        # Check if agent is initialized without executing it
        has_knowledge = hasattr(qa_agent, 'vector_store') and qa_agent.vector_store is not None
        has_documents = hasattr(qa_agent, 'documents') and qa_agent.documents is not None
        
        return {
            "status": "healthy",
            "knowledge_loaded": has_knowledge and has_documents,
            "message": "QA Agent is initialized and ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "knowledge_loaded": False
        }

@router.get("/knowledge-overview")
async def knowledge_overview():
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        return {"status": "error", "message": "QA Agent not initialized"}
    
    try:
        # Get overview of loaded knowledge
        overview = qa_agent.get_knowledge_overview()
        return {
            "status": "success",
            "knowledge_overview": overview,
            "total_documents": len(qa_agent.documents) if hasattr(qa_agent, 'documents') else 0
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }