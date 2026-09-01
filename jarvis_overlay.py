"""
=============================================================================
JARVIS Siri Assistant Floating Widget (High-Visibility & Taskbar Enabled)
=============================================================================
Fixes Applied:
 - Taskbar Icon enabled (no overrideredirect hiding)
 - Forced foreground focus (.lift() & .focus_force())
 - 100% visible over all browser and desktop windows

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import threading
import time
import tkinter as tk
import audio_feedback

try:
    import jarvis_stage1
except Exception:
    jarvis_stage1 = None


class SiriWidgetOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 JARVIS Siri Assistant")
        
        # Always-On-Top and Force Foreground Focus
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.attributes("-alpha", 0.96) # Sleek 96% opacity

        # Size: 240x260 pixels, Centered on Screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = int((screen_w - 240) / 2)
        pos_y = int((screen_h - 260) / 2)
        self.root.geometry(f"240x260+{pos_x}+{pos_y}")

        BG_COLOR = "#0f172a"
        BORDER_COLOR = "#38bdf8"

        self.root.config(bg=BG_COLOR)

        self.card = tk.Frame(self.root, bg=BG_COLOR)
        self.card.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas = tk.Canvas(self.card, width=230, height=150, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill="x", expand=False)

        # Draw Glowing Siri Rings & Core
        self.outer_ring = self.canvas.create_oval(55, 15, 175, 135, outline="#38bdf8", width=5)
        self.middle_ring = self.canvas.create_oval(70, 30, 160, 120, outline="#0284c7", width=3)
        self.inner_core = self.canvas.create_oval(85, 45, 145, 105, fill="#0369a1", outline="")
        self.center_dot = self.canvas.create_oval(103, 63, 127, 87, fill="#ffffff", outline="")

        self.title_label = tk.Label(
            self.card,
            text="🤖 JARVIS ASSISTANT",
            bg=BG_COLOR,
            fg="#38bdf8",
            font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(pady=(0, 2))

        self.status_label = tk.Label(
            self.card,
            text="Click or Say 'Jarvis'",
            bg=BG_COLOR,
            fg="#94a3b8",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(pady=(0, 8))

        # Click Event Binds
        self.root.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-1>", self.on_click)

        self.is_listening = False
        
        # Bring to front on creation
        self.root.after(100, lambda: (self.root.lift(), self.root.focus_force()))

    def _update_ui_internal(self, title, status, outer_color, core_color, status_fg):
        self.canvas.itemconfig(self.outer_ring, outline=outer_color)
        self.canvas.itemconfig(self.inner_core, fill=core_color)
        self.title_label.config(text=title, fg=outer_color)
        self.status_label.config(text=status, fg=status_fg)

    def set_widget_state(self, title, status, outer_color, core_color, status_fg):
        self.root.after(0, lambda: self._update_ui_internal(title, status, outer_color, core_color, status_fg))

    def on_click(self, event):
        if not self.is_listening:
            threading.Thread(target=self.listen_and_respond, daemon=True).start()

    def listen_and_respond(self):
        if self.is_listening:
            return
        self.is_listening = True

        self.set_widget_state("🎤 LISTENING...", "Speak into microphone...", "#4ade80", "#16a34a", "#4ade80")

        try:
            audio_feedback.play_instant_yes_sir()
        except Exception:
            pass

        if jarvis_stage1:
            user_text = jarvis_stage1.listen_to_user()
            if user_text:
                self.set_widget_state("🧠 THINKING...", f"'{user_text}'", "#c084fc", "#9333ea", "#c084fc")
                reply = jarvis_stage1.query_brain(user_text)
                jarvis_stage1.speak(reply)
        else:
            time.sleep(2)

        self.set_widget_state("🤖 JARVIS ASSISTANT", "Click or Say 'Jarvis'", "#38bdf8", "#0369a1", "#94a3b8")
        self.is_listening = False

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SiriWidgetOverlay()
    app.run()
