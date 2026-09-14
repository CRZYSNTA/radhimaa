/* JARVIS V4 Dynamic Theme Engine with continuous linear RGB interpolation */
(function(window) {
  "use strict";

  const PALETTES = {
    orange:  { hex: "#ff7a00", rgb: [1.0, 0.478, 0.0], hot: "#ffe8a0" },
    blue:    { hex: "#00b7ff", rgb: [0.0, 0.718, 1.0], hot: "#d4f1ff" },
    cyan:    { hex: "#00ffff", rgb: [0.0, 1.0, 1.0],   hot: "#e0ffff" },
    purple:  { hex: "#a855ff", rgb: [0.659, 0.333, 1.0], hot: "#f3e8ff" },
    green:   { hex: "#00ff88", rgb: [0.0, 1.0, 0.533], hot: "#e6fffa" },
    red:     { hex: "#ff3030", rgb: [1.0, 0.188, 0.188], hot: "#ffe5e5" },
    white:   { hex: "#ffffff", rgb: [1.0, 1.0, 1.0],   hot: "#ffffff" },
    amber:   { hex: "#ffb300", rgb: [1.0, 0.702, 0.0], hot: "#fff8e1" }
  };

  class ThemeEngine {
    constructor() {
      this.currentThemeName = "orange";
      this.targetTheme = PALETTES.orange;
      this.currentRgb = [1.0, 0.478, 0.0];
      this.currentHex = "#ff7a00";
      this.threeColor = new THREE.Color(this.currentHex);
    }

    setTheme(name) {
      if (PALETTES[name]) {
        this.currentThemeName = name;
        this.targetTheme = PALETTES[name];
      }
    }

    update(dt) {
      const rate = Math.min(1.0, dt * 4.0); // smooth blend
      const tr = this.targetTheme.rgb;
      this.currentRgb[0] += (tr[0] - this.currentRgb[0]) * rate;
      this.currentRgb[1] += (tr[1] - this.currentRgb[1]) * rate;
      this.currentRgb[2] += (tr[2] - this.currentRgb[2]) * rate;

      this.threeColor.setRGB(this.currentRgb[0], this.currentRgb[1], this.currentRgb[2]);
      
      const r = Math.round(this.currentRgb[0] * 255);
      const g = Math.round(this.currentRgb[1] * 255);
      const b = Math.round(this.currentRgb[2] * 255);
      this.currentHex = `rgb(${r}, ${g}, ${b})`;
      
      // Update CSS variables
      document.documentElement.style.setProperty("--jarvis-orange", this.currentHex);
      document.documentElement.style.setProperty("--jarvis-border", `rgba(${r}, ${g}, ${b}, 0.4)`);
    }

    getColor() {
      return this.threeColor;
    }

    getRgbArray() {
      return this.currentRgb;
    }

    getHex() {
      return this.currentHex;
    }
  }

  window.JarvisThemes = new ThemeEngine();
})(window);
