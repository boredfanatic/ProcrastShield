# focus_session/session_controller.py

import time
import json
from datetime import datetime
import os
import re
import pygetwindow as gw

# --- CONFIG ---
CHECK_INTERVAL = 5  # seconds between checks
ALWAYS_ASK = ['YouTube', 'Reddit']  # Tabs always prompt for focus
LOG_DIR = '../data_storage'
LOG_FILE = 'focus_session_log.json'
MEMORY_FILE = 'tab_memory.json'  # Stores previous tab decisions

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Load memory of tab classifications
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, 'r') as f:
        tab_memory = json.load(f)
else:
    tab_memory = {}

# Load previous session log
session_log_path = os.path.join(LOG_DIR, LOG_FILE)
session_log = []

# -------------------
# Utility functions
# -------------------

def detect_site_from_title(title):
    """
    Detect website name from tab title keywords
    """

    title_lower = title.lower()

    site_map = {
        "chatgpt": "ChatGPT",
        "github": "GitHub",
        "youtube": "YouTube",
        "gmail": "Gmail",
        "google drive": "Google Drive",
        "reddit": "Reddit",
        "whatsapp": "WhatsApp",
        "discord": "Discord",
        "stackoverflow": "StackOverflow",
        "meet": "Google Meet"
    }

    for keyword, site in site_map.items():
        if keyword in title_lower:
            return site

    return None


def format_window_title(raw_title):
    """
    Converts raw window title into standardized format:
    <App Name> -> <Website>/<Tab Name>
    """

    raw_title = raw_title.strip()

    # Remove notification numbers like (1) WhatsApp
    raw_title = re.sub(r"^\(\d+\)\s*", "", raw_title)

    # Detect application
    app_name = "Other"

    if "Visual Studio Code" in raw_title:
        app_name = "VS Code"
        content = raw_title.replace(" - Visual Studio Code", "")

    elif "Opera" in raw_title:
        app_name = "Opera"
        content = raw_title.replace(" - Opera", "")

    elif "Chrome" in raw_title:
        app_name = "Chrome"
        content = raw_title.replace(" - Chrome", "")

    elif "Firefox" in raw_title:
        app_name = "Firefox"
        content = raw_title.replace(" - Firefox", "")

    else:
        content = raw_title

    content = content.strip()

    # Detect website if browser
    if app_name in ["Opera", "Chrome", "Firefox"]:

        site = detect_site_from_title(content)

        if site:
            content = f"{site}/{content}"

    if not content:
        content = "Unknown"

    return f"{app_name} -> {content}"


# -------------------
# Active window detection
# -------------------

def get_active_window():
    """
    Automatically detect the active window title.
    """

    try:
        window = gw.getActiveWindow()

        if window and window.title:
            return window.title

    except:
        pass

    return ""


# -------------------
# Session functions
# -------------------

def log_activity(title, status):

    entry = {
        "timestamp": str(datetime.now()),
        "window": title,
        "status": status
    }

    session_log.append(entry)

    print(f"[{entry['timestamp']}] Active window: {title} → {status}")


def is_focus(formatted_title):

    # Check memory first
    for key, value in tab_memory.items():
        if key.lower() in formatted_title.lower():
            return value

    # Always ask for certain websites
    if any(site.lower() in formatted_title.lower() for site in ALWAYS_ASK):
        pass

    # Ask user
    while True:

        ans = input(
            f"Unknown window/tab detected. Is this Focus? '{formatted_title}' (Y/N): "
        ).strip().lower()

        if ans in ["y", "n"]:

            status = "Focus" if ans == "y" else "Distraction"

            remember = input(
                "Do you want ProcrastShield to remember this for future sessions? (Y/N): "
            ).strip().lower()

            if remember == "y":

                tab_memory[formatted_title] = status

                with open(MEMORY_FILE, "w") as f:
                    json.dump(tab_memory, f, indent=4)

            return status

        else:
            print("Please enter Y or N.")


def session_summary():

    total_time = len(session_log) * CHECK_INTERVAL / 60
    focus_time = sum(
        1 for e in session_log if e["status"] == "Focus"
    ) * CHECK_INTERVAL / 60

    distraction_time = total_time - focus_time

    focus_percent = (focus_time / total_time * 100) if total_time else 0

    distractions_per_app = {}

    for e in session_log:

        if e["status"] == "Distraction":

            name = e["window"]

            distractions_per_app[name] = (
                distractions_per_app.get(name, 0) + CHECK_INTERVAL
            )

    print("\n--- Session Summary ---")
    print(f"Duration: {total_time:.2f} min")
    print(f"Focused: {focus_time:.2f} min ({focus_percent:.1f}%)")
    print(f"Distractions: {distraction_time:.2f} min")

    if distractions_per_app:

        print("\nTop distractions:")

        for app, secs in distractions_per_app.items():
            print(f"{app} → {secs/60:.2f} min")

    # Save log
    with open(session_log_path, "w") as f:
        json.dump(session_log, f, indent=4)

    print(f"Session data saved to {session_log_path}")


# -------------------
# Main loop
# -------------------

def main():

    print("Focus session started! Press Ctrl+C to end.")

    try:

        while True:

            raw_title = get_active_window()

            if not raw_title.strip():
                time.sleep(CHECK_INTERVAL)
                continue

            formatted_title = format_window_title(raw_title)

            status = is_focus(formatted_title)

            log_activity(formatted_title, status)

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:

        session_summary()


if __name__ == "__main__":
    main()