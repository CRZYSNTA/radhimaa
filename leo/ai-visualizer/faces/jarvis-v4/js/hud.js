/* JARVIS V4 HUD Telemetry, Clock, Gyroscope & Subtitles */
(function(window) {
  "use strict";

  class HudManager {
    constructor() {
      this.elCpu = document.getElementById("hud-cpu-val");
      this.elCpuBar = document.getElementById("hud-cpu-bar");
      this.elMem = document.getElementById("hud-mem-val");
      this.elMemBar = document.getElementById("hud-mem-bar");
      this.elLink = document.getElementById("hud-link-val");
      this.elTime = document.getElementById("hud-clock");
      this.elStateBadge = document.getElementById("hud-state-badge");
      this.elStatusText = document.getElementById("hud-status-text");
      this.elSubtitle = document.getElementById("hud-subtitle");
      this.elAgentName = document.getElementById("hud-agent-name");

      this.cpuVal = 32;
      this.memVal = 44;
      this.time = 0;
      this.subTimer = null;

      this.initEvents();
    }

    initEvents() {
      if (window.JarvisState) {
        window.JarvisState.onChange((state) => {
          if (this.elStateBadge) {
            this.elStateBadge.textContent = state.name;
          }
          if (this.elStatusText) {
            this.elStatusText.textContent = window.JarvisState.statusText;
          }
        });
      }
    }

    setSubtitle(text, duration = 4000) {
      if (!this.elSubtitle) return;
      this.elSubtitle.textContent = text;
      this.elSubtitle.style.opacity = "1";
      clearTimeout(this.subTimer);
      if (duration > 0) {
        this.subTimer = setTimeout(() => {
          this.elSubtitle.style.opacity = "0";
        }, duration);
      }
    }

    setTelemetry(cpu, mem, link) {
      if (cpu !== undefined) {
        this.cpuVal = cpu;
        if (this.elCpu) this.elCpu.textContent = `${cpu}%`;
        if (this.elCpuBar) this.elCpuBar.style.width = `${Math.min(100, Math.max(0, cpu))}%`;
      }
      if (mem !== undefined) {
        this.memVal = mem;
        if (this.elMem) this.elMem.textContent = `${mem}%`;
        if (this.elMemBar) this.elMemBar.style.width = `${Math.min(100, Math.max(0, mem))}%`;
      }
      if (link !== undefined && this.elLink) {
        this.elLink.textContent = link;
      }
    }

    setAgentName(name) {
      if (this.elAgentName) {
        this.elAgentName.textContent = name.toUpperCase();
      }
    }

    update(dt) {
      this.time += dt;

      // Update real-time clock (HH:MM:SS:MS)
      if (this.elTime) {
        const d = new Date();
        const hh = String(d.getHours()).padStart(2, "0");
        const mm = String(d.getMinutes()).padStart(2, "0");
        const ss = String(d.getSeconds()).padStart(2, "0");
        const ms = String(Math.floor(d.getMilliseconds() / 10)).padStart(2, "0");
        this.elTime.textContent = `${hh}:${mm}:${ss}.${ms} T-SYS`;
      }

      // Subtle dynamic simulated telemetry jitter when no backend is pushing
      if (Math.random() < 0.05) {
        const jitterCpu = Math.min(95, Math.max(15, Math.round(this.cpuVal + (Math.random() * 6 - 3))));
        const jitterMem = Math.min(90, Math.max(20, Math.round(this.memVal + (Math.random() * 2 - 1))));
        this.setTelemetry(jitterCpu, jitterMem);
      }
    }
  }

  window.HudManager = HudManager;
})(window);
