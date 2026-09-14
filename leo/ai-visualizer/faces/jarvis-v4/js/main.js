/* JARVIS V4 Master Animation Loop & System Orchestration */
(function(window) {
  "use strict";

  async function loadShader(path, fallbackId) {
    try {
      const resp = await fetch(path);
      if (resp.ok) {
        return await resp.text();
      }
    } catch (e) {
      // CORS or file:// protocol fallback
    }
    const elem = document.getElementById(fallbackId);
    return elem ? elem.textContent : "";
  }

  async function init() {
    // 1. Initialize AV if available
    if (typeof AV !== "undefined") {
      AV.init({ mic: true });
      AV.ready((a) => {
        document.title = `${a.name} — Holographic Interface`;
        if (window.JarvisHud) {
          window.JarvisHud.setAgentName(a.name);
        }
      });
    }

    // 2. Load Shaders
    const [sphereVert, sphereFrag, particleVert, particleFrag] = await Promise.all([
      loadShader("shaders/sphere.vert", "fallback-sphere-vert"),
      loadShader("shaders/sphere.frag", "fallback-sphere-frag"),
      loadShader("shaders/particle.vert", "fallback-particle-vert"),
      loadShader("shaders/particle.frag", "fallback-particle-frag")
    ]);

    // 3. Instantiate Scene & Layers
    const sceneManager = window.JarvisScene;
    const core = new window.HologramCore(sceneManager.hologramGroup);
    const rings = new window.OrbitalRings(sceneManager.hologramGroup);
    const particles = new window.ParticleCloud(sceneManager.hologramGroup, particleVert, particleFrag);
    const sphere = new window.FracturedSphere(sceneManager.hologramGroup, sphereVert, sphereFrag);
    const arcs = new window.ElectricArcs(sceneManager.hologramGroup);

    // 4. Instantiate 2D HUD & Audio Canvas
    window.JarvisHud = new window.HudManager();
    const waveform = new window.WaveformDisplay();
    const bridge = new window.SignalBridge();

    // Keybindings: 'F' = Fullscreen
    window.addEventListener("keydown", (e) => {
      if (e.key === "f" || e.key === "F") {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      }
    });

    // 5. Master RequestAnimationFrame Loop
    let lastTime = performance.now();

    function animate(now) {
      requestAnimationFrame(animate);

      const dt = Math.min(0.1, (now - lastTime) / 1000);
      lastTime = now;

      // Sync signals (AV & WS)
      bridge.syncWithAV(dt);

      // Update Audio and State
      window.JarvisThemes.update(dt);
      window.JarvisState.update(dt);
      window.JarvisAudio.update(dt);

      const audioLevel = window.JarvisAudio.getLevel();
      const samples = window.JarvisAudio.getSamples();

      // Update 3D Layers
      sceneManager.update(dt);
      core.update(dt, audioLevel);
      rings.update(dt, audioLevel);
      particles.update(dt, audioLevel);
      sphere.update(dt, audioLevel);
      arcs.update(dt, audioLevel);

      // Render 3D Scene
      sceneManager.render();

      // Update 2D Waveform & HUD
      waveform.render(dt, samples, audioLevel);
      window.JarvisHud.update(dt);
    }

    requestAnimationFrame(animate);
  }

  window.addEventListener("DOMContentLoaded", init);
})(window);
