"""
=============================================================================
JARVIS Sleek High-Visibility Floating Siri Widget (Thread-Safe Tkinter)
=============================================================================
Goal: Thread-safe Tkinter overlay widget using root.after() for UI updates.

Fixes Applied:
 - [P1 Fix]: Dispatched all UI updates to main GUI thread using root.after()

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import threading
import time
import tkinter as tk

try:
    import jarvis_stage1
except Exception:
    jarvis_stage1 = None


class SiriWidgetOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS Assistant Widget")
        
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = int((screen_w - 220) / 2)
        pos_y = int((screen_h - 220) / 2)
        self.root.geometry(f"220x220+{pos_x}+{pos_y}")

        BG_COLOR = "#0f172a"
        BORDER_COLOR = "#38bdf8"

        self.root.config(bg=BORDER_COLOR, bd=2)

        self.card = tk.Frame(self.root, bg=BG_COLOR)
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas = tk.Canvas(self.card, width=216, height=150, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill="x", expand=False)

        self.outer_ring = self.canvas.create_oval(48, 15, 168, 135, outline="#38bdf8", width=5)
        self.middle_ring = self.canvas.create_oval(63, 30, 153, 120, outline="#0284c7", width=3)
        self.inner_core = self.canvas.create_oval(78, 45, 138, 105, fill="#0369a1", outline="")
        self.center_dot = self.canvas.create_oval(96, 63, 120, 87, fill="#ffffff", outline="")

        self.title_label = tk.Label(
            self.card,
            text="🤖 JARVIS ASSISTANT",
            bg=BG_COLOR,
            fg="#38bdf8",
            font=("Segoe UI", 10, "bold")
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

        self.start_x = 0
        self.start_y = 0
        
        self.root.bind("<Button-1>", self.on_click)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.is_listening = False

    def _update_ui_internal(self, title, status, outer_color, core_color, status_fg):
        """Internal UI update method scheduled on main Tkinter thread."""
        self.canvas.itemconfig(self.outer_ring, outline=outer_color)
        self.canvas.itemconfig(self.inner_core, fill=core_color)
        self.title_label.config(text=title, fg=outer_color)
        self.status_label.config(text=status, fg=status_fg)

    def set_widget_state(self, title, status, outer_color, core_color, status_fg):
        """Thread-safe UI update wrapper using root.after()."""
        self.root.after(0, lambda: self._update_ui_internal(title, status, outer_color, core_color, status_fg))

    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if not self.is_listening:
            threading.Thread(target=self.listen_and_respond, daemon=True).start()

    def on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.start_x)
        y = self.root.winfo_y() + (event.y - self.start_y)
        self.root.geometry(f"220x220+{x}+{y}")

    def listen_and_respond(self):
        if self.is_listening:
            return
        self.is_listening = True

        # Thread-safe UI update
        self.set_widget_state("🎤 LISTENING...", "Speak into microphone...", "#4ade80", "#16a34a", "#4ade80")

        try:
            import audio_feedback
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

        # Thread-safe UI update back to Idle
        self.set_widget_state("🤖 JARVIS ASSISTANT", "Click or Say 'Jarvis'", "#38bdf8", "#0369a1", "#94a3b8")
        self.is_listening = False

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SiriWidgetOverlay()
    app.run()
