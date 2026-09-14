/* JARVIS V4 WebSocket Client & Signal Bus Bridge */
(function(window) {
  "use strict";

  class SignalBridge {
    constructor() {
      this.ws = null;
      this.connected = false;
      this.reconnectTimer = null;
      this.endpoints = [
        "ws://localhost:8000/ws/hologram",
        "ws://localhost:8765"
      ];
      this.endpointIdx = 0;

      this.initWebSocket();
    }

    initWebSocket() {
      const url = this.endpoints[this.endpointIdx];
      try {
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this.connected = true;
          if (window.JarvisHud) {
            window.JarvisHud.setTelemetry(undefined, undefined, "ONLINE [WS]");
          }
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (e) {
            console.warn("Invalid WS JSON:", e);
          }
        };

        this.ws.onclose = () => {
          this.connected = false;
          this.scheduleReconnect();
        };

        this.ws.onerror = () => {
          this.connected = false;
          try { this.ws.close(); } catch (e) {}
        };
      } catch (err) {
        this.scheduleReconnect();
      }
    }

    scheduleReconnect() {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => {
        this.endpointIdx = (this.endpointIdx + 1) % this.endpoints.length;
        this.initWebSocket();
      }, 5000);
    }

    handleMessage(data) {
      if (!data || !data.event) return;

      switch (data.event) {
        case "state_change":
          if (window.JarvisState) {
            window.JarvisState.setState(data.state, data.details);
          }
          break;

        case "theme_change":
          if (window.JarvisThemes) {
            window.JarvisThemes.setTheme(data.theme);
          }
          break;

        case "audio_level":
          if (window.JarvisAudio) {
            window.JarvisAudio.setLevel(data.level);
          }
          break;

        case "assistant_text":
          if (window.JarvisHud) {
            window.JarvisHud.setSubtitle(data.text);
          }
          break;

        case "command":
          if (window.JarvisHud) {
            window.JarvisHud.setSubtitle(`CMD EXEC: ${data.command}`);
          }
          if (window.JarvisState) {
            window.JarvisState.setState("EXECUTING", `COMMAND: ${data.command}`);
          }
          break;

        case "system_status":
          if (window.JarvisHud) {
            window.JarvisHud.setTelemetry(data.cpu, data.ram, data.network);
          }
          break;

        case "tv_status":
          if (window.JarvisHud) {
            window.JarvisHud.setSubtitle(`TV // ${data.action} ${data.details && data.details.app ? data.details.app : ''}`);
          }
          break;
      }
    }

    // Bridge with ai-visualizer core AV object
    syncWithAV(dt) {
      if (typeof AV === "undefined") return;

      AV.tick(dt * 1000);

      // Only let AV override state if external WS is not sending custom states
      if (!this.connected) {
        if (window.JarvisHud) {
          const cpu = (AV.telemetry && AV.telemetry.cpu != null) ? AV.telemetry.cpu : undefined;
          const ram = (AV.telemetry && AV.telemetry.ram != null) ? AV.telemetry.ram : undefined;
          window.JarvisHud.setTelemetry(cpu, ram, "ONLINE [BUS]");
          if (AV.name) window.JarvisHud.setAgentName(AV.name);
        }

        if (AV.alert) {
          window.JarvisState.setState("WARNING", "ALERT SIGNAL ACTIVE");
        } else if (AV.state) {
          const s = AV.state.toUpperCase();
          if (s === "SPEAKING") {
            window.JarvisState.setState("SPEAKING");
          } else if (s === "THINKING") {
            window.JarvisState.setState("PROCESSING");
          } else if (s === "LISTENING") {
            window.JarvisState.setState("LISTENING");
          } else {
            window.JarvisState.setState("IDLE");
          }
        }

        if (window.JarvisAudio) {
          const lvl = AV.state === "listening" ? (AV.micLevel || 0) : (AV.env || AV.level || 0);
          window.JarvisAudio.setLevel(lvl);
          window.JarvisAudio.setSamples(AV.samples);
        }
      }
    }
  }

  window.SignalBridge = SignalBridge;
})(window);
