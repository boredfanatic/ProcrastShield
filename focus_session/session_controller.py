# hybrid_session_controller.py

import time
import json
from datetime import datetime
import pygetwindow as gw

# -----------------------
# Configuration
# -----------------------
FOCUS_KEYWORDS = ["Google Docs", "VS Code", "LeetCode", "Notion", "Jupyter Notebook"]
DISTRACTION_KEYWORDS = ["Wattpad", "Netflix", "Instagram"]
ASK_EVERY_TIME = ["YouTube", "Reddit"]
CHECK_INTERVAL = 5  # seconds
LOG_FILE = "focus_session_log.json"
USER_MEMORY_FILE = "user_memory.json"

# -----------------------
# Load user memory
# -----------------------
try:
    with open(USER_MEMORY_FILE, "r") as f:
        user_memory = json.load(f)
except FileNotFoundError:
    user_memory = {}  # {window_title: "Focus"/"Distraction"}

# -----------------------
# Helper Functions
# -----------------------
def get_active_window():
    try:
        win = gw.getActiveWindow()
        if win:
            return win.title
    except Exception:
        return None

def classify_window(title):
    if title is None:
        return "Unknown"

    # Check user memory first
    if title in user_memory:
        return user_memory[title]

    # Ask every time list
    if any(site.lower() in title.lower() for site in ASK_EVERY_TIME):
        while True:
            ans = input(f"Is this Focus? '{title}' (Y/N): ").strip().lower()
            if ans in ["y", "n"]:
                result = "Focus" if ans == "y" else "Distraction"
                user_memory[title] = result  # save for future
                with open(USER_MEMORY_FILE, "w") as f:
                    json.dump(user_memory, f, indent=4)
                return result

    # Keyword lists
    if any(keyword.lower() in title.lower() for keyword in FOCUS_KEYWORDS):
        return "Focus"
    if any(keyword.lower() in title.lower() for keyword in DISTRACTION_KEYWORDS):
        return "Distraction"

    # Unknown, ask user
    while True:
        ans = input(f"Unknown window/tab detected. Is this Focus? '{title}' (Y/N): ").strip().lower()
        if ans in ["y", "n"]:
            result = "Focus" if ans == "y" else "Distraction"
            user_memory[title] = result
            with open(USER_MEMORY_FILE, "w") as f:
                json.dump(user_memory, f, indent=4)
            return result

# -----------------------
# Main Session Function
# -----------------------
def start_focus_session():
    print("Focus session started! Press Ctrl+C to end.")
    start_time = datetime.now()
    log = []
    focus_seconds = 0
    distraction_seconds = 0

    try:
        while True:
            active_window = get_active_window()
            status = classify_window(active_window)
            timestamp = datetime.now().isoformat()

            # Update counters
            if status == "Focus":
                focus_seconds += CHECK_INTERVAL
            else:
                distraction_seconds += CHECK_INTERVAL

            log.append({
                "time": timestamp,
                "active_window": active_window,
                "status": status
            })

            print(f"[{timestamp}] Active window: {active_window} → {status}")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        end_time = datetime.now()
        duration_minutes = round((end_time - start_time).total_seconds() / 60, 2)
        focus_minutes = round(focus_seconds / 60, 2)
        distraction_minutes = round(distraction_seconds / 60, 2)
        focus_percent = round((focus_seconds / (focus_seconds + distraction_seconds)) * 100, 2) \
                        if (focus_seconds + distraction_seconds) > 0 else 0

        # Prepare session data
        session_data = {
            "start_time": str(start_time),
            "end_time": str(end_time),
            "duration_minutes": duration_minutes,
            "focus_minutes": focus_minutes,
            "distraction_minutes": distraction_minutes,
            "focus_percent": focus_percent,
            "window_log": log
        }

        # Save to JSON
        try:
            with open(LOG_FILE, "r") as f:
                all_sessions = json.load(f)
        except FileNotFoundError:
            all_sessions = []

        all_sessions.append(session_data)

        with open(LOG_FILE, "w") as f:
            json.dump(all_sessions, f, indent=4)

        print("\n--- Session Summary ---")
        print(f"Duration: {duration_minutes} min")
        print(f"Focused: {focus_minutes} min ({focus_percent}%)")
        print(f"Distractions: {distraction_minutes} min")
        print(f"Session data saved to {LOG_FILE}")
        print("------------------------")

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    start_focus_session()