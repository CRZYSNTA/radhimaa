"""
JARVIS V4 - Shared Application ChatService
Authoritative application service shared across Web, API (/v1/chat), Desktop, and Mobile clients.
No route or UI component implements its own AI logic.
"""

from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from orchestration.orchestrator import get_orchestrator, JarvisOrchestrator, OrchestratorResponse

logger = logging.getLogger("JARVIS.Orchestration.ChatService")


@dataclass
class ChatRequestDTO:
    message: str
    conversation_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    confirmed: bool = False
    user_id: str = "default_user"


@dataclass
class ChatResponseDTO:
    conversation_id: str
    message_id: str
    status: str
    content: str
    tool_events: List[Dict[str, Any]] = field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "status": self.status,
            "content": self.content,
            "tool_events": self.tool_events,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_payload": self.confirmation_payload
        }


class ChatService:
    def __init__(self, orchestrator: Optional[JarvisOrchestrator] = None):
        self.orchestrator = orchestrator or get_orchestrator()

    async def handle(self, request: ChatRequestDTO) -> ChatResponseDTO:
        msg_id = str(uuid.uuid4())
        res: OrchestratorResponse = await self.orchestrator.run(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            confirmed=request.confirmed
        )

        return ChatResponseDTO(
            conversation_id=res.conversation_id,
            message_id=msg_id,
            status="requires_confirmation" if res.requires_confirmation else ("completed" if res.success else "failed"),
            content=res.content,
            tool_events=res.tool_events,
            requires_confirmation=res.requires_confirmation,
            confirmation_payload=res.confirmation_payload
        )

    async def handle_stream(self, request: ChatRequestDTO):
        """Streams conversation responses and tool events as an async generator."""
        msg_id = str(uuid.uuid4())
        cid = request.conversation_id or str(uuid.uuid4())
        res: OrchestratorResponse = await self.orchestrator.run(
            message=request.message,
            conversation_id=cid,
            user_id=request.user_id,
            confirmed=request.confirmed
        )

        if res.requires_confirmation:
            yield {
                "type": "confirmation_required",
                "conversation_id": cid,
                "message_id": msg_id,
                "tool": (res.confirmation_payload or {}).get("tool", ""),
                "arguments": (res.confirmation_payload or {}).get("arguments", {}),
                "details": res.confirmation_payload
            }
            return

        if res.tool_events:
            yield {
                "type": "tool_events",
                "conversation_id": cid,
                "message_id": msg_id,
                "tool_events": res.tool_events
            }

        # Yield streaming chunks
        words = res.content.split(" ")
        for idx, word in enumerate(words):
            suffix = " " if idx < len(words) - 1 else ""
            yield {
                "type": "chunk",
                "chunk": word + suffix,
                "conversation_id": cid,
                "message_id": msg_id
            }
            await asyncio.sleep(0.01)

        yield {
            "type": "done",
            "conversation_id": cid,
            "message_id": msg_id,
            "content": res.content,
            "status": "completed" if res.success else "failed"
        }


    def handle_sync(self, message: str, conversation_id: Optional[str] = None, confirmed: bool = False) -> str:
        """Synchronous bridge for legacy /ask and desktop callers."""
        req = ChatRequestDTO(message=message, conversation_id=conversation_id, confirmed=confirmed)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async event loop context, run in thread pool or create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    resp = pool.submit(lambda: asyncio.run(self.handle(req))).result()
                    return resp.content
            else:
                resp = loop.run_until_complete(self.handle(req))
                return resp.content
        except RuntimeError:
            resp = asyncio.run(self.handle(req))
            return resp.content


_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
