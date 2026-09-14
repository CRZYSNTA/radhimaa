/**
 * JARVIS V4 Central State Manager
 * Coordinates behavior, speeds, and transitions across visual subsystems.
 */

const JARVIS_STATES = {
    BOOTING: {
        theme: "cyan",
        pulseSpeed: 4.0,
        rotationSpeed: 2.0,
        particleActivity: 1.5,
        statusText: "INITIALIZING QUANTUM CORE..."
    },
    IDLE: {
        theme: "orange",
        pulseSpeed: 1.0,
        rotationSpeed: 0.6,
        particleActivity: 0.8,
        statusText: "SYSTEMS ONLINE — STANDING BY"
    },
    LISTENING: {
        theme: "cyan",
        pulseSpeed: 2.2,
        rotationSpeed: 1.2,
        particleActivity: 1.4,
        statusText: "VOICE INGRESS ACTIVE — LISTENING..."
    },
    TRANSCRIBING: {
        theme: "purple",
        pulseSpeed: 3.2,
        rotationSpeed: 2.5,
        particleActivity: 1.8,
        statusText: "TRANSCRIBING ACOUSTIC STREAM..."
    },
    THINKING: {
        theme: "cyan",
        pulseSpeed: 3.5,
        rotationSpeed: 2.8,
        particleActivity: 2.0,
        statusText: "NEURAL REASONING & PLANNING..."
    },
    PROCESSING: {
        theme: "purple",
        pulseSpeed: 3.5,
        rotationSpeed: 2.8,
        particleActivity: 2.0,
        statusText: "NEURAL LOGIC COMPILING..."
    },
    SPEAKING: {
        theme: "blue",
        pulseSpeed: 2.0,
        rotationSpeed: 1.0,
        particleActivity: 1.6,
        statusText: "SYNTHESIZING VOCAL RESPONSE..."
    },
    EXECUTING: {
        theme: "green",
        pulseSpeed: 2.8,
        rotationSpeed: 2.2,
        particleActivity: 1.8,
        statusText: "DISPATCHING HARDWARE COMMAND..."
    },
    SUCCESS: {
        theme: "green",
        pulseSpeed: 4.0,
        rotationSpeed: 1.5,
        particleActivity: 2.5,
        statusText: "COMMAND EXECUTED SUCCESSFULLY"
    },
    WARNING: {
        theme: "amber",
        pulseSpeed: 3.0,
        rotationSpeed: 1.8,
        particleActivity: 1.5,
        statusText: "SYSTEM WARNING: ATTENTION REQUIRED"
    },
    ERROR: {
        theme: "red",
        pulseSpeed: 5.0,
        rotationSpeed: 3.0,
        particleActivity: 2.2,
        statusText: "CRITICAL EXCEPTION ENCOUNTERED"
    }
};

class StateManager {
    constructor() {
        this.currentState = "BOOTING";
        this.previousState = "IDLE";
        this.stateData = JARVIS_STATES.BOOTING;
        this.details = "System Boot Sequence";
        this.stateStartTime = Date.now();
        this.listeners = [];
        
        // Boot transition to IDLE after 2.5 seconds
        setTimeout(() => {
            if (this.currentState === "BOOTING") {
                this.setState("IDLE", "Standing by for voice or command.");
            }
        }, 2500);
    }

    setState(newState, details = "") {
        const key = newState.toUpperCase();
        if (!JARVIS_STATES[key]) {
            console.warn("[StateManager] Unknown state:", newState);
            return;
        }

        this.previousState = this.currentState;
        this.currentState = key;
        this.stateData = JARVIS_STATES[key];
        this.details = details || this.stateData.statusText;
        this.stateStartTime = Date.now();

        // Update active theme based on state preset
        if (window.ThemeEngine && this.stateData.theme) {
            window.ThemeEngine.setTheme(this.stateData.theme);
        }

        // Notify subscribers
        for (const cb of this.listeners) {
            cb(this.currentState, this.stateData, this.details);
        }

        // Auto-revert SUCCESS or ERROR back to IDLE after burst
        if (key === "SUCCESS") {
            setTimeout(() => {
                if (this.currentState === "SUCCESS") {
                    this.setState("IDLE");
                }
            }, 3000);
        } else if (key === "ERROR") {
            setTimeout(() => {
                if (this.currentState === "ERROR") {
                    this.setState("IDLE");
                }
            }, 4000);
        }
    }

    getState() {
        return this.currentState;
    }

    onStateChange(cb) {
        this.listeners.push(cb);
    }
}

window.StateManager = new StateManager();
