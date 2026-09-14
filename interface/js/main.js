/**
 * JARVIS V4 Master Holographic Application Entrypoint
 * Coordinates 3D Scene, Procedural Core, Shaders, Waveform, HUD, and Performance Fallback.
 */

class JarvisHologramApp {
    constructor() {
        this.lastTime = performance.now();
        this.fpsHistory = [];
        this.currentFps = 60;
        this.perfLevel = "high";
        this.isTabVisible = true;
    }

    async start() {
        console.log("==================================================");
        console.log("  JARVIS V4 HOLOGRAPHIC AI INTERFACE STARTING...  ");
        console.log("==================================================");

        // 1. Initialize 2D HUD & Dynamic Themes
        window.HUDManager.init();

        // 2. Initialize Three.js WebGL Scene
        const webglOk = window.SceneManager.init("webgl-container");
        if (!webglOk) {
            console.error("[App] WebGL unavailable. Activating 2D Canvas fallback.");
            this.activate2DFallback();
            return;
        }

        // 3. Initialize Visual Subsystems
        const scene = window.SceneManager.scene;
        window.JarvisCore.init(scene);
        await window.HolographicSphere.init(scene);
        await window.ParticleSystem.init(scene);
        window.OrbitalRings.init(scene);
        window.EnergyArcs.init(scene);

        // 4. Initialize Audio Waveform Visualizer
        window.VoiceWaveform.init("waveform-canvas");

        // 5. Visibility Change Listener (pause/throttle when hidden)
        document.addEventListener("visibilitychange", () => {
            this.isTabVisible = !document.hidden;
            if (this.isTabVisible) this.lastTime = performance.now();
        });

        // 6. Connect WebSocket Status Indicator
        if (window.JarvisWS) {
            window.JarvisWS.onConnectionChange = (connected) => {
                const connBadge = document.getElementById("hud-ws-status");
                if (connBadge) {
                    connBadge.textContent = connected ? "LINK: SYNCHRONIZED" : "LINK: RECONNECTING...";
                    connBadge.className = connected ? "status-tag ok" : "status-tag alert";
                }
            };
        }

        // 7. Start Animation Loop
        requestAnimationFrame((t) => this.loop(t));
    }

    loop(currentTime) {
        requestAnimationFrame((t) => this.loop(t));

        if (!this.isTabVisible) return;

        const delta = Math.min((currentTime - this.lastTime) / 1000, 0.1);
        this.lastTime = currentTime;

        // Performance & FPS Tracking
        const instantFps = 1.0 / (delta || 0.016);
        this.fpsHistory.push(instantFps);
        if (this.fpsHistory.length > 30) this.fpsHistory.shift();
        this.currentFps = this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length;

        // Adaptive performance scaling
        if (this.fpsHistory.length >= 30) {
            if (this.currentFps < 32 && this.perfLevel === "high") {
                this.perfLevel = "medium";
                console.warn("[Performance] Throttling particles to medium profile.");
                window.ParticleSystem.setPerformanceLevel("medium");
            } else if (this.currentFps < 24 && this.perfLevel === "medium") {
                this.perfLevel = "low";
                console.warn("[Performance] Throttling particles to low profile.");
                window.ParticleSystem.setPerformanceLevel("low");
            }
        }

        // Update Theme Interpolation
        window.ThemeEngine.update(delta);
        const themeColor = window.ThemeEngine.getThreeColor();
        const themeHex = window.ThemeEngine.getHex();

        // Update Audio Ingress & Reactivity
        const audioLevels = window.AudioEngine.update(delta);

        // Fetch Active State Data
        const stateData = window.StateManager.stateData;

        // Update 3D Visual Objects
        window.JarvisCore.update(delta, stateData, themeColor, audioLevels);
        window.HolographicSphere.update(delta, stateData, themeColor, audioLevels);
        window.ParticleSystem.update(delta, stateData, themeColor, audioLevels);
        window.OrbitalRings.update(delta, stateData, themeColor, audioLevels);
        window.EnergyArcs.update(delta, stateData, themeColor, audioLevels);

        // Render WebGL Frame
        window.SceneManager.render();

        // Update 2D Waveform Canvas
        window.VoiceWaveform.update(delta, audioLevels, themeHex);

        // Update HUD
        window.HUDManager.update(delta, this.currentFps);
    }

    activate2DFallback() {
        const fallbackContainer = document.getElementById("fallback-container");
        if (fallbackContainer) fallbackContainer.style.display = "flex";
        
        const statusTag = document.getElementById("hud-ws-status");
        if (statusTag) statusTag.textContent = "MODE: 2D FALLBACK";
    }
}

function bootJarvisApp() {
    if (window._jarvisAppStarted) return;
    window._jarvisAppStarted = true;
    const app = new JarvisHologramApp();
    window.JarvisApp = app;
    app.start();
}

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", bootJarvisApp);
} else {
    bootJarvisApp();
}
