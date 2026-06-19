"""Copilot chat endpoint."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from config import COPILOT_ENABLED
from services import copilot

router = APIRouter(prefix="/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(req: ChatRequest):
    result = copilot.answer(req.question)
    result["backend"] = "claude" if COPILOT_ENABLED else "fallback"
    return result
