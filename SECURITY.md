# 🛡️ JARVIS V3.0 — Security & Trust Model

## 1. Ground-Truth Permission Tiers

In JARVIS V3.0, the LLM is treated as an **untrusted reasoning component**. An AI model cannot escalate permissions by specifying `"permission": "SAFE"` inside its generated JSON plan. All tool authorizations are enforced statically in Python via `core/permissions.py`.

| Permission Level | Description | Example Tools |
| :--- | :--- | :--- |
| **`SAFE`** | Read-only operations, desktop viewing, volume adjustments, web searches, safe app launches. Executed automatically. | `volume_up`, `volume_down`, `get_time`, `get_system_stats`, `take_screenshot`, `analyze_screen`, `read_file` |
| **`CONFIRM`** | Destructive, modifying, or state-altering actions. Requires explicit user prompt or approval callback before execution. | `delete_file`, `write_file`, `close_app` |
| **`BLOCKED`** | High-risk operations that are permanently rejected by security policy. Cannot be overridden. | `run_shell_cmd`, `format_disk`, `modify_system_registry`, arbitrary subprocess execution |

---

## 2. Sandboxed File Operations

To protect the host operating system from arbitrary disk modifications or directory traversal attacks:

1. **Path Traversal Guards**: Any file path containing `..` or attempting relative breakout is immediately rejected with a `BLOCKED` status.
2. **Path Resolution**: All paths are resolved to absolute canonical paths via `pathlib.Path.resolve()`.
3. **Whitelist Root Boundaries**: File operations are strictly confined to predefined safe directories (`config.SAFE_PATHS`):
   - User Downloads folder
   - User Documents folder
   - User Desktop folder
   - The JARVIS application workspace directory
4. Any attempt to write, read, or delete outside these roots results in an immediate permission denial.

---

## 3. Remote Server & Cloud Security

JARVIS provides local and remote API endpoints via `server.py` and `cloud_deployment/main.py`:

- **Loopback Exemption**: Requests originating from `127.0.0.1`, `localhost`, or `::1` are permitted for seamless local UI communication.
- **Remote Fail-Closed**: All remote (non-loopback) incoming traffic is authenticated against `config.AUTH_TOKEN` or `JARVIS_AUTH_TOKEN`. If no authentication token is configured on the server, remote requests **fail closed** with HTTP 403 Forbidden.
- **No Referer Bypass**: Client-controlled `Referer` or `Origin` headers are strictly **never** used for authorization.
- **Dual Token Support**: Remote clients can authenticate via:
  - `X-JARVIS-Token: <token>` HTTP header
  - `Authorization: Bearer <token>` HTTP standard header
  - WebSocket query parameter: `ws://host/ws/chat?token=<token>` or WebSocket handshake headers.
- **WebSocket Protection**: Both `server.py` and `cloud_deployment/main.py` authenticate WebSocket connections before accepting messages. Unauthenticated connections are terminated immediately with status `1008 (Policy Violation)`.
- **No Public Hardcoded Secret**: No default shared secret is bundled in client-delivered HTML/JS dashboards. The web console prompts the user for their token and stores it in session storage.
- **CORS Hardening**: Wildcard origin with credential sharing is disallowed to prevent CSRF exploits.

---

## 4. Input Sanitization & Abuse Prevention

To protect SQLite database integrity, prevent memory exhaustion, and avoid quota drainage on cloud LLM APIs:

- **Message Length Limits**: All incoming text messages across HTTP (`/ask`, `/api/chat`) and WebSockets (`/ws/chat`) are capped at a maximum of **4,000 characters**. Requests exceeding this threshold are rejected immediately with HTTP 400 Bad Request.
- **Rate Limiting**: An in-memory sliding-window rate limiter enforces a threshold of **30 requests per minute per client IP**. Bursts exceeding this rate return HTTP 429 Too Many Requests.

---

## 5. Execution Audit Logging

Every tool execution step is permanently recorded in the local SQLite database (`action_logs` table) with:
- Timestamp
- Goal description
- Tool name and parameter payload
- Authoritative permission applied
- Success status (0 or 1)
- Verifier observation / error message
- Execution duration in milliseconds
