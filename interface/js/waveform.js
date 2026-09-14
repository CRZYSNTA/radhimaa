/**
 * JARVIS V4 Real-Time Audio Voice Waveform
 * Renders glowing audio-reactive oscilloscope waveform beneath the central holographic core.
 */

class VoiceWaveform {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.width = 600;
        this.height = 100;
        this.time = 0;
    }

    init(canvasId = "waveform-canvas") {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.warn("[Waveform] Canvas element not found:", canvasId);
            return;
        }
        this.ctx = this.canvas.getContext("2d");
        this.resize();
        window.addEventListener("resize", () => this.resize());
        console.log("[Waveform] Audio waveform visualizer initialized.");
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        this.width = rect.width || 600;
        this.height = rect.height || 100;
        this.canvas.width = this.width * (window.devicePixelRatio || 1);
        this.canvas.height = this.height * (window.devicePixelRatio || 1);
        if (this.ctx) {
            this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        }
    }

    update(delta, audioLevels, themeHex = "#ff7a00") {
        if (!this.ctx || !this.canvas) return;
        this.time += delta;

        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);

        const midY = this.height / 2;
        const amp = audioLevels ? (audioLevels.volume * 40.0 + audioLevels.bass * 25.0) : 0;
        const isVoiceActive = amp > 2.0;

        // Fetch real Web Audio buffer if mic is active
        const timeData = window.AudioEngine ? window.AudioEngine.getWaveformData() : null;

        ctx.save();
        ctx.strokeStyle = themeHex;
        ctx.shadowColor = themeHex;
        ctx.shadowBlur = isVoiceActive ? 16 : 8;
        ctx.lineWidth = isVoiceActive ? 2.5 : 1.5;

        ctx.beginPath();
        const segments = 120;
        const dx = this.width / segments;

        for (let i = 0; i <= segments; i++) {
            const x = i * dx;
            const normX = (i / segments);
            // Windowing envelope: damp edges so waveform tapers cleanly to zero at ends
            const envelope = Math.sin(normX * Math.PI);

            let waveOffset = 0;
            if (timeData && timeData.length > 0) {
                const sampleIdx = Math.floor(normX * (timeData.length - 1));
                const v = (timeData[sampleIdx] - 128) / 128.0;
                waveOffset = v * (amp + 8.0) * envelope;
            } else {
                // Procedural synthesized harmonic wave
                const s1 = Math.sin(normX * 18.0 + this.time * 6.0) * (amp + 4.0);
                const s2 = Math.cos(normX * 32.0 - this.time * 9.0) * (amp * 0.45);
                const idleRipple = Math.sin(normX * 8.0 + this.time * 2.0) * 3.0;
                waveOffset = (s1 + s2 + idleRipple) * envelope;
            }

            const y = midY + waveOffset;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();

        // Mirrored faint secondary reflection wave
        ctx.lineWidth = 1.0;
        ctx.globalAlpha = 0.35;
        ctx.beginPath();
        for (let i = 0; i <= segments; i++) {
            const x = i * dx;
            const normX = (i / segments);
            const envelope = Math.sin(normX * Math.PI);
            const s = Math.sin(normX * 12.0 - this.time * 4.0) * (amp * 0.7 + 2.0) * envelope;
            const y = midY - s;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        ctx.restore();
    }
}

window.VoiceWaveform = new VoiceWaveform();
