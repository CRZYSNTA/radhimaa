/**
 * JARVIS V4 Cinematic HUD Subsystem
 * Manages corner framing brackets, top telemetry bar, rotating gyro dial widget,
 * real-time system stats (CPU/RAM/Network), AI assistant speech subtitles,
 * and Smart TV command visualization.
 */

class HUDManager {
    constructor() {
        this.timeEl = null;
        this.stateBadgeEl = null;
        this.stateDetailEl = null;
        this.cpuEl = null;
        this.ramEl = null;
        this.netEl = null;
        this.commandBoxEl = null;
        this.commandTextEl = null;
        this.assistantBoxEl = null;
        this.assistantTextEl = null;
        this.tvBannerEl = null;
        this.tvActionEl = null;
        this.tvDetailEl = null;
        this.gyroDialEl = null;
        this.fpsEl = null;
        
        this.commandTimeout = null;
        this.tvTimeout = null;
        this.assistantTimeout = null;
        this.gyroAngle = 0;
    }

    init() {
        this.timeEl = document.getElementById("hud-clock");
        this.stateBadgeEl = document.getElementById("hud-state-badge");
        this.stateDetailEl = document.getElementById("hud-state-detail");
        this.cpuEl = document.getElementById("hud-cpu");
        this.ramEl = document.getElementById("hud-ram");
        this.netEl = document.getElementById("hud-net");
        this.commandBoxEl = document.getElementById("hud-command-box");
        this.commandTextEl = document.getElementById("hud-command-text");
        this.assistantBoxEl = document.getElementById("hud-assistant-box");
        this.assistantTextEl = document.getElementById("hud-assistant-text");
        this.tvBannerEl = document.getElementById("hud-tv-banner");
        this.tvActionEl = document.getElementById("hud-tv-action");
        this.tvDetailEl = document.getElementById("hud-tv-detail");
        this.gyroDialEl = document.getElementById("hud-gyro-dial");
        this.fpsEl = document.getElementById("hud-fps");

        // Clock update timer
        setInterval(() => this.updateClock(), 1000);
        this.updateClock();

        // Listen for state changes
        if (window.StateManager) {
            window.StateManager.onStateChange((state, data, details) => {
                this.onStateUpdated(state, data, details);
            });
        }

        console.log("[HUD] Cinematic HUD Manager initialized.");
    }

    updateClock() {
        if (!this.timeEl) return;
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, "0");
        const mins = String(now.getMinutes()).padStart(2, "0");
        const secs = String(now.getSeconds()).padStart(2, "0");
        this.timeEl.textContent = `${hrs}:${mins}:${secs}`;
    }

    onStateUpdated(state, data, details) {
        if (this.stateBadgeEl) {
            this.stateBadgeEl.textContent = state;
        }
        if (this.stateDetailEl) {
            this.stateDetailEl.textContent = details || data.statusText;
        }
    }

    updateSystemTelemetry(cpu, ram, network = "CONNECTED") {
        if (this.cpuEl && typeof cpu === "number") {
            this.cpuEl.textContent = `${Math.round(cpu)}%`;
            const fill = document.getElementById("hud-cpu-bar");
            if (fill) fill.style.width = `${Math.min(100, Math.round(cpu))}%`;
        }
        if (this.ramEl && typeof ram === "number") {
            this.ramEl.textContent = `${Math.round(ram)}%`;
            const fill = document.getElementById("hud-ram-bar");
            if (fill) fill.style.width = `${Math.min(100, Math.round(ram))}%`;
        }
        if (this.netEl) {
            this.netEl.textContent = network;
        }
    }

    showCommand(commandName, details = null) {
        if (!this.commandBoxEl || !this.commandTextEl) return;
        
        let displayStr = commandName;
        if (details && typeof details === "object") {
            if (details.action) displayStr += ` » ${details.action}`;
            else if (details.query) displayStr += ` » ${details.query}`;
        }

        this.commandTextEl.textContent = displayStr;
        this.commandBoxEl.classList.add("active");

        if (this.commandTimeout) clearTimeout(this.commandTimeout);
        this.commandTimeout = setTimeout(() => {
            if (this.commandBoxEl) this.commandBoxEl.classList.remove("active");
        }, 4500);
    }

    showAssistantText(text) {
        if (!this.assistantBoxEl || !this.assistantTextEl) return;

        this.assistantTextEl.textContent = text;
        this.assistantBoxEl.classList.add("active");

        if (this.assistantTimeout) clearTimeout(this.assistantTimeout);
        const duration = Math.max(4000, text.length * 70);
        this.assistantTimeout = setTimeout(() => {
            if (this.assistantBoxEl) this.assistantBoxEl.classList.remove("active");
        }, duration);
    }

    showTvStatus(action, details = null) {
        if (!this.tvBannerEl || !this.tvActionEl || !this.tvDetailEl) return;

        let actionText = `TCL ANDROID TV : ${action}`;
        let detailText = "COMMUNICATION LINK: OK";

        if (details) {
            if (action.includes("VOLUME")) {
                actionText = "TCL TV VOLUME CONTROL";
                detailText = details.value ? `LEVEL: ${details.value}` : (action.includes("UP") ? "VOLUME +5" : "VOLUME -5");
            } else if (action.includes("POWER")) {
                actionText = "TCL ANDROID TV POWER";
                detailText = "CONNECTED • POWER: ACTIVE";
            } else if (action.includes("APP") || details.app) {
                const appName = details.app || details.app_name || "STREAMING";
                actionText = "TCL TV APPLICATION LAUNCH";
                detailText = `LAUNCHING: ${appName.toUpperCase()}`;
            }
        }

        this.tvActionEl.textContent = actionText;
        this.tvDetailEl.textContent = detailText;
        this.tvBannerEl.classList.add("active");

        if (this.tvTimeout) clearTimeout(this.tvTimeout);
        this.tvTimeout = setTimeout(() => {
            if (this.tvBannerEl) this.tvBannerEl.classList.remove("active");
        }, 5000);
    }

    update(delta, fps) {
        // Rotate bottom-right gyro dial widget smoothly
        this.gyroAngle += delta * 18.0;
        if (this.gyroDialEl) {
            this.gyroDialEl.style.transform = `rotate(${this.gyroAngle}deg)`;
        }

        // Update FPS monitor
        if (this.fpsEl && fps) {
            this.fpsEl.textContent = `${Math.round(fps)} FPS`;
        }
    }
}

window.HUDManager = new HUDManager();
