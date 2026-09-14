# JARVIS V4 — Observability, Live Diagnostics & Preflight Architecture

This document specifies the operational telemetry, runtime diagnostics, request tracing, and preflight verification systems implemented in **JARVIS V4 Phase 2**.

---

## 1. Architectural Philosophy

Phase 2 introduces deep operational transparency across JARVIS while enforcing two non-negotiable principles:
1. **Zero Secret Leakage:** Diagnostics and traces must NEVER leak API keys, tokens, passwords, session secrets, private memories, or raw visual frame data.
2. **Deterministic Truthfulness:** Component statuses must reflect actual hardware and network availability. If a camera is unplugged or an AI model API key is unconfigured, the system reports `WARN` or `FAIL`, never simulated health.

---

## 2. Health vs. Diagnostics Separation

| Endpoint | Purpose | Scope | Auth/Origin |
| :--- | :--- | :--- | :--- |
| `GET /health` | Liveness & basic readiness check | Minimal JSON (`{"status": "online", "version": "4.0.0", "instance_id": "..."}`) | Fast, low-overhead loopback check |
| `GET /api/diagnostics` | Full operational telemetry | Subsystem states, performance metrics, trace summaries, error categorization | Loopback & authenticated origin protected |

---

## 3. Diagnostic Payload Specification (`/api/diagnostics`)

The response returns a structured diagnostic tree:

```json
{
  "server": {
    "instance_id": "inst_7b9a1f2c",
    "version": "4.0.0",
    "uptime_seconds": 1245.8,
    "start_time": "2026-09-13T13:25:00Z",
    "host": "127.0.0.1",
    "port": 8000,
    "active_connections": 2
  },
  "ai": {
    "active_provider": "gemini",
    "available": true,
    "api_key_configured": true,
    "last_latency_ms": 320.5
  },
  "memory": {
    "db_healthy": true,
    "db_path": "jarvis_memory.db",
    "user_profiles_count": 1,
    "total_memories": 42
  },
  "voice": {
    "input_mode": "local",
    "tts_engine": "edge-tts",
    "is_listening": false,
    "mic_available": true
  },
  "vision": {
    "camera_available": true,
    "active_captures": 0,
    "last_capture_status": "idle"
  },
  "executor": {
    "registered_tools_count": 14,
    "registered_tools": ["read_file", "write_file", "search_web"],
    "active_executions": 0
  },
  "websocket": {
    "hologram_subscribers": 1,
    "total_broadcasts": 150
  },
  "mobile": {
    "pairing_mode_active": false,
    "paired_devices_count": 0,
    "connected_devices": []
  },
  "recent_errors": [],
  "recent_traces": []
}
```

---

## 4. Error Categorization & Sanitization (`core/errors.py`)

Every error captured in the runtime is classified under an authoritative `ErrorCategory`:
- `AUTHENTICATION_ERROR`
- `AUTHORIZATION_ERROR`
- `TOOL_VALIDATION_ERROR`
- `TOOL_EXECUTION_ERROR`
- `VERIFICATION_ERROR`
- `AI_PROVIDER_ERROR`
- `AI_MODEL_ERROR`
- `MEMORY_ERROR`
- `VISION_CAPTURE_ERROR`
- `VOICE_ERROR`
- `NETWORK_ERROR`
- `TIMEOUT_ERROR`
- `INTERNAL_ERROR`

### Sanitization Rules
The `ErrorTracker` filters all messages and metadata through regex and token matching to redact:
- High-entropy tokens and API keys (e.g. `AIza...`, `sk-...`)
- Authorization headers (`Bearer ...`)
- Passwords and private memory values
- Secret file paths (`.env`, `id_rsa`, `shadow`)

---

## 5. Request & Operation Tracing (`core/tracing.py`)

A unified `TraceManager` tracks end-to-end operation flows using unique correlation IDs:
- **Trace Spans:** Each phase (`request_received`, `intent_resolved`, `plan_created`, `tool_validation`, `tool_permission_check`, `tool_execution`, `tool_verification`, `ai_generation`) records:
  - `name`: Name of the phase
  - `start_time` / `end_time`
  - `duration_ms`
  - `status`: `"ok"` or `"error"`
  - `metadata`: Sanitized contextual details
- **Ring Buffer:** Retains the last 50 operation traces in memory for real-time inspection without unbounded memory growth.

---

## 6. Live Preflight Verification Script (`preflight.py`)

The preflight tool validates a live, running JARVIS instance before mission-critical use:

```bash
# Run against local running server
python preflight.py --url http://127.0.0.1:8000

# JSON output mode for CI/automation
python preflight.py --url http://127.0.0.1:8000 --json
```

### PASS / WARN / FAIL Semantics
- **PASS**: Subsystem is fully operational and healthy.
- **WARN**: Non-blocking issue (e.g., webcam not plugged in, mobile pairing idle, fallback voice engine active). Preflight exits with status code `0`.
- **FAIL**: Critical subsystem broken (e.g., server unreachable, memory database locked or corrupted, security boundary violated, registered tools empty). Preflight exits with status code `1`.

### Non-Destructive Memory Probe
Preflight tests the memory pipeline by:
1. Writing a probe entry with an ephemeral key (`__preflight_probe_<timestamp>`)
2. Reading and validating the probe entry
3. Deleting the probe entry immediately
4. Leaving zero residual data in `jarvis_memory.db`

---

## 7. UI Diagnostics Surface

A live diagnostic modal is integrated into the Desktop HUD (`interface/index.html`):
- Clickable `DIAGNOSTICS` status pill in the top header.
- Displays real-time subsystem state (Server, AI, Memory, Voice, Vision, Tools).
- Displays active correlation ID, latency, and uptime.
- Inspects recent errors and recent execution traces on demand.
- Updates in real-time via WebSocket and polling.
