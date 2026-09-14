/* JARVIS V4 Audio Processor & Level Smoother */
(function(window) {
  "use strict";

  class AudioProcessor {
    constructor() {
      this.level = 0.0;
      this.targetLevel = 0.0;
      this.samples = new Float32Array(64);
      this.peakDecay = 0.96;
    }

    setLevel(target) {
      this.targetLevel = Math.max(0.0, Math.min(1.0, target));
    }

    setSamples(rawSamples) {
      if (rawSamples && rawSamples.length) {
        const count = Math.min(64, rawSamples.length);
        for (let i = 0; i < count; i++) {
          this.samples[i] = rawSamples[i];
        }
      }
    }

    update(dt) {
      // Attack fast, decay slower
      const tau = this.targetLevel > this.level ? 0.06 : 0.28;
      this.level += (this.targetLevel - this.level) * Math.min(1.0, dt / tau);

      // Natural decay if no updates
      this.targetLevel *= Math.pow(this.peakDecay, dt * 60);
    }

    getLevel() {
      return this.level;
    }

    getSamples() {
      return this.samples;
    }
  }

  window.JarvisAudio = new AudioProcessor();
})(window);
