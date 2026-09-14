"""
Integration tests for /v1/chat/stream endpoint and streaming SSE responses.
"""

import json
from fastapi.testclient import TestClient
from server import app


def test_chat_stream_endpoint():
    client = TestClient(app)
    payload = {
        "message": "Hello Jarvis",
        "conversation_id": "stream_test_conv"
    }

    resp = client.post("/v1/chat/stream", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    lines = resp.text.strip().split("\n\n")
    events = []
    for line in lines:
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    assert len(events) > 0
    # Last event should be 'done'
    assert events[-1]["type"] == "done"
    assert "content" in events[-1]
    assert len(events[-1]["content"]) > 0
