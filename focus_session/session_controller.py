import os
import json
import time
from datetime import datetime, timedelta
import re
import pygetwindow as gw

CHECK_INTERVAL = 5  # seconds

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data_storage'))
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'focus_session_log.json')
MEMORY_FILE = os.path.join(LOG_DIR, 'tab_memory.json')
ACTIVITY_FILE = os.path.join(LOG_DIR, "activity_log.json")

memory = {"site_memory": {}, "tab_memory": {}, "always_ask": {}, "browser_apps": {}}

if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r") as f:
            content = f.read().strip()
            if content:
                loaded = json.loads(content)
                memory.update(loaded)
    except:
        print("Warning: memory file corrupted. Starting fresh.")

session_log = []
focus_streak = 0
distraction_streak = 0

def parse_window_title(raw_title):
    raw_title = raw_title.strip()
    raw_title = re.sub(r"^\(\d+\)\s*", "", raw_title)
    if " - " in raw_title:
        parts = raw_title.rsplit(" - ", 1)
        content = parts[0].strip()
        app_name = parts[1].strip()
    else:
        content = raw_title
        app_name = "Unknown"
    return app_name, content

def get_latest_web_domain():
    try:
        if not os.path.exists(ACTIVITY_FILE):
            return None
        with open(ACTIVITY_FILE, "r") as f:
            lines = f.readlines()
        for line in reversed(lines):
            entry = json.loads(line.strip())
            if entry.get("type") == "web":
                return entry.get("name")
    except:
        pass
    return None

def format_window_title(raw_title):
    app_name, content = parse_window_title(raw_title)
    if app_name in memory["browser_apps"]:
        is_browser = memory["browser_apps"][app_name]
    else:
        ans = input(f"\nIs '{app_name}' a browser? (Y/N): ").strip().lower()
        is_browser = ans == "y"
        memory["browser_apps"][app_name] = is_browser
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)

    if is_browser:
        domain = get_latest_web_domain()
        site = domain if domain else app_name
        display = f"{app_name} -> {domain}" if domain else f"{app_name} -> {content}"
    else:
        site = app_name
        display = f"{app_name} -> {content}"
    return display, site

def get_active_window():
    try:
        window = gw.getActiveWindow()
        if window and window.title:
            return window.title
    except:
        pass
    return ""

def log_unified_activity(name, activity_type):
    entry = {"type": activity_type, "name": name, "timestamp": str(datetime.now())}
    with open(ACTIVITY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def log_activity(title, status):
    global focus_streak, distraction_streak
    entry = {"timestamp": str(datetime.now()), "window": title, "status": status}
    session_log.append(entry)
    log_unified_activity(title, "app")

    if status == "Focus":
        focus_streak += 1
        distraction_streak = 0
        print(f"🔥 Focus streak: {focus_streak}")
    elif status == "Distraction":
        distraction_streak += 1
        focus_streak = 0
        print(f"⚠ Distraction streak: {distraction_streak}")
    else:
        print(f"⏳ Unclassified: {title}")

    print(f"[{entry['timestamp']}] Active window: {title} → {status}")

def is_focus(formatted_title, site):
    if formatted_title in memory["tab_memory"]:
        return memory["tab_memory"][formatted_title]
    if site in memory["site_memory"]:
        return memory["site_memory"][site]

    if site in memory["always_ask"]:
        config = memory["always_ask"][site]
        if config["mode"] == "always":
            pass
        elif config["mode"] == "interval":
            last = config.get("last_asked")
            if last:
                last_time = datetime.fromisoformat(last)
                if datetime.now() - last_time < timedelta(minutes=5):
                    return None
            memory["always_ask"][site]["last_asked"] = str(datetime.now())
    return None

def ask_focus(formatted_title, site):
    while True:
        ans = input(f"\nUnknown window/tab detected:\n{formatted_title}\nIs this Focus? (Y/N): ").strip().lower()
        if ans in ["y", "n"]:
            status = "Focus" if ans == "y" else "Distraction"
            remember = input("\nRemember decision for:\n1. This tab only\n2. Entire app/domain\n3. Ask settings\nChoice: ").strip()
            if remember == "1":
                memory["tab_memory"][formatted_title] = status
            elif remember == "2":
                memory["site_memory"][site] = status
            elif remember == "3":
                print("\nHow to handle this site?\n1. Ask every time\n2. Check occasionally (every 5 mins)")
                mode_choice = input("Choice: ").strip()
                if mode_choice == "1":
                    memory["always_ask"][site] = {"mode": "always"}
                elif mode_choice == "2":
                    memory["always_ask"][site] = {"mode": "interval", "last_asked": None}
            with open(MEMORY_FILE, "w") as f:
                json.dump(memory, f, indent=4)
            return status
        print("Please enter Y or N.")

def session_summary():
    total_time = len(session_log) * CHECK_INTERVAL / 60
    focus_time = sum(1 for e in session_log if e["status"] == "Focus") * CHECK_INTERVAL / 60
    distraction_time = total_time - focus_time
    focus_percent = (focus_time / total_time * 100) if total_time else 0

    print("\n--- Session Summary ---")
    print(f"Duration: {total_time:.2f} min")
    print(f"Focused: {focus_time:.2f} min ({focus_percent:.1f}%)")
    print(f"Distractions: {distraction_time:.2f} min")

    distractions_per_app = {}
    for e in session_log:
        if e["status"] == "Distraction":
            name = e["window"]
            distractions_per_app[name] = distractions_per_app.get(name, 0) + CHECK_INTERVAL

    if distractions_per_app:
        print("\nTop distractions:")
        for app, secs in distractions_per_app.items():
            print(f"{app} → {secs/60:.2f} min")

    with open(LOG_FILE, "w") as f:
        json.dump(session_log, f, indent=4)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)
    print(f"Session data saved to {LOG_FILE}")

def main():
    print("Focus session started! Press Ctrl+C to end.")
    try:
        while True:
            raw_title = get_active_window()
            if not raw_title.strip():
                time.sleep(CHECK_INTERVAL)
                continue
            formatted_title, site = format_window_title(raw_title)
            status = is_focus(formatted_title, site)
            if status is None:
                log_activity(formatted_title, "Unclassified")
                status = ask_focus(formatted_title, site)
            log_activity(formatted_title, status)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        session_summary()

if __name__ == "__main__":
    main()