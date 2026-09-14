/**
 * JARVIS V4 Audio Reactive Subsystem
 * Web Audio API analyser + Backend Audio Level Blending.
 */

class AudioReactivity {
    constructor() {
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.micStream = null;
        this.isMicActive = false;

        // Band levels [0..1]
        this.levels = {
            volume: 0.0,
            bass: 0.0,
            mid: 0.0,
            treble: 0.0,
            average: 0.0
        };

        // Backend-supplied audio level (from TTS / STT via WebSocket)
        this.backendAudioLevel = 0.0;
        this.backendAudioTarget = 0.0;

        // Auto-initialize on first user interaction
        const initAudio = () => {
            if (!this.audioContext) {
                this.initWebAudio();
            }
            window.removeEventListener("click", initAudio);
            window.removeEventListener("keydown", initAudio);
        };
        window.addEventListener("click", initAudio);
        window.addEventListener("keydown", initAudio);
    }

    async initWebAudio() {
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return;

            this.audioContext = new AudioContextClass();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

            // Attempt microphone access
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                try {
                    this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
                    const source = this.audioContext.createMediaStreamSource(this.micStream);
                    source.connect(this.analyser);
                    this.isMicActive = true;
                    console.log("[Audio] Web Audio microphone ingress active.");
                } catch (err) {
                    console.info("[Audio] Microphone permission declined or unavailable. Relying on backend audio stream.");
                }
            }
        } catch (e) {
            console.warn("[Audio] Web Audio initialization notice:", e);
        }
    }

    setBackendLevel(level) {
        this.backendAudioTarget = Math.max(0.0, Math.min(1.0, level));
    }

    update(delta = 0.016) {
        // Smoothly decay backend level
        this.backendAudioLevel += (this.backendAudioTarget - this.backendAudioLevel) * Math.min(1.0, delta * 12.0);
        this.backendAudioTarget *= 0.92; // rapid falloff if no new packets

        let micVol = 0.0;
        let micBass = 0.0;
        let micMid = 0.0;
        let micTreble = 0.0;

        if (this.analyser && this.dataArray && this.audioContext && this.audioContext.state === "running") {
            this.analyser.getByteFrequencyData(this.dataArray);
            const bins = this.dataArray.length; // 128

            // Bass: 0 - 15 bins (~0 to 250Hz)
            let sumBass = 0;
            for (let i = 0; i < 16; i++) sumBass += this.dataArray[i];
            micBass = (sumBass / 16) / 255.0;

            // Mid: 16 - 63 bins (~250Hz to 2000Hz)
            let sumMid = 0;
            for (let i = 16; i < 64; i++) sumMid += this.dataArray[i];
            micMid = (sumMid / 48) / 255.0;

            // Treble: 64 - 127 bins (~2000Hz to 8000Hz)
            let sumTreble = 0;
            for (let i = 64; i < bins; i++) sumTreble += this.dataArray[i];
            micTreble = (sumTreble / (bins - 64)) / 255.0;

            micVol = (micBass * 0.5 + micMid * 0.35 + micTreble * 0.15);
        }

        // Combine Web Audio mic with backend level
        const combinedVol = Math.max(micVol, this.backendAudioLevel);
        const combinedBass = Math.max(micBass, this.backendAudioLevel * 1.1);
        const combinedMid = Math.max(micMid, this.backendAudioLevel * 0.9);
        const combinedTreble = Math.max(micTreble, this.backendAudioLevel * 0.7);

        // Smooth output levels
        const smoothFactor = Math.min(1.0, delta * 10.0);
        this.levels.volume += (combinedVol - this.levels.volume) * smoothFactor;
        this.levels.bass += (combinedBass - this.levels.bass) * smoothFactor;
        this.levels.mid += (combinedMid - this.levels.mid) * smoothFactor;
        this.levels.treble += (combinedTreble - this.levels.treble) * smoothFactor;
        this.levels.average = (this.levels.bass + this.levels.mid + this.levels.treble) / 3.0;

        return this.levels;
    }

    getWaveformData() {
        if (this.analyser && this.audioContext && this.audioContext.state === "running") {
            const timeData = new Uint8Array(this.analyser.fftSize);
            this.analyser.getByteTimeDomainData(timeData);
            return timeData;
        }
        return null;
    }
}

window.AudioEngine = new AudioReactivity();
