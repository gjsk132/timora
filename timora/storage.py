import os
import json
import time
import uuid
import shutil

from .config import DATA


class Store:
    """Owns the on-disk database and read queries over it."""

    def __init__(self):
        self.db = self._load()
        if self._migrate():
            self.save()

    @staticmethod
    def new_id():
        return uuid.uuid4().hex[:12]

    @staticmethod
    def _empty():
        return {"entries": [], "active": None, "tasks": []}

    def _load(self):
        for path in (DATA, DATA + ".bak"):
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict) and "entries" in d:
                    db = self._empty()
                    db.update(d)
                    db.setdefault("tasks", [])
                    return db
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return self._empty()

    def _migrate(self):
        changed = False
        name_to_id = {}
        for t in self.db.get("tasks", []):
            if not t.get("id"):
                t["id"] = self.new_id()
                changed = True
            name_to_id[t["name"]] = t["id"]
        for e in self.db.get("entries", []):
            if not e.get("task_id"):
                tid = name_to_id.get(e.get("name"))
                if tid:
                    e["task_id"] = tid
                    changed = True
        a = self.db.get("active")
        if a and not a.get("task_id"):
            tid = name_to_id.get(a.get("name"))
            if tid:
                a["task_id"] = tid
                changed = True
        return changed

    def save(self):
        tmp = DATA + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.db, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(DATA):
                try:
                    shutil.copy2(DATA, DATA + ".bak")
                except Exception:
                    pass
            os.replace(tmp, DATA)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    def total_of(self, name):
        return sum(e["dur"] for e in self.db.get("entries", [])
                   if e.get("name") == name)

    def grand_total(self):
        total = sum(e["dur"] for e in self.db.get("entries", []))
        a = self.db.get("active")
        if a:
            run = round(time.time() - a["start"])
            if run >= 1:
                total += run
        return total

    def est_of(self, name):
        for t in self.db.get("tasks", []):
            if t.get("name") == name:
                return t.get("est", 0)
        return 0
