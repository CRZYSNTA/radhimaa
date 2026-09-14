"""
JARVIS V3.0 - Media & Content Intelligence Tools
Provides media player automation for Spotify and YouTube video transcript
extraction and AI summarization.
"""

from __future__ import annotations

import re
import urllib.parse
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("JARVIS.Tools.Media")

def spotify_control(action: str = "play", query: Optional[str] = None) -> str:
    """
    Controls Spotify desktop playback and search.
    Args:
        action: 'play', 'pause', 'play_pause', 'next', 'previous', 'mute', 'volume_up', 'volume_down'
        query: Optional track or artist search string.
    """
    act = action.lower().strip()
    try:
        import pyautogui
        old_fs = getattr(pyautogui, "FAILSAFE", True)
        pyautogui.FAILSAFE = False
        try:
            if query:
                import webbrowser
                encoded = urllib.parse.quote(query)
                # Use Spotify URI protocol to search or play
                webbrowser.open(f"spotify:search:{encoded}")
                return f"Searching Spotify for '{query}', sir."

            if act in ("play", "pause", "play_pause", "toggle"):
                pyautogui.press("playpause")
                return "Toggled Spotify playback."
            elif act in ("next", "skip"):
                pyautogui.press("nexttrack")
                return "Skipped to the next track."
            elif act in ("previous", "prev", "back"):
                pyautogui.press("prevtrack")
                return "Returned to previous track."
            elif act in ("volume_up", "louder"):
                pyautogui.press("volumeup", presses=5)
                return "Increased media volume."
            elif act in ("volume_down", "quieter"):
                pyautogui.press("volumedown", presses=5)
                return "Decreased media volume."
            elif act == "mute":
                pyautogui.press("volumemute")
                return "Toggled media mute."
            else:
                pyautogui.press("playpause")
                return f"Sent playback action: {action}"
        finally:
            pyautogui.FAILSAFE = old_fs

    except Exception as e:
        logger.error(f"[Spotify Error]: {e}")
        return f"Unable to control Spotify: {e}"

def get_youtube_transcript_and_summary(url_or_video_id: str) -> str:
    """
    Fetches transcript of a YouTube video and generates a concise summary.
    """
    if not url_or_video_id:
        return "Please provide a valid YouTube URL or video ID, sir."

    video_id = url_or_video_id.strip()
    if "youtube.com" in video_id or "youtu.be" in video_id:
        # Extract video ID
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_id)
        if match:
            video_id = match.group(1)
        else:
            return f"Could not extract a valid YouTube video ID from '{url_or_video_id}'."

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry["text"] for entry in transcript_list])
        
        # Summarize using active AI Provider if available
        try:
            from ai.provider import get_ai_provider
            provider = get_ai_provider()
            prompt = (
                f"Please provide a concise, structured summary with key takeaways from this YouTube video transcript:\n\n"
                f"{full_text[:6000]}"
            )
            summary = provider.generate_response(prompt)
            return f"### YouTube Video Summary:\n\n{summary}"
        except Exception:
            # Fallback to extractive snippet
            snippet = full_text[:800] + ("..." if len(full_text) > 800 else "")
            return f"### YouTube Transcript Excerpt:\n\n{snippet}"

    except ImportError:
        return "YouTube transcript module is not installed. Install 'youtube-transcript-api' to enable video summarization."
    except Exception as e:
        logger.error(f"[YouTube Transcript Error]: {e}")
        return f"Unable to retrieve transcript for video '{video_id}': {e}"


def download_youtube_audio(url_or_query: str) -> str:
    """
    Downloads the audio stream from a YouTube video into the JARVIS sandbox folder.
    Args:
        url_or_query: YouTube URL or search title.
    """
    if not url_or_query:
        return "Please provide a YouTube URL or query to download, sir."

    import os
    import subprocess
    from pathlib import Path
    import config

    sandbox = Path(config.SANDBOX_DIR).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    out_template = str(sandbox / "%(title)s.%(ext)s")

    target = url_or_query.strip()
    if not target.startswith("http"):
        target = f"ytsearch1:{target}"

    try:
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--no-playlist",
            "-o", out_template,
            target
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            return f"Audio downloaded successfully to the JARVIS sandbox directory: `{sandbox}`, sir."
        else:
            return f"Download failed: {res.stderr.strip() or 'yt-dlp error'}"
    except FileNotFoundError:
        return "yt-dlp tool is not found on your system path. Install with 'pip install yt-dlp' to enable audio downloads."
    except Exception as e:
        return f"Failed to download audio: {e}"


def download_youtube_video(url_or_query: str) -> str:
    """
    Downloads a YouTube video in MP4 format into the JARVIS sandbox folder.
    """
    if not url_or_query:
        return "Please provide a YouTube URL or query, sir."

    import subprocess
    from pathlib import Path
    import config

    sandbox = Path(config.SANDBOX_DIR).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    out_template = str(sandbox / "%(title)s.%(ext)s")

    target = url_or_query.strip()
    if not target.startswith("http"):
        target = f"ytsearch1:{target}"

    try:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--no-playlist",
            "-o", out_template,
            target
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if res.returncode == 0:
            return f"Video downloaded successfully to the JARVIS sandbox directory: `{sandbox}`, sir."
        else:
            return f"Download failed: {res.stderr.strip() or 'yt-dlp error'}"
    except FileNotFoundError:
        return "yt-dlp tool is not found on your system path. Install with 'pip install yt-dlp' to enable video downloads."
    except Exception as e:
        return f"Failed to download video: {e}"

