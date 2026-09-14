/* JARVIS V4 9-State Operational Coordinator */
(function(window) {
  "use strict";

  const STATES = {
    BOOTING:    { name: "BOOTING",    theme: "white",  rotSpeed: 0.8, pulseSpeed: 2.0 },
    IDLE:       { name: "IDLE",       theme: "orange", rotSpeed: 0.5, pulseSpeed: 1.2 },
    LISTENING:  { name: "LISTENING",  theme: "cyan",   rotSpeed: 1.2, pulseSpeed: 2.5 },
    PROCESSING: { name: "PROCESSING", theme: "purple", rotSpeed: 2.0, pulseSpeed: 4.0 },
    SPEAKING:   { name: "SPEAKING",   theme: "orange", rotSpeed: 1.5, pulseSpeed: 3.0 }, // Hot glowing orange/electric
    EXECUTING:  { name: "EXECUTING",  theme: "green",  rotSpeed: 1.8, pulseSpeed: 3.5 },
    SUCCESS:    { name: "SUCCESS",    theme: "green",  rotSpeed: 1.0, pulseSpeed: 1.5 },
    WARNING:    { name: "WARNING",    theme: "amber",  rotSpeed: 1.4, pulseSpeed: 4.5 },
    ERROR:      { name: "ERROR",      theme: "red",    rotSpeed: 2.2, pulseSpeed: 6.0 }
  };

  class StateMachine {
    constructor() {
      this.currentState = STATES.IDLE;
      this.previousState = null;
      this.timeInState = 0;
      this.statusText = "SYSTEM ONLINE // STANDBY";
      this.listeners = [];
    }

    setState(stateKey, details = "") {
      const normalized = String(stateKey).toUpperCase().trim();
      let target = STATES[normalized];
      
      // Alias common voice line states
      if (!target) {
        if (normalized === "THINKING") target = STATES.PROCESSING;
        else target = STATES.IDLE;
      }

      if (this.currentState !== target) {
        this.previousState = this.currentState;
        this.currentState = target;
        this.timeInState = 0;
        
        if (window.JarvisThemes) {
          window.JarvisThemes.setTheme(target.theme);
        }

        if (details) {
          this.statusText = details;
        } else {
          this.statusText = `SYSTEM ${target.name} // CORE ACTIVE`;
        }

        this.notify(target);
      }
    }

    onChange(callback) {
      this.listeners.push(callback);
    }

    notify(state) {
      this.listeners.forEach(cb => cb(state));
    }

    update(dt) {
      this.timeInState += dt;
      if (this.currentState === STATES.SUCCESS && this.timeInState > 3.5) {
        this.setState("IDLE");
      }
    }

    get state() {
      return this.currentState.name;
    }

    get rotMultiplier() {
      return this.currentState.rotSpeed;
    }

    get pulseMultiplier() {
      return this.currentState.pulseSpeed;
    }
  }

  window.JarvisState = new StateMachine();
})(window);
