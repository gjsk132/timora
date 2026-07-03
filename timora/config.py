import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA        = os.path.join(PROJECT_DIR, "data.json")
REPORT      = os.path.join(PROJECT_DIR, "report.html")
LOCK        = os.path.join(PROJECT_DIR, ".tracker.lock")
BUNDLE_ICON = os.path.join(PROJECT_DIR, "Timora.app", "Contents", "Resources", "AppIcon.icns")
BUNDLE_ID   = "local.timora"

ACCENT         = "#6366f1"
TASK_ICON      = "circle.fill"
IDLE_LIMIT     = 15 * 60
STALE_LIMIT    = 60 * 60
ENTRY_MENU_MAX = 15
