/**
 * JARVIS V4 Chat Dock, Action Confirmation Modal, & PTT Control Subsystem
 * Connects the 3D Holographic UI to the FastAPI backend (/v1/chat/stream, /v1/tools/{name}/confirm).
 */

class ChatDockManager {
    constructor() {
        this.chatDock = null;
        this.chatMessages = null;
        this.chatInput = null;
        this.chatSendBtn = null;
        this.chatToggleBtn = null;
        this.micPill = null;
        this.micStateLabel = null;
        this.micRmsFill = null;
        this.confirmModal = null;
        this.confirmToolName = null;
        this.confirmToolArgs = null;
        this.confirmApproveBtn = null;
        this.confirmRejectBtn = null;

        this.conversationId = "conv-" + Math.random().toString(36).substring(2, 9);
        this.currentStreamingEl = null;
        this.currentStreamingText = "";
        this.pendingConfirmation = null;
        this.isMinimized = false;

        // Authentication token resolution (URL query > localStorage > sessionStorage > default)
        const urlParams = typeof window !== "undefined" && window.location ? new URLSearchParams(window.location.search) : null;
        this.authToken = (urlParams && (urlParams.get("token") || urlParams.get("auth"))) ||
                         (typeof localStorage !== "undefined" && localStorage.getItem("jarvis_auth_token")) ||
                         (typeof sessionStorage !== "undefined" && sessionStorage.getItem("jarvis_token")) ||
                         "naanthaandaleo";
        if (typeof localStorage !== "undefined") {
            localStorage.setItem("jarvis_auth_token", this.authToken);
        }

        // Web Speech API Subsystems (STT & TTS)
        this.speechEnabled = true;
        this.isListening = false;
        this.recognition = null;
        this.speechSynthesis = typeof window !== "undefined" ? window.speechSynthesis : null;
        this.speechPulseTimer = null;
    }

    init() {
        this.chatDock = document.getElementById("hud-chat-dock");
        this.chatMessages = document.getElementById("chat-messages");
        this.chatInput = document.getElementById("chat-input");
        this.chatSendBtn = document.getElementById("chat-send-btn");
        this.chatToggleBtn = document.getElementById("chat-toggle-btn");

        this.micPill = document.getElementById("hud-mic-pill");
        this.micStateLabel = document.getElementById("mic-state-label");
        this.micRmsFill = document.getElementById("mic-rms-fill");

        this.confirmModal = document.getElementById("hud-confirm-modal");
        this.confirmToolName = document.getElementById("confirm-tool-name");
        this.confirmToolArgs = document.getElementById("confirm-tool-args");
        this.confirmApproveBtn = document.getElementById("confirm-approve-btn");
        this.confirmRejectBtn = document.getElementById("confirm-reject-btn");

        this.bindEvents();
        this.syncStateListeners();
        this.initSpeechEngine();
        console.log("[ChatDock] Initialized with conversation ID:", this.conversationId);
    }

    bindEvents() {
        // Send button
        if (this.chatSendBtn) {
            this.chatSendBtn.addEventListener("click", () => this.handleSendMessage());
        }

        // Input Enter key
        if (this.chatInput) {
            this.chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }

        // Dock minimize / restore toggle
        if (this.chatToggleBtn) {
            this.chatToggleBtn.addEventListener("click", () => {
                this.isMinimized = !this.isMinimized;
                if (this.chatDock) {
                    this.chatDock.classList.toggle("minimized", this.isMinimized);
                }
                this.chatToggleBtn.textContent = this.isMinimized ? "▲ EXPAND" : "▼ DOCK";
            });
        }

        // Confirmation Modal Buttons
        if (this.confirmApproveBtn) {
            this.confirmApproveBtn.addEventListener("click", () => this.handleConfirmation(true));
        }
        if (this.confirmRejectBtn) {
            this.confirmRejectBtn.addEventListener("click", () => this.handleConfirmation(false));
        }

        // Mic Pill & Mic Button Click (click-to-speak toggle)
        const micToggle = document.getElementById("mic-toggle-btn");
        if (micToggle) {
            micToggle.addEventListener("click", (e) => {
                e.stopPropagation();
                this.toggleListening();
                if (window.JarvisWS && window.JarvisWS.isConnected && !window.JarvisWS.isCloud) {
                    window.JarvisWS.send("toggle_mic", {});
                }
            });
        }
        if (this.micPill) {
            this.micPill.style.cursor = "pointer";
            this.micPill.title = "Click to talk / Hold Home key to speak";
            this.micPill.addEventListener("click", () => {
                this.toggleListening();
            });
        }

        // Diagnostics Modal Events
        const diagTrigger = document.getElementById("hud-diag-trigger");
        const diagModal = document.getElementById("hud-diag-modal");
        const diagClose = document.getElementById("diag-close-btn");
        const diagRefresh = document.getElementById("diag-refresh-btn");
        const diagBox = document.getElementById("diag-content-box");

        const fetchDiagnostics = async () => {
            if (!diagBox) return;
            diagBox.innerHTML = "<p style='color: #94a3b8;'>Querying live system diagnostics...</p>";
            try {
                const res = await fetch("/api/diagnostics");
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                let html = "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;'>";

                const addCard = (title, items) => {
                    html += `<div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2);">
                        <div style="font-weight: bold; color: #38bdf8; margin-bottom: 6px;">${title}</div>`;
                    for (const [k, v] of Object.entries(items)) {
                        const valColor = (v === true || v === "ok" || v === "PASS") ? "#4ade80" : (v === false || v === "FAIL" ? "#f87171" : "#e2e8f0");
                        html += `<div style="display: flex; justify-content: space-between; font-size: 11px; margin: 2px 0;">
                            <span style="color: #94a3b8;">${k}:</span>
                            <span style="color: ${valColor}; font-weight: 500;">${v}</span>
                        </div>`;
                    }
                    html += `</div>`;
                };

                if (data.server) addCard("SERVER", { Status: data.server.status, Uptime: `${data.server.uptime_seconds}s`, State: data.server.current_state, PID: data.server.pid });
                if (data.ai) addCard("AI REASONING", { Available: data.ai.available, Provider: data.ai.provider, Model: data.ai.configured_model });
                if (data.memory) addCard("MEMORY VAULT", { Database: data.memory.database_connected, Facts: data.memory.facts_count, Vault: data.memory.vault_directory_available });
                if (data.voice) addCard("VOICE ENGINE", { PTT: data.voice.push_to_talk_initialized, TTS: data.voice.tts_engine_available, AudioLib: data.voice.pyaudio_available });
                if (data.vision) addCard("VISION SENSORS", { Screen: data.vision.screen_capture_available, Camera: data.vision.camera_available });
                if (data.executor) addCard("EXECUTOR & TOOLS", { Catalog: `${data.executor.registered_tools_count} tools`, Policy: "Enforced" });
                if (data.websocket) addCard("WEBSOCKET BRIDGE", { Active: data.websocket.broadcaster_active, Clients: data.websocket.active_clients });
                if (data.mobile) addCard("MOBILE LINK", { Devices: data.mobile.paired_devices_count, Pairing: data.mobile.pairing_session_active });

                html += "</div>";
                diagBox.innerHTML = html;
            } catch (err) {
                diagBox.innerHTML = `<p style='color: #ef4444;'>Failed to load diagnostics: ${err.message}</p>`;
            }
        };

        if (diagTrigger && diagModal) {
            diagTrigger.addEventListener("click", () => {
                diagModal.style.display = "flex";
                fetchDiagnostics();
            });
        }
        if (diagClose && diagModal) {
            diagClose.addEventListener("click", () => {
                diagModal.style.display = "none";
            });
        }
        if (diagRefresh) {
            diagRefresh.addEventListener("click", fetchDiagnostics);
        }
    }

    syncStateListeners() {
        // Synchronize with visual StateManager
        if (window.StateManager) {
            window.StateManager.onStateChange((state, data, details) => {
                this.updateMicBadge(state, details);
            });
        }

        // Synchronize with WebSocket audio levels
        if (window.JarvisWS) {
            window.JarvisWS.on("audio_level", (data) => {
                if (this.micRmsFill && typeof data.level === "number") {
                    const pct = Math.min(100, Math.round(data.level * 100));
                    this.micRmsFill.style.width = `${pct}%`;
                }
            });

            // If user spoke via PTT
            window.JarvisWS.on("user_message", (data) => {
                if (data.text) {
                    this.appendUserMessage(data.text);
                }
            });

            // If assistant vocal text broadcast arrives from background PTT
            window.JarvisWS.on("assistant_text", (data) => {
                if (data.text) {
                    this.appendAssistantMessage(data.text);
                }
            });

            // If confirmation required arrives via WebSocket
            window.JarvisWS.on("confirmation_required", (data) => {
                if (data.tool) {
                    this.showConfirmationModal(data.tool, data.arguments || {}, data.conversation_id || this.conversationId);
                }
            });
        }
    }

    initSpeechEngine() {
        const SpeechRecognition = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
        if (SpeechRecognition) {
            try {
                this.recognition = new SpeechRecognition();
                this.recognition.continuous = false;
                this.recognition.interimResults = true;
                this.recognition.lang = "en-US";

                this.recognition.onstart = () => {
                    this.isListening = true;
                    if (window.StateManager) {
                        window.StateManager.setState("LISTENING", "Capturing voice command...");
                    }
                    if (this.micStateLabel) {
                        this.micStateLabel.textContent = "LISTENING";
                        this.micStateLabel.className = "mic-status-badge state-listening";
                    }
                    if (this.micPill) {
                        this.micPill.className = "hud-mic-pill active-listening";
                    }
                };

                this.recognition.onresult = (event) => {
                    let interimTranscript = "";
                    let finalTranscript = "";

                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript;
                        } else {
                            interimTranscript += event.results[i][0].transcript;
                        }
                    }

                    const currentWords = (finalTranscript || interimTranscript).trim();
                    if (this.chatInput && currentWords) {
                        this.chatInput.value = currentWords;
                    }

                    if (this.micRmsFill) {
                        const fakeLevel = Math.min(100, Math.round(30 + Math.random() * 60));
                        this.micRmsFill.style.width = `${fakeLevel}%`;
                    }
                    if (window.AudioEngine) {
                        window.AudioEngine.setBackendLevel(0.4 + Math.random() * 0.4);
                    }

                    if (finalTranscript) {
                        if (this.micPill) {
                            this.micPill.className = "hud-mic-pill active-thinking";
                        }
                        this.handleSendMessage();
                    }
                };

                this.recognition.onerror = (event) => {
                    console.info("[Voice] Web Speech notice:", event.error);
                    this.isListening = false;
                    if (window.StateManager && window.StateManager.currentState === "LISTENING") {
                        window.StateManager.setState("IDLE", "Standing by.");
                    }
                    if (this.micStateLabel) {
                        this.micStateLabel.textContent = "IDLE";
                        this.micStateLabel.className = "mic-status-badge state-idle";
                    }
                    if (this.micPill) {
                        this.micPill.className = "hud-mic-pill";
                    }
                    if (this.micRmsFill) this.micRmsFill.style.width = "0%";
                };

                this.recognition.onend = () => {
                    this.isListening = false;
                    if (this.micStateLabel) {
                        this.micStateLabel.textContent = "IDLE";
                        this.micStateLabel.className = "mic-status-badge state-idle";
                    }
                    if (this.micPill) {
                        this.micPill.className = "hud-mic-pill";
                    }
                    if (this.micRmsFill) this.micRmsFill.style.width = "0%";
                    if (window.StateManager && window.StateManager.currentState === "LISTENING") {
                        window.StateManager.setState("IDLE", "Standing by.");
                    }
                };
                console.log("[Voice] Browser speech recognition subsystem initialized.");
            } catch (e) {
                console.warn("[Voice] Speech recognition initialization notice:", e);
            }
        }

        // Global Home Key Push-To-Talk
        if (typeof window !== "undefined") {
            window.addEventListener("keydown", (e) => {
                if (e.key === "Home" && !e.repeat && document.activeElement !== this.chatInput) {
                    e.preventDefault();
                    this.startListening();
                }
            });

            window.addEventListener("keyup", (e) => {
                if (e.key === "Home" && this.isListening) {
                    e.preventDefault();
                    this.stopListening();
                }
            });
        }
    }

    startListening() {
        if (!this.recognition) {
            console.info("[Voice] Web Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.");
            this.appendAssistantMessage("Voice capture requires Chrome, Edge, or a Web Speech API browser, sir.");
            return;
        }
        if (this.isListening) return;

        try {
            if (this.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
            this.recognition.start();
        } catch (e) {
            console.debug("[Voice] Speech recognition start exception:", e);
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (e) {}
        }
    }

    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    speak(text, audioB64 = null) {
        if (!this.speechEnabled || typeof window === "undefined" || !text) return;

        try {
            if (this.currentAudio) {
                try { this.currentAudio.pause(); } catch(e){}
                this.currentAudio = null;
            }
            if ("speechSynthesis" in window) {
                window.speechSynthesis.cancel();
            }
            if (this.speechPulseTimer) {
                clearInterval(this.speechPulseTimer);
                this.speechPulseTimer = null;
            }

            // Clean text for speech: strip URLs, markdown symbols, tool tags, brackets
            let clean = text
                .replace(/https?:\/\/\S+/g, "")
                .replace(/<[^>]+>/g, "")
                .replace(/[*#_`~]/g, "")
                .replace(/\[TOOL\][^\n]+/g, "")
                .replace(/\{[^}]+\}/g, "")
                .trim();

            if (!clean) return;

            const onStartSpeaking = () => {
                if (window.StateManager) {
                    window.StateManager.setState("SPEAKING", "Formulating vocal response...");
                }
                if (this.micPill) {
                    this.micPill.className = "hud-mic-pill active-speaking";
                }
                if (this.micStateLabel) {
                    this.micStateLabel.textContent = "SPEAKING";
                    this.micStateLabel.className = "mic-status-badge state-speaking";
                }
                if (window.HUDManager) {
                    window.HUDManager.showAssistantText(clean);
                }

                // Animate waveform while speaking
                this.speechPulseTimer = setInterval(() => {
                    if (window.AudioEngine) {
                        window.AudioEngine.setBackendLevel(0.4 + Math.random() * 0.45);
                    }
                }, 100);
            };

            const finalizeSpeaking = () => {
                if (this.speechPulseTimer) {
                    clearInterval(this.speechPulseTimer);
                    this.speechPulseTimer = null;
                }
                if (this.micPill) {
                    this.micPill.className = "hud-mic-pill";
                }
                if (this.micStateLabel) {
                    this.micStateLabel.textContent = "IDLE";
                    this.micStateLabel.className = "mic-status-badge state-idle";
                }
                setTimeout(() => {
                    if (window.StateManager && window.StateManager.currentState === "SPEAKING") {
                        window.StateManager.setState("IDLE", "Standing by.");
                    }
                }, 1000);
            };

            // If Fish Audio / server audio_b64 is present, play directly
            if (audioB64) {
                try {
                    const audio = new Audio("data:audio/mp3;base64," + audioB64);
                    this.currentAudio = audio;
                    audio.onplay = onStartSpeaking;
                    audio.onended = () => {
                        this.currentAudio = null;
                        finalizeSpeaking();
                    };
                    audio.onerror = () => {
                        this.currentAudio = null;
                        this.fallbackBrowserSpeech(clean, onStartSpeaking, finalizeSpeaking);
                    };
                    audio.play().catch(() => {
                        this.fallbackBrowserSpeech(clean, onStartSpeaking, finalizeSpeaking);
                    });
                    return;
                } catch (e) {
                    console.debug("[Voice] Audio play error, falling back to browser speech synthesis:", e);
                }
            }

            this.fallbackBrowserSpeech(clean, onStartSpeaking, finalizeSpeaking);
        } catch (e) {
            console.warn("[Voice] Speech synthesis notice:", e);
        }
    }

    fallbackBrowserSpeech(clean, onStartSpeaking, finalizeSpeaking) {
        if (!("speechSynthesis" in window)) return;
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.rate = 1.02;
        utterance.pitch = 0.96;

        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => 
            v.lang.startsWith("en") && 
            (v.name.includes("UK") || v.name.includes("British") || v.name.includes("George") || v.name.includes("David") || v.name.includes("Daniel") || v.name.includes("Male") || v.name.includes("Natural"))
        ) || voices.find(v => v.lang.startsWith("en"));

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        utterance.onstart = onStartSpeaking;
        utterance.onend = finalizeSpeaking;
        utterance.onerror = finalizeSpeaking;

        window.speechSynthesis.speak(utterance);
    }

    updateMicBadge(state, details = "") {
        if (!this.micStateLabel) return;
        this.micStateLabel.textContent = state;
        this.micStateLabel.className = `mic-status-badge state-${state.toLowerCase()}`;

        if (this.micPill) {
            this.micPill.className = `hud-mic-pill active-${state.toLowerCase()}`;
        }
    }

    async handleSendMessage() {
        if (!this.chatInput) return;
        const text = this.chatInput.value.trim();
        if (!text) return;

        this.chatInput.value = "";

        // Client-side authentication command: /auth <token>
        if (text.startsWith("/auth ")) {
            const newToken = text.substring(6).trim();
            if (newToken) {
                this.authToken = newToken;
                if (typeof localStorage !== "undefined") localStorage.setItem("jarvis_auth_token", newToken);
                if (typeof sessionStorage !== "undefined") sessionStorage.setItem("jarvis_token", newToken);
                this.appendUserMessage(text);
                this.appendAssistantMessage("Security access token updated successfully, sir. Cloud neural link authenticated.");
                return;
            }
        }

        this.appendUserMessage(text);

        // Update HUD state to THINKING
        if (window.StateManager) {
            window.StateManager.setState("THINKING", "Synthesizing response...");
        }

        // Call streaming endpoint
        await this.streamChat(text);
    }

    appendUserMessage(text) {
        if (!this.chatMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-bubble user-bubble";
        msgDiv.innerHTML = `<div class="bubble-sender">YOU</div><div class="bubble-content">${this.escapeHtml(text)}</div>`;
        this.chatMessages.appendChild(msgDiv);
        this.scrollToBottom();
    }

    createAssistantStreamingBubble() {
        if (!this.chatMessages) return null;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-bubble assistant-bubble";
        msgDiv.innerHTML = `<div class="bubble-sender">JARVIS // NEURAL CORE</div><div class="bubble-content"><span class="stream-text"></span><span class="cursor-blink">▌</span></div>`;
        this.chatMessages.appendChild(msgDiv);
        this.scrollToBottom();
        return msgDiv;
    }

    appendToolCard(bubbleEl, toolEvents) {
        if (!bubbleEl || !Array.isArray(toolEvents)) return;
        toolEvents.forEach(evt => {
            const card = document.createElement("div");
            card.className = `tool-badge-card ${evt.success ? "success" : "failure"}`;
            const statusIcon = evt.success ? "✓" : "✗";
            card.innerHTML = `
                <div class="tool-badge-header">
                    <span class="tool-icon">${statusIcon}</span>
                    <span class="tool-name">[TOOL] ${this.escapeHtml(evt.tool || "action")}</span>
                </div>
                ${evt.output ? `<div class="tool-badge-output">${this.escapeHtml(String(evt.output))}</div>` : ""}
                ${evt.error ? `<div class="tool-badge-error">${this.escapeHtml(String(evt.error))}</div>` : ""}
            `;
            bubbleEl.appendChild(card);
        });
        this.scrollToBottom();
    }

    appendAssistantMessage(text) {
        if (!this.chatMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-bubble assistant-bubble";
        msgDiv.innerHTML = `<div class="bubble-sender">JARVIS // NEURAL CORE</div><div class="bubble-content">${this.escapeHtml(text)}</div>`;
        this.chatMessages.appendChild(msgDiv);
        this.scrollToBottom();
    }

    async streamChat(message) {
        const bubble = this.createAssistantStreamingBubble();
        const textSpan = bubble ? bubble.querySelector(".stream-text") : null;
        const cursor = bubble ? bubble.querySelector(".cursor-blink") : null;
        let accumulated = "";

        const payload = {
            conversation_id: this.conversationId,
            message: message,
            text: message,
            confirmed: false
        };

        const headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        };
        if (this.authToken) {
            headers["X-JARVIS-Token"] = this.authToken;
            headers["Authorization"] = `Bearer ${this.authToken}`;
        }

        try {
            let response = await fetch("/v1/chat/stream", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(payload)
            });

            // If streaming route is unavailable (404/405), fallback to non-streaming POST /v1/chat or /ask
            if (response.status === 404 || response.status === 405) {
                console.log("[ChatDock] /v1/chat/stream not supported, falling back to /v1/chat or /ask...");
                const nonStreamHeaders = Object.assign({}, headers);
                delete nonStreamHeaders["Accept"];
                response = await fetch("/v1/chat", {
                    method: "POST",
                    headers: nonStreamHeaders,
                    body: JSON.stringify(payload)
                });
                if (response.status === 404) {
                    response = await fetch("/ask", {
                        method: "POST",
                        headers: nonStreamHeaders,
                        body: JSON.stringify({ text: message, message: message })
                    });
                }
                if (response.status === 401 || response.status === 403) {
                    if (textSpan) {
                        textSpan.innerHTML = `Access Denied: Security Token Required.<br><small style="color: var(--jarvis-primary);">Type <code style="background: rgba(255,122,0,0.2); padding: 2px 4px; border-radius: 2px;">/auth &lt;token&gt;</code> to authenticate.</small>`;
                    }
                    if (cursor) cursor.remove();
                    if (window.StateManager) window.StateManager.setState("ERROR", "Auth required.");
                    return;
                }
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                const data = await response.json();
                const reply = data.reply || data.response || data.text || "Neural core online, sir.";
                if (textSpan) textSpan.textContent = reply;
                if (cursor) cursor.remove();
                this.speak(reply, data.audio_b64);
                return;
            }

            if (response.status === 401 || response.status === 403) {
                if (textSpan) {
                    textSpan.innerHTML = `Access Denied: Security Token Required.<br><small style="color: var(--jarvis-primary);">Type <code style="background: rgba(255,122,0,0.2); padding: 2px 4px; border-radius: 2px;">/auth &lt;token&gt;</code> to authenticate.</small>`;
                }
                if (cursor) cursor.remove();
                if (window.StateManager) window.StateManager.setState("ERROR", "Auth required.");
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            let streamAudioB64 = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop(); // keep partial line

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(trimmed.substring(6));
                            if (data.type === "chunk") {
                                accumulated += data.chunk;
                                if (textSpan) textSpan.textContent = accumulated;
                                this.scrollToBottom();
                            } else if (data.type === "tool_events") {
                                this.appendToolCard(bubble, data.tool_events);
                            } else if (data.type === "confirmation_required") {
                                this.showConfirmationModal(data.tool, data.arguments, data.conversation_id || this.conversationId);
                            } else if (data.type === "done") {
                                if (!accumulated && data.content) {
                                    accumulated = data.content;
                                    if (textSpan) textSpan.textContent = accumulated;
                                }
                                if (data.audio_b64) {
                                    streamAudioB64 = data.audio_b64;
                                }
                            }
                        } catch (err) {
                            console.debug("[ChatDock] SSE parse skip:", trimmed);
                        }
                    }
                }
            }

            if (cursor) cursor.remove();
            if (accumulated) {
                this.speak(accumulated, streamAudioB64);
            }
        } catch (err) {
            console.error("[ChatDock] Streaming failed:", err);
            if (textSpan) {
                textSpan.textContent = "Error: Unable to stream neural response from backend server.";
            }
            if (cursor) cursor.remove();
            if (window.StateManager) {
                window.StateManager.setState("ERROR", "Communication failed.");
            }
        }
    }

    showConfirmationModal(toolName, args, conversationId) {
        this.pendingConfirmation = {
            toolName: toolName,
            args: args,
            conversationId: conversationId || this.conversationId
        };

        if (this.confirmToolName) {
            this.confirmToolName.textContent = toolName;
        }
        if (this.confirmToolArgs) {
            this.confirmToolArgs.textContent = JSON.stringify(args, null, 2);
        }
        if (this.confirmModal) {
            this.confirmModal.style.display = "flex";
        }
        if (window.StateManager) {
            window.StateManager.setState("WARNING", `CONFIRMATION REQUIRED: ${toolName}`);
        }
    }

    hideConfirmationModal() {
        if (this.confirmModal) {
            this.confirmModal.style.display = "none";
        }
        this.pendingConfirmation = null;
    }

    async handleConfirmation(isApproved) {
        if (!this.pendingConfirmation) return;
        const { toolName, args, conversationId } = this.pendingConfirmation;
        this.hideConfirmationModal();

        const bubble = this.createAssistantStreamingBubble();
        const textSpan = bubble ? bubble.querySelector(".stream-text") : null;
        const cursor = bubble ? bubble.querySelector(".cursor-blink") : null;

        if (!isApproved) {
            if (textSpan) textSpan.textContent = `Action '${toolName}' was denied by user.`;
            if (cursor) cursor.remove();
            if (window.StateManager) window.StateManager.setState("IDLE", "Action rejected.");
            return;
        }

        if (textSpan) textSpan.textContent = `Executing authorized action '${toolName}'...`;
        if (window.StateManager) window.StateManager.setState("EXECUTING", `Executing ${toolName}...`);

        try {
            const resp = await fetch(`/v1/tools/${encodeURIComponent(toolName)}/confirm`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    tool_name: toolName,
                    arguments: args,
                    confirmed: true
                })
            });
            const data = await resp.json();
            if (cursor) cursor.remove();

            if (data.tool_events) {
                this.appendToolCard(bubble, data.tool_events);
            }
            if (textSpan) {
                textSpan.textContent = data.content || `Action '${toolName}' executed successfully.`;
            }
            if (window.StateManager) {
                window.StateManager.setState("SUCCESS", "Action completed.");
                setTimeout(() => window.StateManager.setState("IDLE", "Standing by."), 2500);
            }
        } catch (e) {
            console.error("[ChatDock] Confirmation execution error:", e);
            if (cursor) cursor.remove();
            if (textSpan) textSpan.textContent = `Execution failed: ${e.message}`;
            if (window.StateManager) window.StateManager.setState("ERROR", "Execution failed.");
        }
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
}

window.ChatDock = new ChatDockManager();
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => window.ChatDock.init());
} else {
    window.ChatDock.init();
}
