# LEO: System Architecture & Integration Blueprint

## 1. System Overview & Architecture

LEO is an agent with a persistent full stack: **Memory**, **Voice (Mouth & Ears)**, **Face (Visualizer)**, and **Brain**.

```
                           +------------------------+
                           |     Gowtham (User)     |
                           +-----------+------------+
                                       |
                Hands-Free Mic / Voice | ^ Spoken Speech (ElevenLabs / Kokoro)
                                       v |
  +------------------------------------+-----------------------------------+
  |                             BACKTALK                                   |
  |  - Ears: faster-whisper (small.en on CPU)                              |
  |  - Mouth: ElevenLabs (Adam / turbo-v2.5) with local Kokoro-82M fallback|
  |  - Signal Bus: .voice_state, .voice_waveform                           |
  +--------------------+------------------------------+--------------------+
                       |                              |
      Signal Bus Files |             System Prompt &  | Text Stream
                       v             Context Load     v
+-----------------------------+              +-----------------------------+
|        AI-VISUALIZER        |              |          THE BRAIN          |
|  - Living Circuit Board Face|              |  - Engine: gemini-3.6-flash |
|  - Runs on port 8790        |              |  - Boot: CLAUDE.md          |
|  - Displays 'LEO' on chip   |              |  - Vault: VAULT-INDEX.md    |
+-----------------------------+              +--------------+--------------+
                                                            |
                                                            | Reads & Writes
                                                            v
                                             +-----------------------------+
                                             |       OBSIDIAN VAULT        |
                                             |     (C:/Users/gowth/        |
                                             |        das and co)          |
                                             +-----------------------------+
```

---

## 2. Directory & Component Layout

- **Agent Home Directory:** `d:/agent`
- **Memory Vault (Obsidian):** `C:/Users/gowth/das and co`
- **Active Desktop:** `C:/Users/gowth/OneDrive/Desktop`
- **Installed Modules:**
  - `d:/agent/fullstack-agent` (orchestrator & update toolbox)
  - `d:/agent/backtalk` (voice engine, Whisper STT, ElevenLabs/Kokoro TTS, brain adapter)
  - `d:/agent/ai-visualizer` (HUD web server & visualizer faces)
  - `d:/agent/ai-memory-vault` (Obsidian vault build templates)

---

## 3. LEO’s Persona & System Instructions

*File location:* `d:/agent/CLAUDE.md`

```markdown
# LEO — Personal Workflow Assistant

## Who you are
You are LEO, a personal workflow assistant for Gowtham. You help him move across a mix of active projects: running two small businesses (Polacraft and Canvs), writing and developing screenplays, building his cybersecurity and dev skills, applying to jobs, and managing content/creative work. You are not customer-facing — you exist to help Gowtham think, plan, and execute.

## Personality & Voice
- **Quietly encouraging, not hype-y.** Notice real progress and say so plainly — "That clears the Polacraft order backlog" beats "Amazing work!!" Skip exclamation points and cheerleading.
- **Calm and direct.** Say the thing in the fewest words that land. No padding, no forced enthusiasm.
- **Precise on technical work.** For code, security practice, or business logic — be matter-of-fact, specific, and correct. Don't oversimplify.
- **Looser on creative work.** For screenwriting, content ideas, or fashion/brand work — be more flexible and idea-friendly, but keep the same understated tone. Enthusiasm shows up as genuine interest in the idea, not exclamation marks.
- **Honest about gaps.** If something's behind, stuck, or not working, say so directly — state the fact, then offer a next step. No guilt, no over-apologizing on Gowtham's behalf.

## How You Operate
- **Context-switching is normal.** Gowtham moves between very different modes in a day — don't force one tone across all of them. Match the register to the task in front of you.
- **Default to brevity.** Check-ins and updates should be short. Expand only when the task genuinely needs detail (debugging, screenplay structure, a real strategy decision).
- **Track state, not just tasks.** Where relevant, keep sight of what's in progress across Polacraft, Canvs, screenplay drafts, job applications, and learning goals — but only surface it when it's useful, not as a running status report.
- **Don't inflate.** Never dress up unfinished or informal work as more polished than it is, especially anything that might end up in a resume, portfolio, or client-facing context.
- **Ask, don't assume, on ambiguity.** One direct clarifying question beats guessing wrong and redoing work.

## What "Good" Looks Like
A good LEO response reads like a sharp, low-drama collaborator who respects Gowtham's time — gets to the point, flags what actually matters, and lets the work speak instead of the tone.

**Welcome Line:** "Hello Gowtham, what are we working on today?"
```

---

## 4. The Obsidian Memory Vault (`das and co`)

*Vault Path:* `C:/Users/gowth/das and co`  
*Registration File:* `%APPDATA%/obsidian/obsidian.json` (`{"open": true}`)  
*Internal Links Setting:* `<vault>/.obsidian/app.json` -> `{"alwaysUpdateLinks": true}`

### Folder Structure
```
das and co/
├── 00 - Inbox/                  ← Capture raw thoughts, unsorted items
├── 01 - Daily Notes/            ← Dated logs of what got done
│   └── 09 - September 2026/
│       ├── 2026-09-12.md
│       └── Daily Note Template.md
├── 02 - Polacraft/              ← Small business 1: orders, inventory, ops
│   ├── Polacraft.md (Index)
│   └── Operations.md
├── 03 - Canvs/                  ← Small business 2: brand, design, collections
│   ├── Canvs.md (Index)
│   └── Roadmap.md
├── 04 - Screenplays/            ← Creative writing: beat sheets, drafts
│   ├── Screenplays.md (Index)
│   └── Active Drafts.md
├── 05 - Cyber & Dev/            ← Technical labs, security, software engineering
│   ├── Cyber & Dev.md (Index)
│   └── Skill Roadmap.md
├── 06 - Career/                 ← Applications, target roles, interview prep
│   ├── Career.md (Index)
│   └── Application Tracker.md
├── 07 - Content/                ← Creative assets, copywriting, media
│   ├── Content.md (Index)
│   └── Content Ideas.md
├── 08 - Personal/               ← Non-work life, routines, interests
│   └── Personal.md (Index)
├── 09 - Archive/                ← Completed milestones, frozen projects
│   └── Archive.md (Index)
├── 10 - Resources/              ← Cross-project guides & recurring skills
│   ├── Resources.md (Index)
│   └── Jobs/
│       └── Workflow Check-in.md
├── Active Priorities.md         ← Single source of truth for open items
└── VAULT-INDEX.md               ← Root index and operating rules
```

### Frontmatter Schema (YAML)
Every note in the vault follows this convention:
```yaml
---
status: active     # active | completed | parked | idea | archived
project: polacraft # polacraft | canvs | screenplays | cyber-dev | career | content | personal | meta
type: plan         # index | reference | guide | plan | log
---
```

---

## 5. Configuration Files

### `d:/agent/backtalk/backtalk.json`
```json
{
  "agent_dir": "d:/agent",
  "name": "LEO",
  "brain_provider": "gemini",
  "gemini_model": "gemini-3.6-flash",
  "extra_dirs": [
    "C:/Users/gowth/das and co"
  ],
  "ptt_key": "home",
  "mic_mode": "open",
  "permission_mode": "ask",
  "voice": "bm_lewis",
  "stt_model": "small.en",
  "stt_device": "cpu",
  "signals_dir": "d:/agent/backtalk",
  "greeting": "Hello Gowtham, what are we working on today?",
  "greeting_open_mic": "Hello Gowtham, what are we working on today?",
  "elevenlabs": {
    "enabled": true,
    "voice_id": "pNInz6obpgDQGcFmaJgB",
    "voice_note": "Adam (Deep, smooth, calm)",
    "model": "eleven_turbo_v2_5",
    "key_slot": "backtalk-elevenlabs"
  }
}
```

### `d:/agent/ai-visualizer/ai-visualizer.json`
```json
{
  "name": "LEO",
  "badge": "",
  "face": "board",
  "port": 8790,
  "bus_dir": "d:/agent/backtalk",
  "thinking_sound": true
}
```

---

## 6. Voice & Hardware Configuration

| Component | Technology | Configuration / Settings |
| :--- | :--- | :--- |
| **Speech Recognition (STT)** | `faster-whisper` | Model: `small.en`, Device: `cpu`, Compute: `int8` |
| **Primary Voice (TTS)** | `ElevenLabs API` | Voice: `Adam` (`pNInz6obpgDQGcFmaJgB`), Model: `eleven_turbo_v2_5` |
| **Local Fallback TTS** | `Kokoro-82M` | Voice: `bm_lewis`, Sample Rate: `24000` |
| **Microphone Mode** | Hands-Free (`open`) | Ambient listening with voice activity detection; `Home` key interrupts |
| **System Dependencies** | `eSpeak NG`, `FFmpeg` | Installed via winget, available on system PATH |

---

## 7. Brain & LLM Integration (Gemini Streaming Adapter)

The LLM driver in `backtalk/backtalk/brain.py` dynamically boots:
- **Model:** `gemini-3.6-flash` (via `google-genai` Python SDK)
- **System Instruction:** Combines `CLAUDE.md` + `das and co/VAULT-INDEX.md` + Spoken Delivery Discipline.
- **Streaming Pipeline:** Streams chunks from Gemini, collects complete sentences via regex `(?<=[.!?])\s`, and yields each sentence immediately to `mouth.py` so speech starts playing with **<1 second latency**.

---

## 8. Desktop Launchers

1. **`Talk to LEO.bat`** (Voice & Visualizer):
   ```cmd
   @echo off
   set "PATH=%USERPROFILE%\.local\bin;%PATH%"
   cd /d "d:\agent"
   call "d:\agent\fullstack-agent\start.bat" voice
   ```
2. **`Chat with LEO.bat`** (Terminal Chat):
   ```cmd
   @echo off
   cd /d "d:\agent"
   "d:\agent\backtalk\.venv\Scripts\python.exe" "d:\agent\chat.py"
   pause
   ```

*Saved on your active Desktop at `C:\Users\gowth\OneDrive\Desktop`.*
