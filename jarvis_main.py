"""
=============================================================================
JARVIS: Main Unified System Orchestrator (with Dual Calling Commands)
=============================================================================
Summon Triggers:
 1. 🗣️ Voice Command: Say 'Jarvis'
 2. 👏 Double Clap: Clap hands twice (Clap... Clap!)

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import sys
import os
import threading

import jarvis_stage1
import gesture_mouse
import clap_wake_engine
import database

def run_dual_summoning_engine():
    """Runs the Dual Trigger Engine (Voice 'Jarvis' + Double Clap sound detector)."""
    engine = clap_wake_engine.DualTriggerEngine()
    engine.start()

def run_gesture_control():
    """Launches the Air-Gesture Virtual Mouse in camera window."""
    mouse = gesture_mouse.GestureMouse()
    mouse.run()

def run_server():
    """Launches the FastAPI Cross-Device Server."""
    import uvicorn
    import server
    print("\n🚀 Launching JARVIS Central Server on http://localhost:8000 ...")
    uvicorn.run(server.app, host="0.0.0.0", port=8000)

def main():
    database.init_db()
    
    print("\n" + "=" * 65)
    print("   🤖 WELCOME TO YOUR PERSONAL JARVIS AI ASSISTANT SYSTEM")
    print("=" * 65)
    print("   Select an Operating Mode:")
    print("   [1] Dual Calling Assistant (Voice 'Jarvis' OR Double Clap 👏)")
    print("   [2] Air-Gesture Virtual Mouse (Control cursor with webcam)")
    print("   [3] Start Central Web Server (Access JARVIS from phone/web)")
    print("   [4] Simple Terminal Text Console")
    print("   [5] Exit")
    print("=" * 65)

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        run_dual_summoning_engine()
    elif choice == "2":
        run_gesture_control()
    elif choice == "3":
        run_server()
    elif choice == "4":
        jarvis_stage1.main()
    elif choice == "5":
        print("Powering down JARVIS. Good day, sir!")
        sys.exit(0)
    else:
        print("Invalid choice. Please run again and select 1 to 5.")

if __name__ == "__main__":
    main()
