"""
JARVIS V3.0 - Memory Retrieval & Action Logging
Provides context retrieval, fuzzy fact searching, and audit logging of actions.
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional
from memory.database import get_db

logger = logging.getLogger("JARVIS.Memory.Retrieval")

def search_facts(query: str) -> List[Dict[str, str]]:
    """Search user facts by key or value substring."""
    clean_q = f"%{query.strip().lower()}%"
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, value, category FROM user_facts
                WHERE key LIKE ? OR value LIKE ?
                ORDER BY updated_at DESC
            """, (clean_q, clean_q))
            return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[Retrieval] Error searching facts: {e}")
        return []

def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search both facts and recent conversations for context relevant to a query.
    """
    results: List[Dict[str, Any]] = []

    # 1. Check facts
    matched_facts = search_facts(query)
    for f in matched_facts[:top_k]:
        results.append({
            "type": "fact",
            "key": f["key"],
            "content": f"{f['key']}: {f['value']}"
        })

    # 2. Check conversation history
    clean_q = f"%{query.strip().lower()}%"
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, timestamp FROM conversations
                WHERE content LIKE ?
                ORDER BY id DESC LIMIT ?
            """, (clean_q, top_k))
            for row in cursor.fetchall():
                results.append({
                    "type": "conversation",
                    "role": row["role"],
                    "content": row["content"]
                })
    except Exception as e:
        logger.error(f"[Retrieval] Error querying conversations: {e}")

    return results[:top_k]

def log_action(
    goal: str,
    tool: str,
    params: Dict[str, Any],
    permission: str,
    success: bool,
    error: str = "",
    duration_ms: float = 0.0
) -> None:
    """Audit log of tool execution for verification and replanning."""
    now = time.time()
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO action_logs (timestamp, goal, tool, params, permission, success, error, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now,
                goal,
                tool,
                json.dumps(params) if isinstance(params, (dict, list)) else str(params),
                permission,
                1 if success else 0,
                str(error),
                duration_ms
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"[Retrieval] Error logging action: {e}")

def get_action_logs(limit: int = 10, tool: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent action audit logs."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if tool:
                cursor.execute("""
                    SELECT id, timestamp, goal, tool, params, permission, success, error, duration_ms
                    FROM action_logs WHERE tool = ? ORDER BY id DESC LIMIT ?
                """, (tool, limit))
            else:
                cursor.execute("""
                    SELECT id, timestamp, goal, tool, params, permission, success, error, duration_ms
                    FROM action_logs ORDER BY id DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"[Retrieval] Error fetching action logs: {e}")
        return []
