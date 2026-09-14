/**
 * JARVIS V4 Dynamic Theme Engine
 * Provides smooth color interpolation (lerp) across visual subsystems.
 */

const THEME_PRESETS = {
    orange: "#ff7a00", // Default JARVIS core
    blue: "#00b7ff",
    cyan: "#00ffff",
    purple: "#a855ff",
    green: "#00ff88",
    red: "#ff3030",
    white: "#ffffff",
    amber: "#ffb300"
};

class ThemeEngine {
    constructor() {
        this.themes = THEME_PRESETS;
        this.currentThemeName = "orange";
        
        // Colors stored as RGB floats [0..1]
        this.currentRgb = { r: 1.0, g: 0.478, b: 0.0 }; // #ff7a00
        this.targetRgb = { r: 1.0, g: 0.478, b: 0.0 };
        this.lerpSpeed = 3.5; // Smooth transition speed
        
        this.listeners = [];
    }

    hexToRgb(hex) {
        let clean = hex.replace("#", "");
        if (clean.length === 3) {
            clean = clean.split("").map(c => c + c).join("");
        }
        const num = parseInt(clean, 16);
        return {
            r: ((num >> 16) & 255) / 255,
            g: ((num >> 8) & 255) / 255,
            b: (num & 255) / 255
        };
    }

    rgbToHex(r, g, b) {
        const toHex = (v) => {
            const hex = Math.round(v * 255).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        };
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    }

    setTheme(nameOrHex) {
        let hex = this.themes[nameOrHex.toLowerCase()] || nameOrHex;
        if (!hex.startsWith("#")) {
            hex = "#" + hex;
        }
        
        try {
            this.targetRgb = this.hexToRgb(hex);
            this.currentThemeName = nameOrHex;
        } catch (e) {
            console.warn("[Theme] Invalid color:", nameOrHex);
        }
    }

    update(delta = 0.016) {
        const factor = Math.min(1.0, delta * this.lerpSpeed);
        this.currentRgb.r += (this.targetRgb.r - this.currentRgb.r) * factor;
        this.currentRgb.g += (this.targetRgb.g - this.currentRgb.g) * factor;
        this.currentRgb.b += (this.targetRgb.b - this.currentRgb.b) * factor;

        const currentHex = this.getHex();
        // Update CSS variables for HUD elements
        document.documentElement.style.setProperty("--jarvis-primary", currentHex);
        document.documentElement.style.setProperty("--jarvis-primary-glow", currentHex + "88");
        document.documentElement.style.setProperty("--jarvis-primary-dim", currentHex + "33");

        for (const cb of this.listeners) {
            cb(this.currentRgb, currentHex);
        }
    }

    getHex() {
        return this.rgbToHex(this.currentRgb.r, this.currentRgb.g, this.currentRgb.b);
    }

    getThreeColor() {
        if (typeof THREE !== "undefined") {
            return new THREE.Color(this.currentRgb.r, this.currentRgb.g, this.currentRgb.b);
        }
        return this.currentRgb;
    }

    onChange(cb) {
        this.listeners.push(cb);
    }
}

window.ThemeEngine = new ThemeEngine();
