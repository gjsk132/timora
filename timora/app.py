import os
import time
import datetime
import webbrowser
import subprocess

import rumps

from .config import (TASK_ICON, IDLE_LIMIT, STALE_LIMIT, ENTRY_MENU_MAX,
                     REPORT, PROJECT_DIR)
from .formatting import fmt_clock, fmt_dur, fmt_est, day_of, task_label, parse_task_line
from .storage import Store
from .assets import app_icon
from .menu import MI
from .notifications import notify
from .system import idle_seconds
from .dialogs import (alert, alert3, batch_add_dialog,
                      edit_task_dialog, edit_entry_dialog)
from .report import build_report
from .i18n import t, set_language, get_language, detect_default

THRESHOLDS = (5, 15, 30, 60)


class Tracker(rumps.App):
    def __init__(self):
        super().__init__("Timora", title="📕")
        self.quit_button = MI(t("quit"), "power")
        try:
            from AppKit import (NSApplication,
                                NSApplicationActivationPolicyAccessory)
            app = NSApplication.sharedApplication()
            app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            ic = app_icon()
            if ic is not None:
                app.setApplicationIconImage_(ic)
        except Exception:
            pass
        self._icon_reapplied = False
        self.store = Store()
        self.db = self.store.db
        set_language(self.db.get("lang") or detect_default())
        a = self.db.get("active")
        if a and a.get("name"):
            a["base"] = self.store.total_of(a["name"])
        self._task_map = {}
        self._del_map = {}
        self._edit_map = {}
        self._entry_map = {}
        self._done_map = {}
        self._reopen_map = {}
        self._thr_map = {}
        self._cur_symbol = None
        self._cur_day = datetime.date.today()
        self._startup_checked = False
        self._idle_notified = False
        self._idle_counter = 0
        self.build_menu()
        self.timer = rumps.Timer(self.tick, 1)
        self.timer.start()
        self.refresh_title()

    # ----- settings helpers -----
    @property
    def settings(self):
        return self.db.setdefault("settings", {})

    def _notify_on(self):
        return self.settings.get("notifications", True)

    def _away_on(self):
        return self.settings.get("idle_detection", True)

    def _idle_limit(self):
        return self.settings.get("idle_limit", IDLE_LIMIT)

    def note(self, title, subtitle, message):
        if self._notify_on():
            notify(title, subtitle, message)

    def _save(self):
        self.store.save()

    # ----- manage tasks submenu -----
    def _manage_menu(self):
        mng = MI(t("manage"), "slider.horizontal.3")
        mng.add(MI(t("add_tasks_menu"), "plus", callback=self.add_tasks))
        all_tasks = self.db.get("tasks", [])
        todo = [x for x in all_tasks if not x.get("done")]
        done = [x for x in all_tasks if x.get("done")]
        edit = MI(t("edit_task_menu"), "square.and.pencil")
        dele = MI(t("delete_task_menu"), "trash")
        if todo:
            for x in todo:
                lbl = task_label(x)
                self._edit_map[lbl] = x
                edit.add(MI(lbl, TASK_ICON, callback=self.edit_task))
                self._del_map[lbl] = x
                dele.add(MI(lbl, TASK_ICON, callback=self.delete_task))
        else:
            edit.add(rumps.MenuItem(t("no_active_tasks")))
            dele.add(rumps.MenuItem(t("no_active_tasks")))
        mng.add(edit)
        mng.add(dele)
        mng.add(None)
        comp = MI(t("complete_task_menu"), "checkmark.circle")
        if todo:
            for x in todo:
                lbl = task_label(x)
                self._done_map[lbl] = x
                comp.add(MI(lbl, TASK_ICON, callback=self.complete_task))
        else:
            comp.add(rumps.MenuItem(t("no_active_tasks")))
        mng.add(comp)
        if done:
            reopen = MI(t("reopen_task_menu"), "arrow.uturn.left")
            for x in done:
                lbl = task_label(x)
                self._reopen_map[lbl] = x
                reopen.add(MI(lbl, TASK_ICON, callback=self.reopen_task))
            mng.add(reopen)
        return mng

    # ----- settings submenu -----
    def _settings_menu(self):
        self._thr_map = {}
        s = MI(t("settings_menu"), "gearshape")

        lang = MI(t("language_menu"), "globe")
        en = MI(t("lang_en"), callback=self.set_lang_en)
        ko = MI(t("lang_ko"), callback=self.set_lang_ko)
        en.state = 1 if get_language() == "en" else 0
        ko.state = 1 if get_language() == "ko" else 0
        lang.add(en)
        lang.add(ko)
        s.add(lang)
        s.add(None)

        notif = MI(t("notifications_toggle"), callback=self.toggle_notifications)
        notif.state = 1 if self._notify_on() else 0
        s.add(notif)

        away = MI(t("away_toggle"), callback=self.toggle_away)
        away.state = 1 if self._away_on() else 0
        s.add(away)

        thr = MI(t("away_threshold"), "clock")
        cur = self._idle_limit() // 60
        for mins in THRESHOLDS:
            lbl = t("minutes", n=mins)
            self._thr_map[lbl] = mins * 60
            it = MI(lbl, callback=self.set_threshold)
            it.state = 1 if cur == mins else 0
            thr.add(it)
        s.add(thr)
        s.add(None)

        s.add(MI(t("open_data_folder"), "folder", callback=self.open_data_folder))
        return s

    # ----- menu -----
    def build_menu(self):
        self.menu.clear()
        self.quit_button.title = t("quit")
        self._task_map = {}
        self._del_map = {}
        self._edit_map = {}
        self._entry_map = {}
        self._done_map = {}
        self._reopen_map = {}
        active = self.db.get("active")
        if active:
            verb = t("status_resumed") if active.get("base", 0) > 0 else t("status_inprogress")
            status = MI(f"{verb}: {active['name']}", "circle.fill")
            self.menu = [
                status,
                MI(t("stop_save"), "stop.fill", callback=self.stop),
                MI(t("cancel_nosave"), "xmark", callback=self.cancel),
                None,
                self._manage_menu(),
                None,
                MI(t("detailed_view"), "chart.bar.xaxis", callback=self.open_report),
                MI(t("progress_menu"), "target", callback=self.progress_summary),
                MI(t("today_menu"), "list.bullet.clipboard", callback=self.today_summary),
                self._entries_menu(),
                None,
                self._settings_menu(),
            ]
        else:
            start = MI(t("start_choose"), "play.fill")
            todo = [x for x in self.db.get("tasks", []) if not x.get("done")]
            grand = self.store.grand_total()
            if grand > 0:
                start.add(rumps.MenuItem(t("total_fmt", dur=fmt_dur(grand))))
                start.add(None)
            if todo:
                for x in todo:
                    lbl = self.start_label(x)
                    self._task_map[lbl] = x
                    start.add(MI(lbl, TASK_ICON, callback=self.start_task))
            else:
                start.add(rumps.MenuItem(t("add_first")))
            self.menu = [
                start,
                None,
                self._manage_menu(),
                None,
                MI(t("detailed_view"), "chart.bar.xaxis", callback=self.open_report),
                MI(t("progress_menu"), "target", callback=self.progress_summary),
                MI(t("today_menu"), "list.bullet.clipboard", callback=self.today_summary),
                self._entries_menu(),
                None,
                self._settings_menu(),
            ]

    def _entries_menu(self):
        mng = MI(t("edit_delete_records"), "arrow.uturn.backward")
        entries = self.db.get("entries", [])
        if entries:
            for e in reversed(entries[-ENTRY_MENU_MAX:]):
                lbl = "%s %s  %s · %s" % (
                    datetime.datetime.fromtimestamp(e["start"]).strftime("%-m/%-d"),
                    datetime.datetime.fromtimestamp(e["start"]).strftime("%H:%M"),
                    e["name"], fmt_dur(e["dur"]))
                self._entry_map[lbl] = e
                mng.add(MI(lbl, TASK_ICON, callback=self.edit_entry))
        else:
            mng.add(rumps.MenuItem(t("no_saved_records")))
        return mng

    def _set_symbol(self, name):
        try:
            from AppKit import NSImage
            btn = self._nsapp.nsstatusitem.button()
            if btn is None:
                return False
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
            if img is None:
                return False
            img.setTemplate_(True)
            btn.setImage_(img)
            return True
        except Exception:
            return False

    def refresh_title(self):
        a = self.db.get("active")
        want = "book" if a else "book.closed"
        if want != self._cur_symbol:
            if self._set_symbol(want):
                self._cur_symbol = want
        if a:
            total = a.get("base", 0) + (time.time() - a["start"])
            name = a["name"]
            if len(name) > 14:
                name = name[:13] + "…"
            self.title = (f" {name} {fmt_clock(total)}"
                          if self._cur_symbol else
                          f"📖 {name} {fmt_clock(total)}")
        else:
            self.title = "" if self._cur_symbol else "📕"

    def tick(self, _):
        self.refresh_title()
        today = datetime.date.today()
        if today != self._cur_day:
            self._cur_day = today
            self.build_menu()
        if not self._icon_reapplied:
            self._icon_reapplied = True
            try:
                from AppKit import NSApplication
                ic = app_icon()
                if ic is not None:
                    NSApplication.sharedApplication().setApplicationIconImage_(ic)
            except Exception:
                pass
        if not self._startup_checked:
            self._startup_checked = True
            self._check_stale_active()
        if self.db.get("active") and self._away_on():
            self._idle_counter += 1
            if self._idle_counter >= 20:
                self._idle_counter = 0
                self._check_idle()
        else:
            self._idle_counter = 0
            self._idle_notified = False

    def _check_stale_active(self):
        a = self.db.get("active")
        if not a:
            return
        elapsed = time.time() - a.get("start", time.time())
        today = datetime.date.today().strftime("%Y-%m-%d")
        if elapsed <= STALE_LIMIT and day_of(a["start"]) == today:
            return
        r = alert3(
            t("stale_title"),
            t("stale_msg", name=a["name"], dur=fmt_dur(elapsed)),
            t("stale_save"), t("stale_discard"), t("stale_keep"))
        if r == 1:
            self.stop(None)
        elif r == 2:
            self.cancel(None)

    def _check_idle(self):
        if idle_seconds() >= self._idle_limit():
            if not self._idle_notified:
                self._idle_notified = True
                a = self.db.get("active")
                nm = a["name"] if a else ""
                self.note(t("idle_title"), t("idle_sub", name=nm), t("idle_msg"))
        else:
            self._idle_notified = False

    # ----- settings actions -----
    def set_lang_en(self, _):
        self._set_lang("en")

    def set_lang_ko(self, _):
        self._set_lang("ko")

    def _set_lang(self, lang):
        self.db["lang"] = lang
        set_language(lang)
        self._save()
        self.build_menu()
        self.refresh_title()

    def toggle_notifications(self, _):
        self.settings["notifications"] = not self._notify_on()
        self._save()
        self.build_menu()

    def toggle_away(self, _):
        self.settings["idle_detection"] = not self._away_on()
        self._save()
        self.build_menu()

    def set_threshold(self, sender):
        secs = self._thr_map.get(sender.title)
        if not secs:
            return
        self.settings["idle_limit"] = secs
        self._idle_notified = False
        self._save()
        self.build_menu()

    def open_data_folder(self, _):
        from .config import DATA
        target = DATA if os.path.exists(DATA) else PROJECT_DIR
        try:
            subprocess.run(["open", "-R", target])
        except Exception:
            try:
                subprocess.run(["open", PROJECT_DIR])
            except Exception:
                pass

    # ----- task actions -----
    def add_tasks(self, _):
        text = batch_add_dialog()
        if text is None:
            return
        existing = {x["name"] for x in self.db.get("tasks", [])}
        added = skipped = 0
        for line in str(text).splitlines():
            nm, est = parse_task_line(line)
            if not nm:
                continue
            if nm in existing:
                skipped += 1
                continue
            existing.add(nm)
            self.db.setdefault("tasks", []).append(
                {"name": nm, "est": est, "done": False, "id": Store.new_id()})
            added += 1
        if added:
            self._save()
            self.build_menu()
        if added or skipped:
            msg = t("added_msg", n=added) + (t("added_dup", n=skipped) if skipped else "")
            self.note(t("added_title"), "", msg)

    def edit_task(self, sender):
        x = self._edit_map.get(sender.title)
        if not x:
            return
        old_name = x["name"]
        upd = edit_task_dialog(x.get("name", ""), x.get("est", 0))
        if not upd:
            return
        new_name = upd["name"]
        if new_name != old_name and any(
                o is not x and o.get("name") == new_name
                for o in self.db.get("tasks", [])):
            alert(t("dup_title"), t("dup_msg", name=new_name))
            return
        x["name"], x["est"] = new_name, upd["est"]
        if new_name != old_name:
            tid = x.get("id")
            if tid:
                for e in self.db.get("entries", []):
                    if e.get("task_id") == tid:
                        e["name"] = new_name
                a = self.db.get("active")
                if a and a.get("task_id") == tid:
                    a["name"] = new_name
        self._save()
        self.build_menu()
        self.refresh_title()

    def edit_entry(self, sender):
        e = self._entry_map.get(sender.title)
        if not e:
            return
        res = edit_entry_dialog(e.get("name", ""), e.get("dur", 0))
        if not res:
            return
        action, data = res
        if action == "delete":
            try:
                self.db["entries"].remove(e)
            except ValueError:
                pass
        elif action == "save":
            e["name"] = data["name"]
            e["dur"] = data["dur"]
            e["end"] = e.get("start", 0) + data["dur"]
        self._save()
        self.build_menu()

    def delete_task(self, sender):
        x = self._del_map.get(sender.title)
        if not x:
            return
        if alert(title=t("del_title"),
                 message=t("del_msg", name=x["name"]),
                 ok=t("del_ok"), cancel=t("cancel")) == 1:
            try:
                self.db["tasks"].remove(x)
            except ValueError:
                pass
            self._save()
            self.build_menu()

    def complete_task(self, sender):
        x = self._done_map.get(sender.title)
        if not x:
            return
        a = self.db.get("active")
        if a and a.get("name") == x["name"]:
            self.stop(None)
        x["done"] = True
        x["done_at"] = time.time()
        self._save()
        self.build_menu()
        self.refresh_title()
        total = self.store.total_of(x["name"])
        est = x.get("est", 0)
        cmp_txt = (t("completed_cmp", pct=round(total / (est * 60) * 100), est=fmt_est(est))
                   if est else "")
        self.note(t("completed_title"), x["name"],
                  t("completed_msg", dur=fmt_dur(total), cmp=cmp_txt))

    def reopen_task(self, sender):
        x = self._reopen_map.get(sender.title)
        if not x:
            return
        x["done"] = False
        x.pop("done_at", None)
        self._save()
        self.build_menu()

    def start_label(self, x):
        name = x["name"]
        parts = []
        total = self.store.total_of(name)
        if total > 0:
            parts.append(t("total_part", dur=fmt_dur(total)))
        if x.get("est"):
            parts.append(t("est_part", dur=fmt_est(x["est"])))
        return f"{name}   ({' · '.join(parts)})" if parts else name

    def start_task(self, sender):
        x = self._task_map.get(sender.title)
        if not x:
            return
        self.db["active"] = {
            "name": x["name"], "task_id": x.get("id"), "start": time.time(),
            "base": self.store.total_of(x["name"]),
        }
        self._save()
        self.build_menu()
        self.refresh_title()

    def stop(self, _):
        a = self.db.get("active")
        if not a:
            return
        dur = round(time.time() - a["start"])
        if dur >= 1:
            self.db["entries"].append({
                "id": f"{int(a['start']*1000)}",
                "name": a["name"], "task_id": a.get("task_id"),
                "start": a["start"], "end": time.time(), "dur": dur,
            })
        self.db["active"] = None
        self._save()
        self.build_menu()
        self.refresh_title()
        total = a.get("base", 0) + dur
        est = self.store.est_of(a["name"])
        if est:
            pct = round(total / (est * 60) * 100)
            cmp_txt = t("stop_cmp", pct=pct, est=fmt_est(est)) + (t("over_suffix") if total > est * 60 else "")
        else:
            cmp_txt = ""
        self.note(t("saved_title"), a["name"],
                  t("saved_msg", dur=fmt_dur(dur), total=fmt_dur(total), cmp=cmp_txt))

    def cancel(self, _):
        self.db["active"] = None
        self._save()
        self.build_menu()
        self.refresh_title()

    def progress_summary(self, _):
        act = {}
        for e in self.db.get("entries", []):
            act[e["name"]] = act.get(e["name"], 0) + e["dur"]
        a = self.db.get("active")
        if a:
            run = round(time.time() - a["start"])
            if run >= 1:
                act[a["name"]] = act.get(a["name"], 0) + run
        tasks = self.db.get("tasks", [])
        rows = [x for x in tasks if act.get(x["name"], 0) > 0 or x.get("est")]
        if not rows:
            alert(t("progress_title_plain"), t("progress_none"))
            return
        rows.sort(key=lambda x: (bool(x.get("done")), -act.get(x["name"], 0)))
        lines = []
        for x in rows:
            nm = x["name"]
            sec = act.get(nm, 0)
            est = x.get("est", 0)
            mark = "✅ " if x.get("done") else ""
            if est:
                pct = round(sec / (est * 60) * 100)
                tag = t("prog_with_est", act=fmt_dur(sec), est=fmt_est(est), pct=pct)
                if sec > est * 60:
                    tag += t("over_suffix")
            else:
                tag = t("prog_no_est", act=fmt_dur(sec))
            lines.append(f"• {mark}{nm}\n   {tag}")
        alert(title=t("progress_title"), message="\n".join(lines))

    def today_summary(self, _):
        today = datetime.date.today().strftime("%Y-%m-%d")
        by = {}
        for e in self.db["entries"]:
            if day_of(e["start"]) == today:
                by[e["name"]] = by.get(e["name"], 0) + e["dur"]
        a = self.db.get("active")
        if a and day_of(a["start"]) == today:
            run = round(time.time() - a["start"])
            if run >= 1:
                by[a["name"]] = by.get(a["name"], 0) + run
        if not by:
            alert(t("today_title_plain"), t("today_none"))
            return
        total = sum(by.values())
        lines = [t("today_total", dur=fmt_dur(total)) + "\n"]
        for name, sec in sorted(by.items(), key=lambda kv: -kv[1]):
            pct = round(sec / total * 100) if total else 0
            lines.append(f"• {name}\n   " + t("today_item", dur=fmt_dur(sec), pct=pct))
        lines.append(t("today_footer"))
        alert(title=t("today_title"), message="\n".join(lines))

    def open_report(self, _):
        with open(REPORT, "w", encoding="utf-8") as f:
            f.write(build_report(self.db))
        webbrowser.open("file://" + REPORT)
