// JARVIS V3.0 Mobile Companion Application Logic
let authToken = localStorage.getItem('jarvis_mobile_token') || '';
let deviceId = localStorage.getItem('jarvis_device_id') || '';
let deferredInstallPrompt = null;
let telemetryTimer = null;
let screenStreamTimer = null;

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/mobile/service-worker.js').catch(err => console.log('SW error:', err));
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  const banner = document.getElementById('install-banner');
  if (banner) banner.style.display = 'flex';
});

document.getElementById('btn-install-pwa')?.addEventListener('click', async () => {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    const { outcome } = await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    document.getElementById('install-banner').style.display = 'none';
  }
});

// Sound Feedback (Synthetic HUD Beep)
function playHudBeep(freq = 880, duration = 0.04) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {}
}

function hapticFeedback(pattern = 15) {
  if (navigator.vibrate) {
    navigator.vibrate(pattern);
  }
}

// ---------------------------------------------------------------------------
// Initialization & Pairing
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupTouchpad();
  setupChat();
  setupControls();
  initVoiceSettings();

  // Check URL parameters for auto-pairing (?pin=123456)
  const urlParams = new URLSearchParams(window.location.search);
  const pinParam = urlParams.get('pin');
  if (pinParam) {
    const pinInput = document.getElementById('pair-pin');
    if (pinInput) pinInput.value = pinParam;
    if (!authToken) {
      attemptPairing(pinParam);
    }
  } else if (!authToken) {
    // Attempt auto-discovery of active pairing PIN from local server
    fetch('/api/pairing/status')
      .then(r => r.json())
      .then(d => {
        if (d && d.pin) {
          const pinInput = document.getElementById('pair-pin');
          if (pinInput && !pinInput.value) {
            pinInput.value = d.pin;
          }
        }
      })
      .catch(() => {});
  }

  if (authToken) {
    showDashboard();
  } else {
    showPairingScreen();
  }

  document.getElementById('btn-pair')?.addEventListener('click', () => {
    const pin = document.getElementById('pair-pin').value.trim();
    attemptPairing(pin);
  });

  document.getElementById('btn-unpair')?.addEventListener('click', unpairDevice);
});

function showPairingScreen() {
  document.getElementById('view-pairing').style.display = 'flex';
  document.getElementById('app-nav').style.display = 'none';
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.getElementById('conn-dot').classList.add('disconnected');
  document.getElementById('conn-text').textContent = 'UNPAIRED';
  document.getElementById('btn-unpair').style.display = 'none';
  if (telemetryTimer) clearInterval(telemetryTimer);
}

function showDashboard() {
  document.getElementById('view-pairing').style.display = 'none';
  document.getElementById('app-nav').style.display = 'flex';
  document.getElementById('pane-chat').classList.add('active');
  document.getElementById('conn-dot').classList.remove('disconnected');
  document.getElementById('conn-text').textContent = 'CONNECTED';
  document.getElementById('btn-unpair').style.display = 'inline-block';

  // Start background polling and WebSocket connection
  initControlWebSocket();
  fetchTelemetry();
  if (!telemetryTimer) {
    telemetryTimer = setInterval(fetchTelemetry, 3500);
  }
}

async function attemptPairing(pin) {
  const errEl = document.getElementById('pair-error');
  errEl.style.display = 'none';

  if (!pin || pin.length < 4) {
    errEl.textContent = 'Please enter a valid 6-digit PIN.';
    errEl.style.display = 'block';
    return;
  }

  const deviceName = document.getElementById('pair-name').value.trim() || 'Mobile Device';

  try {
    const res = await fetch('/api/pairing/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin: pin, device_name: deviceName })
    });

    const data = await res.json();
    if (res.ok && data.success && data.auth_token) {
      authToken = data.auth_token;
      deviceId = data.device_id;
      localStorage.setItem('jarvis_mobile_token', authToken);
      localStorage.setItem('jarvis_device_id', deviceId);
      playHudBeep(1200, 0.1);
      hapticFeedback([30, 50, 30]);
      showDashboard();
    } else {
      errEl.textContent = data.detail || 'Pairing failed. Check PIN and try again.';
      errEl.style.display = 'block';
      hapticFeedback(80);
    }
  } catch (err) {
    errEl.textContent = 'Connection error. Ensure phone is on the same Wi-Fi.';
    errEl.style.display = 'block';
  }
}

function unpairDevice() {
  if (confirm('Unpair this phone from JARVIS PC?')) {
    localStorage.removeItem('jarvis_mobile_token');
    localStorage.removeItem('jarvis_device_id');
    authToken = '';
    deviceId = '';
    showPairingScreen();
  }
}

// ---------------------------------------------------------------------------
// Tab Navigation
// ---------------------------------------------------------------------------
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      playHudBeep(950, 0.03);
      hapticFeedback(12);

      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      const targetTab = item.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      const activePane = document.getElementById(targetTab);
      if (activePane) activePane.classList.add('active');

      if (targetTab === 'pane-stats') {
        fetchTelemetry(true);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Mobile Voice Pack & Neural TTS Management
// ---------------------------------------------------------------------------
let voiceEngine = localStorage.getItem('jarvis_voice_engine') || 'neural';
let activeNeuralVoice = localStorage.getItem('jarvis_neural_voice') || 'en-GB-RyanNeural';
let activeDeviceVoiceName = localStorage.getItem('jarvis_device_voice_name') || '';
let voiceSpeed = parseFloat(localStorage.getItem('jarvis_voice_speed') || '1.0');
let voicePitch = parseFloat(localStorage.getItem('jarvis_voice_pitch') || '1.0');
let ttsAudioPlayer = new Audio();
let cachedDeviceVoices = [];

function initVoiceSettings() {
  const selNeural = document.getElementById('select-neural-voice');
  if (selNeural) selNeural.value = activeNeuralVoice;

  const sliderSpeed = document.getElementById('slider-voice-speed');
  if (sliderSpeed) sliderSpeed.value = voiceSpeed;

  const sliderPitch = document.getElementById('slider-voice-pitch');
  if (sliderPitch) sliderPitch.value = voicePitch;

  updateVoiceSliderLabels();
  setVoiceEngine(voiceEngine);
  populateDeviceVoices();

  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      populateDeviceVoices();
    };
  }

  updateActiveVoiceLabel();
}

function updateVoiceSliderLabels() {
  const speed = document.getElementById('slider-voice-speed')?.value || '1.0';
  const pitch = document.getElementById('slider-voice-pitch')?.value || '1.0';
  const lblSpeed = document.getElementById('lbl-voice-speed');
  const lblPitch = document.getElementById('lbl-voice-pitch');
  if (lblSpeed) lblSpeed.textContent = `${parseFloat(speed).toFixed(2)}x`;
  if (lblPitch) lblPitch.textContent = `${parseFloat(pitch).toFixed(2)}x`;
}

function updateActiveVoiceLabel() {
  const lbl = document.getElementById('lbl-active-voice');
  if (!lbl) return;

  if (voiceEngine === 'neural') {
    const sel = document.getElementById('select-neural-voice');
    const txt = sel?.options[sel.selectedIndex]?.text || activeNeuralVoice;
    lbl.textContent = txt.split('(')[0].replace(/[🇬🇧🇺🇸🇦🇺🇮🇳⚡📱]/g, '').trim() || 'JARVIS';
  } else {
    const sel = document.getElementById('select-device-voice');
    const txt = sel?.options[sel.selectedIndex]?.text || activeDeviceVoiceName || 'Phone Device';
    lbl.textContent = txt.split('(')[0].slice(0, 16).trim();
  }
}

window.toggleVoiceModal = function() {
  const modal = document.getElementById('modal-voice-pack');
  if (!modal) return;
  const isHidden = modal.style.display === 'none' || !modal.style.display;
  modal.style.display = isHidden ? 'flex' : 'none';
  if (isHidden) {
    initVoiceSettings();
    hapticFeedback(15);
  }
};

window.setVoiceEngine = function(engine) {
  voiceEngine = engine;
  const btnNeural = document.getElementById('btn-engine-neural');
  const btnDevice = document.getElementById('btn-engine-device');
  const grpNeural = document.getElementById('group-neural-voices');
  const grpDevice = document.getElementById('group-device-voices');

  if (engine === 'neural') {
    btnNeural?.classList.add('active');
    btnDevice?.classList.remove('active');
    if (grpNeural) grpNeural.style.display = 'block';
    if (grpDevice) grpDevice.style.display = 'none';
  } else {
    btnDevice?.classList.add('active');
    btnNeural?.classList.remove('active');
    if (grpNeural) grpNeural.style.display = 'none';
    if (grpDevice) grpDevice.style.display = 'block';
    populateDeviceVoices();
  }
  updateActiveVoiceLabel();
};

function populateDeviceVoices() {
  if (!('speechSynthesis' in window)) return;
  const sel = document.getElementById('select-device-voice');
  if (!sel) return;

  cachedDeviceVoices = window.speechSynthesis.getVoices();
  if (!cachedDeviceVoices.length) return;

  sel.innerHTML = '';
  cachedDeviceVoices.forEach((v) => {
    const opt = document.createElement('option');
    opt.value = v.name;
    opt.textContent = `${v.name} (${v.lang})`;
    if (v.name === activeDeviceVoiceName) {
      opt.selected = true;
    }
    sel.appendChild(opt);
  });
}

window.onVoiceSelected = function() {
  updateActiveVoiceLabel();
};

window.saveVoiceSettings = async function() {
  const selNeural = document.getElementById('select-neural-voice');
  if (selNeural) activeNeuralVoice = selNeural.value;

  const selDevice = document.getElementById('select-device-voice');
  if (selDevice) activeDeviceVoiceName = selDevice.value;

  voiceSpeed = parseFloat(document.getElementById('slider-voice-speed')?.value || '1.0');
  voicePitch = parseFloat(document.getElementById('slider-voice-pitch')?.value || '1.0');

  localStorage.setItem('jarvis_voice_engine', voiceEngine);
  localStorage.setItem('jarvis_neural_voice', activeNeuralVoice);
  localStorage.setItem('jarvis_device_voice_name', activeDeviceVoiceName);
  localStorage.setItem('jarvis_voice_speed', voiceSpeed);
  localStorage.setItem('jarvis_voice_pitch', voicePitch);

  updateActiveVoiceLabel();
  hapticFeedback([20, 40]);
  playHudBeep(1100, 0.05);

  // Sync to server if neural voice
  if (voiceEngine === 'neural' && authToken) {
    try {
      await fetch('/api/tts/set_voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ voice: activeNeuralVoice })
      });
    } catch (e) {}
  }

  toggleVoiceModal();
};

window.testVoicePreview = function() {
  speakJarvisReply("Online and at your service, sir.");
};

async function speakJarvisReply(text) {
  const speakEnabled = document.getElementById('chk-speech-reply')?.checked;
  if (!speakEnabled || !text || !text.trim()) return;

  // 1. Studio Neural Voice Engine (Edge-TTS over HTTPS)
  if (voiceEngine === 'neural') {
    try {
      const ratePct = `${Math.round((voiceSpeed - 1.0) * 100)}%`;
      const pitchHz = `${Math.round((voicePitch - 1.0) * 100)}Hz`;

      const res = await fetch('/api/tts/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          text: text,
          voice: activeNeuralVoice,
          rate: ratePct.startsWith('-') ? ratePct : `+${ratePct}`,
          pitch: pitchHz.startsWith('-') ? pitchHz : `+${pitchHz}`
        })
      });

      if (res.ok) {
        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        ttsAudioPlayer.pause();
        ttsAudioPlayer.src = audioUrl;
        await ttsAudioPlayer.play();
        return;
      }
    } catch (err) {
      console.warn('Neural TTS fallback to device voice:', err);
    }
  }

  // 2. Phone Device Native TTS Fallback
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = voiceSpeed;
    utter.pitch = voicePitch;

    if (activeDeviceVoiceName && cachedDeviceVoices.length) {
      const match = cachedDeviceVoices.find(v => v.name === activeDeviceVoiceName);
      if (match) utter.voice = match;
    }
    window.speechSynthesis.speak(utter);
  }
}

// ---------------------------------------------------------------------------
// Chat & Voice
// ---------------------------------------------------------------------------
function setupChat() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send');
  const micBtn = document.getElementById('btn-mic');

  sendBtn?.addEventListener('click', () => {
    const text = input.value.trim();
    if (text) {
      sendChatMessage(text);
      input.value = '';
    }
  });

  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const text = input.value.trim();
      if (text) {
        sendChatMessage(text);
        input.value = '';
      }
    }
  });

  // Web Speech API Voice Input
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    let isRecording = false;

    micBtn?.addEventListener('click', () => {
      if (isRecording) {
        recognition.stop();
      } else {
        try {
          recognition.start();
          micBtn.classList.add('recording');
          document.getElementById('voice-status').textContent = 'Listening...';
          isRecording = true;
          hapticFeedback(20);
        } catch (e) {}
      }
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        input.value = transcript;
        sendChatMessage(transcript);
        input.value = '';
      }
    };

    recognition.onend = () => {
      micBtn.classList.remove('recording');
      document.getElementById('voice-status').textContent = 'Tap mic to speak';
      isRecording = false;
    };

    recognition.onerror = () => {
      micBtn.classList.remove('recording');
      document.getElementById('voice-status').textContent = 'Mic error. Tap to retry';
      isRecording = false;
    };
  } else {
    if (micBtn) micBtn.style.display = 'none';
  }
}

window.sendQuickPrompt = function(promptText) {
  sendChatMessage(promptText);
};

async function sendChatMessage(text) {
  appendChatBubble('user', text);
  playHudBeep(700, 0.04);

  try {
    const res = await fetch('/api/remote/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ message: text })
    });

    if (res.status === 401 || res.status === 403) {
      unpairDevice();
      return;
    }

    const data = await res.json();
    const reply = data.reply || data.response || 'Action completed, sir.';
    appendChatBubble('jarvis', reply);
    playHudBeep(1100, 0.06);

    // Speak response using chosen Voice Pack & Engine
    speakJarvisReply(reply);
  } catch (err) {
    appendChatBubble('jarvis', `Connection error: ${err.message}`);
  }
}

function appendChatBubble(sender, text) {
  const history = document.getElementById('chat-history');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  if (sender === 'jarvis') {
    bubble.innerHTML = `<span class="speaker">JARVIS</span>${escapeHtml(text)}`;
  } else {
    bubble.textContent = text;
  }

  history.appendChild(bubble);
  history.scrollTop = history.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
}

// ---------------------------------------------------------------------------
// Remote System Controls
// ---------------------------------------------------------------------------
let isUserAdjustingBrightness = false;

function setupControls() {
  const slider = document.getElementById('slider-brightness');
  const label = document.getElementById('brightness-val');
  let bTimeout = null;

  const onBrightnessChange = (e) => {
    const val = parseInt(e.target.value, 10);
    if (label) label.textContent = `${val}%`;
    isUserAdjustingBrightness = true;
    clearTimeout(bTimeout);
    bTimeout = setTimeout(() => {
      execSystemCmd('set_brightness', val);
      setTimeout(() => { isUserAdjustingBrightness = false; }, 1200);
    }, 100);
  };

  slider?.addEventListener('input', onBrightnessChange);
  slider?.addEventListener('change', onBrightnessChange);
}

let controlWs = null;
let pendingMouseDx = 0;
let pendingMouseDy = 0;
let pendingScrollDy = 0;
let mouseDispatchTimer = null;
let isHttpMouseInFlight = false;

function initControlWebSocket() {
  if (controlWs && (controlWs.readyState === WebSocket.OPEN || controlWs.readyState === WebSocket.CONNECTING)) {
    return;
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const tokenParam = authToken ? `?token=${encodeURIComponent(authToken)}` : '';
  const wsUrl = `${proto}//${window.location.host}/ws/chat${tokenParam}`;
  
  try {
    controlWs = new WebSocket(wsUrl);
    controlWs.onopen = () => {
      console.log('[Control] High-speed WebSocket connected');
    };
    controlWs.onclose = () => {
      controlWs = null;
      if (authToken) {
        setTimeout(initControlWebSocket, 2000);
      }
    };
    controlWs.onerror = () => {
      if (controlWs) controlWs.close();
    };
  } catch (e) {
    controlWs = null;
  }
}

function flushMouseDeltas() {
  // 1. Two-finger Scroll
  if (Math.abs(pendingScrollDy) >= 1) {
    const sdy = Math.round(pendingScrollDy);
    pendingScrollDy = 0;
    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      controlWs.send(JSON.stringify({ type: 'mouse', action: 'scroll', dy: sdy }));
    } else {
      sendMouseEvent('scroll', { dy: sdy });
    }
  }

  // 2. Cursor Movement
  const intDx = Math.round(pendingMouseDx);
  const intDy = Math.round(pendingMouseDy);

  if (intDx !== 0 || intDy !== 0) {
    pendingMouseDx -= intDx;
    pendingMouseDy -= intDy;

    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      controlWs.send(JSON.stringify({ type: 'mouse', action: 'move', dx: intDx, dy: intDy }));
    } else {
      if (!isHttpMouseInFlight) {
        isHttpMouseInFlight = true;
        sendMouseEvent('move', { dx: intDx, dy: intDy, speed: 1.0 }).finally(() => {
          isHttpMouseInFlight = false;
        });
      } else {
        pendingMouseDx += intDx;
        pendingMouseDy += intDy;
      }
    }
  }
}

window.execSystemCmd = async function(cmd, val = null) {
  hapticFeedback(15);
  playHudBeep(850, 0.03);

  if (controlWs && controlWs.readyState === WebSocket.OPEN) {
    controlWs.send(JSON.stringify({ type: 'system', command: cmd, value: val }));
    return { status: 'ok' };
  }

  try {
    const res = await fetch('/api/remote/system', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        'x-jarvis-token': authToken
      },
      body: JSON.stringify({ command: cmd, value: val })
    });
    return await res.json();
  } catch (e) {
    console.error('System command error:', e);
  }
};

window.confirmSleep = function() {
  if (confirm('Put host PC to sleep now?')) {
    execSystemCmd('sleep_pc');
  }
};

window.launchApp = function(appName) {
  execSystemCmd('launch_app', appName);
};

// ---------------------------------------------------------------------------
// Virtual Touchpad & Mouse
// ---------------------------------------------------------------------------
function setupTouchpad() {
  const pad = document.getElementById('touchpad-surface');
  if (!pad) return;

  let lastX = 0, lastY = 0;
  let startX = 0, startY = 0;
  let startTime = 0;
  let touchCount = 1;
  let isMoving = false;

  if (!mouseDispatchTimer) {
    mouseDispatchTimer = setInterval(flushMouseDeltas, 16);
  }

  pad.addEventListener('touchstart', (e) => {
    e.preventDefault();
    touchCount = e.touches.length;
    const t = e.touches[0];
    lastX = t.clientX;
    lastY = t.clientY;
    startX = t.clientX;
    startY = t.clientY;
    startTime = Date.now();
    isMoving = false;
  }, { passive: false });

  pad.addEventListener('touchmove', (e) => {
    e.preventDefault();
    touchCount = e.touches.length;
    const t = e.touches[0];
    const rawDx = t.clientX - lastX;
    const rawDy = t.clientY - lastY;
    lastX = t.clientX;
    lastY = t.clientY;

    if (touchCount === 2) {
      isMoving = true;
      pendingScrollDy += -rawDy * 1.5;
      return;
    }

    const dist = Math.hypot(rawDx, rawDy);
    if (dist > 0.3) {
      isMoving = true;
      // High-precision ballistic acceleration
      let accel = 1.35;
      if (dist < 2.5) {
        accel = 0.95; // Precision micro-targeting
      } else if (dist < 8) {
        accel = 1.45; // Smooth standard tracking
      } else if (dist < 20) {
        accel = 2.2;  // Quick glide
      } else {
        accel = Math.min(3.8, 2.2 + (dist - 20) * 0.1); // Fast flick across screen
      }

      pendingMouseDx += rawDx * accel;
      pendingMouseDy += rawDy * accel;
    }
  }, { passive: false });

  pad.addEventListener('touchend', (e) => {
    e.preventDefault();
    const duration = Date.now() - startTime;
    const totalDist = Math.hypot(lastX - startX, lastY - startY);

    // Tap detection: short duration + minimal movement
    if (totalDist < 16 && duration < 320) {
      pendingMouseDx = 0;
      pendingMouseDy = 0;
      const button = (touchCount >= 2) ? 'right' : 'left';
      if (controlWs && controlWs.readyState === WebSocket.OPEN) {
        controlWs.send(JSON.stringify({ type: 'mouse', action: 'click', button: button }));
      } else {
        sendMouseEvent('click', { button: button });
      }
      hapticFeedback(button === 'right' ? [20, 20] : 15);
      playHudBeep(1000, 0.02);
    }
  }, { passive: false });

  document.getElementById('btn-left-click')?.addEventListener('click', () => {
    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      controlWs.send(JSON.stringify({ type: 'mouse', action: 'click', button: 'left' }));
    } else {
      sendMouseEvent('click', { button: 'left' });
    }
    hapticFeedback(15);
  });

  document.getElementById('btn-right-click')?.addEventListener('click', () => {
    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      controlWs.send(JSON.stringify({ type: 'mouse', action: 'click', button: 'right' }));
    } else {
      sendMouseEvent('click', { button: 'right' });
    }
    hapticFeedback(25);
  });
}

async function sendMouseEvent(action, params = {}) {
  try {
    const res = await fetch('/api/remote/mouse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ action, ...params })
    });
    return await res.json();
  } catch (e) {}
}

window.sendKeyboardKey = async function(key) {
  hapticFeedback(15);
  if (controlWs && controlWs.readyState === WebSocket.OPEN) {
    controlWs.send(JSON.stringify({ type: 'keyboard', action: 'press', key: key }));
    return;
  }
  try {
    await fetch('/api/remote/keyboard', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ action: 'press', key })
    });
  } catch (e) {}
};

window.promptKeyboardText = async function() {
  const text = prompt('Enter text to type into active PC window:');
  if (text) {
    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      controlWs.send(JSON.stringify({ type: 'keyboard', action: 'type', text: text }));
      playHudBeep(900, 0.04);
      return;
    }
    try {
      await fetch('/api/remote/keyboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ action: 'type', text })
      });
      playHudBeep(900, 0.04);
    } catch (e) {}
  }
};

// ---------------------------------------------------------------------------
// Screen Mirror
// ---------------------------------------------------------------------------
window.setTrackpadMode = function(mode) {
  const btnTouch = document.getElementById('btn-mode-touchpad');
  const btnScreen = document.getElementById('btn-mode-screen');
  const wrapTouch = document.getElementById('touchpad-wrapper');
  const wrapScreen = document.getElementById('screen-wrapper');

  if (mode === 'touchpad') {
    btnTouch.style.background = 'linear-gradient(135deg, rgba(0,210,255,0.2), rgba(0,119,255,0.3))';
    btnTouch.style.borderColor = 'var(--accent-cyan)';
    btnScreen.style.background = 'transparent';
    btnScreen.style.borderColor = 'transparent';
    wrapTouch.style.display = 'flex';
    wrapScreen.style.display = 'none';
    if (screenStreamTimer) clearInterval(screenStreamTimer);
  } else {
    btnScreen.style.background = 'linear-gradient(135deg, rgba(0,210,255,0.2), rgba(0,119,255,0.3))';
    btnScreen.style.borderColor = 'var(--accent-cyan)';
    btnTouch.style.background = 'transparent';
    btnTouch.style.borderColor = 'transparent';
    wrapTouch.style.display = 'none';
    wrapScreen.style.display = 'flex';
    refreshScreenSnapshot();

    const autoChk = document.getElementById('chk-auto-screen');
    if (autoChk && autoChk.checked) {
      screenStreamTimer = setInterval(refreshScreenSnapshot, 1200);
    }
  }
};

document.getElementById('chk-auto-screen')?.addEventListener('change', (e) => {
  if (e.target.checked) {
    screenStreamTimer = setInterval(refreshScreenSnapshot, 1200);
  } else {
    if (screenStreamTimer) clearInterval(screenStreamTimer);
  }
});

window.refreshScreenSnapshot = function() {
  const img = document.getElementById('screen-img');
  if (img && authToken) {
    img.src = `/api/remote/screen?token=${encodeURIComponent(authToken)}&t=${Date.now()}`;
  }
};

// ---------------------------------------------------------------------------
// Telemetry & Hardware Stats
// ---------------------------------------------------------------------------
async function fetchTelemetry(manual = false) {
  if (!authToken) return;

  try {
    const res = await fetch('/api/remote/telemetry', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    if (res.status === 401 || res.status === 403) {
      unpairDevice();
      return;
    }

    const data = await res.json();
    if (data.cpu_percent !== undefined) {
      document.getElementById('stat-cpu-val').textContent = `${data.cpu_percent}%`;
      const cpuBar = document.getElementById('stat-cpu-bar');
      cpuBar.style.width = `${data.cpu_percent}%`;
      cpuBar.className = `gauge-bar-fill ${data.cpu_percent > 80 ? 'warning' : ''}`;

      document.getElementById('stat-ram-val').textContent = `${data.ram_used_gb} GB / ${data.ram_total_gb} GB (${data.ram_percent}%)`;
      const ramBar = document.getElementById('stat-ram-bar');
      ramBar.style.width = `${data.ram_percent}%`;
      ramBar.className = `gauge-bar-fill ${data.ram_percent > 85 ? 'warning' : ''}`;

      document.getElementById('stat-disk-val').textContent = `${data.disk_free_gb} GB`;

      if (data.battery) {
        document.getElementById('stat-battery-val').textContent = `${data.battery.percent}%`;
        document.getElementById('stat-battery-status').textContent = data.battery.plugged ? '⚡ Charging' : '🔋 On Battery';
      }

      if (data.active_window) {
        document.getElementById('stat-window').textContent = data.active_window;
      }

      if (data.brightness !== undefined && data.brightness !== null && !isUserAdjustingBrightness) {
        const slider = document.getElementById('slider-brightness');
        const bLabel = document.getElementById('brightness-val');
        if (slider && document.activeElement !== slider) {
          slider.value = data.brightness;
        }
        if (bLabel) {
          bLabel.textContent = `${data.brightness}%`;
        }
      }
    }

    if (manual) playHudBeep(1100, 0.03);
  } catch (e) {}
}

// ---------------------------------------------------------------------------
// Clipboard & File Sync
// ---------------------------------------------------------------------------
window.getPCClipboard = async function() {
  try {
    const res = await fetch('/api/remote/clipboard', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ action: 'get' })
    });
    const data = await res.json();
    document.getElementById('clip-text').value = data.text || '';
    playHudBeep(900, 0.04);
  } catch (e) {}
};

window.sendPCClipboard = async function() {
  const text = document.getElementById('clip-text').value;
  try {
    await fetch('/api/remote/clipboard', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ action: 'set', text: text })
    });
    playHudBeep(1050, 0.04);
    alert('Pushed to PC clipboard!');
  } catch (e) {}
};

window.uploadSelectedFile = async function() {
  const fileInput = document.getElementById('upload-file-input');
  if (!fileInput.files.length) {
    alert('Please choose a file to upload.');
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const statusEl = document.getElementById('upload-status');
  statusEl.style.display = 'block';
  statusEl.textContent = 'Uploading...';

  try {
    const res = await fetch('/api/remote/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${authToken}` },
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      statusEl.textContent = `✓ Uploaded to PC: ${data.filename}`;
      playHudBeep(1200, 0.08);
      fileInput.value = '';
    } else {
      statusEl.textContent = `Upload failed: ${data.detail || 'Error'}`;
    }
  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
  }
};
