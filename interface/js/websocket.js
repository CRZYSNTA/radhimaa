/**
 * JARVIS V4 WebSocket Bridge Client
 * Auto-reconnecting client for state, theme, audio, and TV command synchronization.
 */

class JarvisWebSocketClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectTimer = null;
        this.reconnectInterval = 2500;
        this.portsToTry = [8000, 8765];
        this.currentPortIndex = 0;
        this.handlers = new Map();
        
        // Listeners for UI notification
        this.onConnectionChange = null;

        this.initConnection();
    }

    getWebSocketUrl() {
        // If served from an HTTP server, prioritize its host & port
        if (window.location.protocol.startsWith("http") && window.location.port) {
            const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
            return `${proto}//${window.location.hostname}:${window.location.port}/ws/hologram`;
        }
        
        // Standalone or local file:// environment: rotate through default ports
        const port = this.portsToTry[this.currentPortIndex];
        return `ws://127.0.0.1:${port}/ws/hologram`;
    }

    initConnection() {
        if (this.socket) {
            try { this.socket.close(); } catch (e) {}
        }

        const url = this.getWebSocketUrl();
        console.log(`[WebSocket] Connecting to JARVIS backend at ${url}...`);

        try {
            this.socket = new WebSocket(url);
        } catch (e) {
            this.handleDisconnect();
            return;
        }

        this.socket.onopen = () => {
            console.log("[WebSocket] Connection established with JARVIS backend.");
            this.isConnected = true;
            if (this.onConnectionChange) this.onConnectionChange(true);
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.routeEvent(data);
            } catch (err) {
                // Non-json message or plain text
                console.log("[WebSocket] Received text:", event.data);
            }
        };

        this.socket.onclose = () => {
            this.handleDisconnect();
        };

        this.socket.onerror = (err) => {
            console.warn("[WebSocket] Socket error:", err);
            this.socket.close();
        };
    }

    handleDisconnect() {
        if (this.isConnected) {
            console.warn("[WebSocket] Disconnected from JARVIS backend.");
        }
        this.isConnected = false;
        if (this.onConnectionChange) this.onConnectionChange(false);

        if (!this.reconnectTimer) {
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                // Switch port candidate for next attempt if local
                if (!window.location.port) {
                    this.currentPortIndex = (this.currentPortIndex + 1) % this.portsToTry.length;
                }
                this.initConnection();
            }, this.reconnectInterval);
        }
    }

    routeEvent(data) {
        const eventType = data.event || data.type;
        if (!eventType) return;

        switch (eventType) {
            case "state_change":
                if (window.StateManager) {
                    window.StateManager.setState(data.state, data.details || "");
                }
                break;

            case "theme_change":
            case "theme":
                if (window.ThemeEngine) {
                    const themeVal = data.color || data.theme || "orange";
                    window.ThemeEngine.setTheme(themeVal);
                }
                break;

            case "audio_level":
                if (window.AudioEngine && typeof data.level === "number") {
                    window.AudioEngine.setBackendLevel(data.level);
                }
                break;

            case "assistant_text":
                if (window.HUDManager) {
                    window.HUDManager.showAssistantText(data.text);
                }
                break;

            case "command":
                if (window.HUDManager) {
                    window.HUDManager.showCommand(data.command, data.details);
                }
                if (window.StateManager) {
                    window.StateManager.setState("EXECUTING", `COMMAND: ${data.command}`);
                }
                break;

            case "system_status":
                if (window.HUDManager) {
                    window.HUDManager.updateSystemTelemetry(data.cpu, data.ram, data.network);
                }
                break;

            case "tv_status":
                if (window.HUDManager) {
                    window.HUDManager.showTvStatus(data.action, data.details);
                }
                break;

            case "init_sync":
                if (window.StateManager && data.state) window.StateManager.setState(data.state);
                if (window.ThemeEngine && data.theme) window.ThemeEngine.setTheme(data.theme);
                if (window.HUDManager && data.system) {
                    window.HUDManager.updateSystemTelemetry(data.system.cpu, data.system.ram, data.system.network);
                }
                break;

            default:
                break;
        }

        // Trigger custom handlers if any
        if (this.handlers.has(eventType)) {
            for (const cb of this.handlers.get(eventType)) {
                cb(data);
            }
        }
    }

    send(eventType, payload = {}) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const data = Object.assign({ event: eventType }, payload);
            this.socket.send(JSON.stringify(data));
        }
    }

    on(eventType, callback) {
        if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, []);
        }
        this.handlers.get(eventType).push(callback);
    }
}

window.JarvisWS = new JarvisWebSocketClient();
