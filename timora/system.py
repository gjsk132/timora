import re
import subprocess


def idle_seconds():
    """Seconds with no keyboard/mouse input. Returns 0 on failure."""
    try:
        out = subprocess.run(["ioreg", "-c", "IOHIDSystem"],
                             capture_output=True, text=True, timeout=2).stdout
        m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if m:
            return int(m.group(1)) / 1e9
    except Exception:
        pass
    return 0.0
