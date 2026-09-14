# 🧠 Lessons Learned & System Corrections

*Records corrections and heuristics so JARVIS never makes the same mistake twice.*

- [Rule] Never import or couple tools with external repositories; keep JARVIS 100% standalone.
- [Rule] Always verify audio device availability before initializing sounddevice streams to prevent test hangs.
- [Rule] Always initialize QApplication before instantiating PySide6 QWidget instances.
