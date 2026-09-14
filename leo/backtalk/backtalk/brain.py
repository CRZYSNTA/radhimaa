# backtalk: talk to your Claude Code agent out loud.
# Copyright (C) 2026 Jared Rhodenizer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The warm brain — a persistent Claude session via the Agent SDK,
streaming.

One ClaudeSDKClient lives for the whole voice session: no per-turn
process spawn, no per-turn context reload. Partial-message streaming
means sentences are yielded the moment they're complete, so the mouth
starts speaking while the rest of the thought is still forming.

The session's cwd is YOUR agent's folder (agent_dir in backtalk.json) —
whatever CLAUDE.md lives there defines who is speaking. backtalk adds
only the spoken-delivery discipline (config.DISCIPLINE): the medium,
never the character.
"""
import asyncio
import os
import re
import warnings
from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

try:
    from claude_agent_sdk import CanUseToolShadowedWarning
except ImportError:                       # older SDKs: nothing to silence
    CanUseToolShadowedWarning = None

from backtalk import signals
from backtalk.config import CFG, DISCIPLINE
from backtalk.vlog import log

_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


SESSION_FILE = os.path.join(CFG["signals_dir"], ".backtalk_session")


class WarmBrain:
    def __init__(self, model: str | None = None, can_use_tool=None,
                 resume_id: str | None = None):
        self.provider = CFG.get("brain_provider") or ("gemini" if os.environ.get("GEMINI_API_KEY") else "claude")
        if self.provider == "gemini":
            self.model = model or CFG.get("gemini_model") or "gemini-3.5-flash-lite"
        else:
            self.model = model or CFG["model"]
        self._can_use_tool = can_use_tool
        self.session = {"turns": 0, "out_tokens": 0, "in_tokens": 0,
                        "cost": 0.0}
        self._client: ClaudeSDKClient | None = None
        self._resume_id = resume_id
        self._dirty = False
        self._gemini_chat = None
        self._gemini_client = None
        self._interrupted = False

    def _build_gemini_prompt(self):
        prompt_parts = []
        agent_dir = CFG.get("agent_dir") or "d:/agent"
        claude_md = os.path.join(agent_dir, "CLAUDE.md")
        if os.path.exists(claude_md):
            with open(claude_md, "r", encoding="utf-8") as f:
                prompt_parts.append(f.read())
        for extra in CFG.get("extra_dirs", []):
            vindex = os.path.join(extra, "VAULT-INDEX.md")
            if os.path.exists(vindex):
                with open(vindex, "r", encoding="utf-8") as f:
                    prompt_parts.append("\n\n---\nVAULT INDEX:\n" + f.read())
                break
        prompt_parts.append("\n\n" + DISCIPLINE)
        return "\n\n".join(prompt_parts)

    async def start(self):
        if self.provider == "gemini":
            from google import genai
            from google.genai import types
            from backtalk.tools import SYSTEM_TOOLS
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or CFG.get("gemini_api_key")
            self._gemini_client = genai.Client(api_key=api_key)
            system_prompt = self._build_gemini_prompt()
            self._gemini_chat = self._gemini_client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    tools=SYSTEM_TOOLS,
                )
            )
            log(f"[brain] Gemini connected ({self.model}) with {len(SYSTEM_TOOLS)} automation tools")
            return

        mode = CFG["permission_mode"]
        if mode == "default":
            mode = "ask"     # legacy alias, see config.py
        # backtalk's "ask" = the SDK's "default" mode with gated calls
        # routed to the spoken can_use_tool gate.
        sdk_mode = "default" if mode == "ask" else mode
        if sdk_mode == "bypassPermissions" and self._can_use_tool \
                and CanUseToolShadowedWarning:
            # Deliberate auto-approve: the SDK warns that the callback is
            # shadowed. That IS the chosen behavior, so boot quietly.
            warnings.filterwarnings("ignore",
                                    category=CanUseToolShadowedWarning)
        resume, self._resume_id = self._resume_id, None   # consume once

        def _opts(rid):
            return ClaudeAgentOptions(
                cwd=CFG["agent_dir"],
                model=self.model,
                system_prompt={"type": "preset", "preset": "claude_code",
                               "append": DISCIPLINE},
                include_partial_messages=True,
                permission_mode=sdk_mode,
                can_use_tool=self._can_use_tool,
                add_dirs=CFG["extra_dirs"],
                skills=CFG["visible_skills"],
                resume=rid,
            )
        if resume:
            try:
                self._client = ClaudeSDKClient(options=_opts(resume))
                await self._client.connect()
                log(f"[brain] resumed session {resume[:8]}")
                return
            except Exception as e:
                # a stale or invalid saved session must never brick the
                # launch. Fall back to a fresh conversation and say so.
                log(f"[brain] resume failed ({str(e)[:80]}), "
                    f"starting fresh")
                try:
                    await self._client.disconnect()
                except Exception:
                    pass
        self._client = ClaudeSDKClient(options=_opts(None))
        await self._client.connect()

    async def set_permission_mode(self, backtalk_mode: str):
        """Live flip, no reconnect, conversation intact ("ask" maps to
        the SDK's "default", whose gated calls hit the spoken gate)."""
        if self._client:
            sdk_mode = "default" if backtalk_mode == "ask" \
                else backtalk_mode
            await self._client.set_permission_mode(sdk_mode)

    async def context_usage(self):
        """The CLI's own context-window breakdown, or None."""
        try:
            return await self._client.get_context_usage()
        except Exception:
            return None

    def _remember_session(self, rm):
        """Persist the session id after a completed turn, so the next
        launch can reattach (config: resume_last_session). Must never
        break a turn; silence on any failure."""
        if not CFG.get("resume_last_session"):
            return
        sid = getattr(rm, "session_id", None)
        if not sid:
            return
        try:
            with open(SESSION_FILE, "w") as f:
                f.write(sid)
        except OSError:
            pass

    def _tally(self, rm, count_turn=True):
        """Session usage bookkeeping. Must never break a turn."""
        try:
            u = getattr(rm, "usage", None) or {}
            s = self.session
            if count_turn:
                s["turns"] += 1
            s["out_tokens"] += int(u.get("output_tokens") or 0)
            s["in_tokens"] += (int(u.get("input_tokens") or 0)
                               + int(u.get("cache_read_input_tokens")
                                     or 0))
            c = getattr(rm, "total_cost_usd", None)
            if c:
                s["cost"] += float(c)
        except Exception:
            pass

    async def _pull_rate_limits(self):
        """Ask the CLI outright how much of the plan is spent.

        A DIRECT QUERY, not the RateLimitEvent stream. The event fires
        rarely and usually arrives carrying resets_at with no utilization
        at all, so a listener built on it reports nothing most of the
        time -- which is exactly how this feature looked broken for its
        whole life. (Community fix, ai-visualizer issue #1.)

        THIS REACHES PAST THE SDK'S PUBLIC SURFACE ON PURPOSE, and a
        reader should know it rather than discover it. `get_usage` is a
        control request the bundled CLI answers but the SDK never wraps,
        so there is no supported call to make. The supported-looking
        alternative is a dead end and was tested as one: the terminal
        status line never fires in a headless session, so its numbers
        are unreachable from here.

        Which means this can stop working without anyone doing anything
        wrong, and the containment is the point. Every failure is
        swallowed and the readout simply goes quiet. It must never cost
        a turn, so it is also bounded -- an unanswered control request
        would otherwise hang the voice line mid-conversation."""
        if not CFG.get("show_usage"):
            return
        try:
            usage = await asyncio.wait_for(
                self._client._query._send_control_request(
                    {"subtype": "get_usage"}), 5)
            for window in ("five_hour", "seven_day"):
                w = (usage.get("rate_limits") or {}).get(window)
                if not w:
                    continue
                # Two spellings accepted deliberately: this shape is not
                # documented anywhere, so the cheap tolerance is worth
                # more than the tidiness. Both are percentages, and the
                # rest of the pipeline wants a 0..1 fraction.
                pct = w.get("utilization")
                if pct is None:
                    pct = w.get("used_percentage")
                pct = pct / 100 if pct is not None else None
                resets = w.get("resets_at")
                if isinstance(resets, str):
                    resets = int(datetime.fromisoformat(resets).timestamp())
                signals.set_rate_limit(window, pct, resets)
        except Exception:
            pass

    async def command(self, cmd: str) -> str:
        """Run a console slash command (/clear, /compact, /model,
        /effort) through the normal stream and return whatever text the
        CLI answered with (confirmations, errors). Slash-command replies
        arrive as COMPLETE AssistantMessages, not stream deltas, so
        ask_stream cannot see them. Bounded like reset_turn is: this
        stream is not trusted to always deliver, and an unbounded await
        here would deafen the whole voice loop. On timeout the pipe is
        left marked dirty so the next reset_turn drains or rebuilds."""
    async def command(self, cmd: str) -> str:
        if self.provider == "gemini":
            if cmd == "/clear":
                await self.start()
                return "Cleared. Fresh slate."
            return ""
        self._dirty = True
        await self._client.query(cmd)
        texts = []

        async def _collect():
            async for msg in self._client.receive_response():
                t = type(msg).__name__
                if t == "AssistantMessage":
                    for b in getattr(msg, "content", []) or []:
                        txt = getattr(b, "text", None)
                        if txt:
                            texts.append(txt)
                elif t == "ResultMessage":
                    self._dirty = False
                    self._tally(msg, count_turn=False)
                    self._remember_session(msg)
                    break

        try:
            await asyncio.wait_for(_collect(), 90)
        except asyncio.TimeoutError:
            log(f"[brain] console command timed out: {cmd!r}")
            return "error: the command timed out"
        return " ".join(texts).strip()

    async def interrupt(self):
        self._interrupted = True
        if self._client:
            await self._client.interrupt()

    async def reset_turn(self, timeout: float = 8.0):
        self._interrupted = False
        if self.provider == "gemini":
            self._dirty = False
            return
        if not self._client or not self._dirty:
            return
        try:
            await asyncio.wait_for(self._client.interrupt(), 5)
        except Exception:
            pass  # turn may already be over — the drain below is the point

        async def _drain() -> int:
            n = 0
            async for msg in self._client.receive_response():
                n += 1
                if type(msg).__name__ == "ResultMessage":
                    break
            return n

        try:
            drained = await asyncio.wait_for(_drain(), timeout)
            log(f"[brain] interrupted turn drained ({drained} stale messages)")
            self._dirty = False
        except Exception:
            log("[brain] stream desynced beyond repair — rebuilding the "
                "session (conversation memory for this session resets)")
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
            await self.start()
            self._dirty = False

    async def stop(self):
        if self._client:
            await self._client.disconnect()
            self._client = None
        self._gemini_chat = None
        self._gemini_client = None

    async def ask_stream(self, utterance: str):
        if self.provider == "gemini":
            self._dirty = True
            self._interrupted = False
            buf = ""
            loop = asyncio.get_running_loop()

            fallback_models = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.1-flash-lite"]
            if self.model not in fallback_models:
                fallback_models.insert(0, self.model)

            for attempt_model in fallback_models:
                if self.model != attempt_model or self._gemini_chat is None:
                    try:
                        from google.genai import types
                        self.model = attempt_model
                        system_prompt = self._build_gemini_prompt()
                        self._gemini_chat = self._gemini_client.chats.create(
                            model=self.model,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.7,
                                tools=SYSTEM_TOOLS,
                            )
                        )
                        log(f"[brain] Gemini switched to model ({self.model})")
                    except Exception as e:
                        log(f"[brain] Failed to switch to {attempt_model}: {e}")
                        continue

                def _get_stream():
                    return self._gemini_chat.send_message_stream(utterance)

                try:
                    stream = await loop.run_in_executor(None, _get_stream)
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        log(f"[brain] Gemini quota reached on {self.model}, attempting fallback...")
                        self._gemini_chat = None
                        continue
                    log(f"[brain] Gemini query error: {e}")
                    self._dirty = False
                    return

                def _next_chunk(it):
                    try:
                        return next(it)
                    except StopIteration:
                        return None
                    except Exception as e:
                        log(f"[brain] Gemini stream chunk error: {e}")
                        return ("ERROR", e)

                had_quota_err = False
                yielded_any = False

                while not self._interrupted:
                    chunk = await loop.run_in_executor(None, _next_chunk, stream)
                    if chunk is None:
                        break
                    if isinstance(chunk, tuple) and chunk[0] == "ERROR":
                        err_str = str(chunk[1])
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            had_quota_err = True
                        break
                    text = getattr(chunk, "text", "") or ""
                    if not text:
                        continue
                    buf += text
                    while True:
                        m = _SENTENCE_END.search(buf)
                        if not m:
                            break
                        sentence, buf = buf[:m.end()].strip(), buf[m.end():]
                        if sentence:
                            yielded_any = True
                            yield sentence

                if had_quota_err and not yielded_any:
                    log(f"[brain] Quota error on {self.model}, trying next available model...")
                    self._gemini_chat = None
                    buf = ""
                    continue

                tail = buf.strip()
                if tail and not self._interrupted:
                    yield tail
                self._dirty = False
                self.session["turns"] += 1
                return

            self._dirty = False
            return

        self._dirty = True             # in flight until its ResultMessage
        await self._client.query(utterance)
        buf = ""
        async for msg in self._client.receive_response():
            t = type(msg).__name__
            if t == "StreamEvent":
                ev = getattr(msg, "event", {}) or {}
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta", {}) or {}
                    if delta.get("type") == "text_delta":
                        buf += delta.get("text", "")
                        # emit any complete sentences
                        while True:
                            m = _SENTENCE_END.search(buf)
                            if not m:
                                break
                            sentence, buf = (buf[:m.end()].strip(),
                                             buf[m.end():])
                            if sentence:
                                yield sentence
                elif ev.get("type") == "content_block_stop":
                    # End of a speech block (e.g. right before a tool
                    # call): flush NOW. Without this, pre-tool filler
                    # ("On it — let me grab that.") sits silent in the
                    # buffer through the whole tool run, then plays
                    # glued to the answer: long dead air, then two
                    # thoughts at once.
                    tail = buf.strip()
                    buf = ""
                    if tail:
                        yield tail
            elif t == "ResultMessage":
                self._dirty = False    # turn fully consumed — pipe aligned
                self._tally(msg)
                self._remember_session(msg)
                await self._pull_rate_limits()
                break
        tail = buf.strip()
        if tail:
            yield tail


if __name__ == "__main__":
    import time

    async def demo():
        b = WarmBrain()
        await b.start()
        for prompt in ("Voice check: greet me in one sentence.",
                       "And what's two plus two, spoken like yourself?"):
            t0 = time.time()
            async for s in b.ask_stream(prompt):
                print(f"  ({time.time()-t0:4.1f}s) {s}", flush=True)
        await b.stop()

    asyncio.run(demo())
