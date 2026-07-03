import os
import atexit
import subprocess

from .config import LOCK


def _is_tracker_pid(pid):
    if pid <= 0 or pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, timeout=2).stdout
        return "timora" in out
    except Exception:
        return True


def _release_lock():
    try:
        with open(LOCK) as f:
            if int((f.read().strip() or "0")) == os.getpid():
                os.remove(LOCK)
    except Exception:
        pass


def already_running():
    """True if another instance holds the lock; otherwise claim it."""
    try:
        if os.path.exists(LOCK):
            with open(LOCK) as f:
                pid = int((f.read().strip() or "0"))
            if _is_tracker_pid(pid):
                return True
    except Exception:
        pass
    try:
        with open(LOCK, "w") as f:
            f.write(str(os.getpid()))
        atexit.register(_release_lock)
    except Exception:
        pass
    return False
