/* JARVIS V4 Dual-Mirrored Oscilloscope Waveform Canvas */
(function(window) {
  "use strict";

  class WaveformDisplay {
    constructor() {
      this.canvas = document.getElementById("waveform-canvas");
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext("2d");
      this.time = 0;

      this.resize();
      window.addEventListener("resize", () => this.resize());
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      this.width = this.canvas.width = rect.width * (window.devicePixelRatio || 1);
      this.height = this.canvas.height = rect.height * (window.devicePixelRatio || 1);
    }

    render(dt, samples, audioLevel) {
      if (!this.ctx) return;
      this.time += dt;

      const w = this.width;
      const h = this.height;
      const cy = h * 0.5;

      this.ctx.clearRect(0, 0, w, h);

      // Baseline center line
      this.ctx.beginPath();
      this.ctx.strokeStyle = "rgba(255, 122, 0, 0.25)";
      this.ctx.lineWidth = 1;
      this.ctx.moveTo(0, cy);
      this.ctx.lineTo(w, cy);
      this.ctx.stroke();

      const numPoints = 80;
      const themeHex = window.JarvisThemes ? window.JarvisThemes.getHex() : "#ff7a00";

      // Build mirrored waveform paths
      this.ctx.beginPath();
      this.ctx.strokeStyle = themeHex;
      this.ctx.lineWidth = 2;
      this.ctx.shadowBlur = 12;
      this.ctx.shadowColor = themeHex;

      const topPoints = [];
      const botPoints = [];

      for (let i = 0; i <= numPoints; i++) {
        const normX = i / numPoints;
        const x = normX * w;
        
        // Windowed tapering envelope (zeros at edges)
        const envelope = Math.sin(normX * Math.PI);

        let amp = 0;
        if (samples && samples.length) {
          const sampleIdx = Math.floor(normX * (samples.length - 1));
          amp = (samples[sampleIdx] || 0) * (h * 0.45);
        } else {
          // Idle harmonic ripples
          amp = (Math.sin(normX * 12.0 + this.time * 4.0) * 0.5 +
                 Math.sin(normX * 24.0 - this.time * 2.5) * 0.3) * (6.0 + audioLevel * 25.0);
        }

        const yOffset = amp * envelope;
        topPoints.push({ x, y: cy - yOffset });
        botPoints.push({ x, y: cy + yOffset });
      }

      // Draw top half
      this.ctx.moveTo(topPoints[0].x, topPoints[0].y);
      for (let i = 1; i < topPoints.length; i++) {
        this.ctx.lineTo(topPoints[i].x, topPoints[i].y);
      }
      this.ctx.stroke();

      // Draw bottom reflected half
      this.ctx.beginPath();
      this.ctx.moveTo(botPoints[0].x, botPoints[0].y);
      for (let i = 1; i < botPoints.length; i++) {
        this.ctx.lineTo(botPoints[i].x, botPoints[i].y);
      }
      this.ctx.stroke();

      // Fill subtle translucent glow between waves
      this.ctx.shadowBlur = 0;
      this.ctx.fillStyle = "rgba(255, 122, 0, 0.08)";
      this.ctx.beginPath();
      this.ctx.moveTo(topPoints[0].x, topPoints[0].y);
      for (let i = 1; i < topPoints.length; i++) {
        this.ctx.lineTo(topPoints[i].x, topPoints[i].y);
      }
      for (let i = botPoints.length - 1; i >= 0; i--) {
        this.ctx.lineTo(botPoints[i].x, botPoints[i].y);
      }
      this.ctx.closePath();
      this.ctx.fill();
    }
  }

  window.WaveformDisplay = WaveformDisplay;
})(window);
