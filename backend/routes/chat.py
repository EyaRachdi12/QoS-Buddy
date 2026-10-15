"""Agent 1: Chat routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from core.schemas import ChatRequest, ChatResponse
from routes.deps import get_agent1, get_current_user_optional

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _user=Depends(get_current_user_optional)):
    agent1 = get_agent1()
    if not agent1:
        raise HTTPException(status_code=503, detail="Agent 1 (Chatbot) not available")

    try:
        result = agent1.query(
            request.message,
            include_live_insights=request.include_live_insights,
            conversation_id=request.conversation_id,
        )
        return ChatResponse(
            answer=result["answer"],
            context=result["context"],
            success=result["success"],
            timestamp=datetime.now().isoformat(),
            intent=result.get("intent"),
            confidence=result.get("confidence"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
