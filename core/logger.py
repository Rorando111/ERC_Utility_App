import csv
from datetime import datetime

def log_action(username, action, filenames=None):
    filenames = ", ".join(filenames) if filenames else ""
    log_file = f"activity_log_{username}.csv"

    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            action,
            filenames
        ])
