#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📕 내 업무 기록 — macOS 메뉴바 앱
- 평소: 📕 (덮인 책) / 진행 중: 📖 (펼친 책) + 하는 일 + 진행시간
- 할 일을 미리 목록에 등록 → 시작할 때 목록에서 선택
- '상세 보기'로 목록·날짜별 합계·카테고리 통계·그래프 창 열기
"""
import os, sys, json, time, datetime, webbrowser, subprocess, atexit, shutil, re, uuid
import rumps

APP_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA     = os.path.join(APP_DIR, "data.json")
REPORT   = os.path.join(APP_DIR, "report.html")
LOCK     = os.path.join(APP_DIR, ".tracker.lock")

ACCENT = "#6366f1"          # 그래프·막대 기본 색
TASK_ICON = "circle.fill"   # 메뉴 할 일 항목 아이콘
IDLE_LIMIT = 15 * 60        # 자리비움 알림 기준(초)
STALE_LIMIT = 60 * 60       # 재시작 시 '진행 중' 세션이 이만큼 지났으면 확인
ENTRY_MENU_MAX = 15         # 기록 수정/삭제 메뉴에 보여줄 최근 기록 수


# ---------- 앱 아이콘(모래시계, 런타임 생성) ----------
def make_app_icon(size=512):
    """블루→인디고 스퀘어클 + 흰 모래시계. NSImage 반환(실패 시 None)."""
    try:
        from AppKit import (NSImage, NSBezierPath, NSColor, NSGradient, NSMakeRect,
                            NSMakeSize, NSImageSymbolConfiguration,
                            NSCompositingOperationSourceOver, NSFontWeightSemibold)
        img = NSImage.alloc().initWithSize_(NSMakeSize(size, size))
        img.lockFocus()
        inset = size * 0.085
        rect = NSMakeRect(inset, inset, size - 2 * inset, size - 2 * inset)
        radius = (size - 2 * inset) * 0.2237
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
        c1 = NSColor.colorWithSRGBRed_green_blue_alpha_(0x37/255, 0x82/255, 0xf6/255, 1)
        c2 = NSColor.colorWithSRGBRed_green_blue_alpha_(0x6b/255, 0x5b/255, 0xf0/255, 1)
        NSGradient.alloc().initWithStartingColor_endingColor_(c1, c2)\
            .drawInBezierPath_angle_(path, -90)
        sym = NSImage.imageWithSystemSymbolName_accessibilityDescription_("hourglass", None)
        conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(
            size * 0.34, NSFontWeightSemibold, 3)
        try:
            conf = conf.configurationByApplyingConfiguration_(
                NSImageSymbolConfiguration.configurationWithHierarchicalColor_(
                    NSColor.whiteColor()))
        except Exception:
            pass
        s = sym.imageWithSymbolConfiguration_(conf)
        sz = s.size()
        s.drawAtPoint_fromRect_operation_fraction_(
            ((size - sz.width) / 2, (size - sz.height) / 2),
            NSMakeRect(0, 0, sz.width, sz.height), NSCompositingOperationSourceOver, 1.0)
        img.unlockFocus()
        return img
    except Exception:
        return None

_APP_ICON = None
def app_icon():
    """앱 아이콘 NSImage(캐시). 다이얼로그·앱 아이콘에 공용."""
    global _APP_ICON
    if _APP_ICON is None:
        _APP_ICON = make_app_icon()
    return _APP_ICON


# ---------- 알림 아이콘 (기본 Python 로켓 대신 앱 아이콘) ----------
_ICON_FILE = None
def icon_file():
    """알림(NSUserNotification)에 쓸 앱 아이콘 파일 경로(캐시).
    nohup으로 python을 직접 띄우면 알림이 'Python'이 보낸 걸로 잡혀
    로켓 아이콘이 뜨므로, 앱 아이콘 이미지를 명시적으로 지정한다."""
    global _ICON_FILE
    if _ICON_FILE is not None:
        return _ICON_FILE or None
    # 1) 앱 번들 아이콘(.icns)이 있으면 그대로 사용
    cand = os.path.join(APP_DIR, "시간기록.app", "Contents", "Resources", "AppIcon.icns")
    if os.path.exists(cand):
        _ICON_FILE = cand
        return _ICON_FILE
    # 2) 없으면 런타임 생성 아이콘(모래시계)을 PNG로 써둔다
    try:
        from AppKit import NSBitmapImageRep
        img = app_icon()
        if img is not None:
            rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
            png = rep.representationUsingType_properties_(4, None)  # 4 = PNG
            out = os.path.join(APP_DIR, ".appicon.png")
            png.writeToFile_atomically_(out, True)
            _ICON_FILE = out
            return _ICON_FILE
    except Exception:
        pass
    _ICON_FILE = ""   # 실패 기록(재시도 방지)
    return None

def fix_bundle_identifier():
    """알림이 'Python'(로켓 아이콘)으로 뜨는 것을 막는다.
    run 스크립트가 python을 .app에서 분리(nohup)해 띄우므로, 알림센터는
    보낸 주체를 Python으로 보고 로켓을 그린다. NSUserNotification은 큰 앱
    아이콘을 '프로세스의 번들 식별자'로 LaunchServices에서 찾으므로, 실행 중
    프로세스의 식별자를 한 번이라도 실행된 시간기록.app(local.timetracker)으로
    지정하면 그 앱 아이콘(모래시계)이 알림에 표시된다."""
    try:
        from Foundation import NSBundle
        info = NSBundle.mainBundle().infoDictionary()
        if info is not None:
            info["CFBundleIdentifier"] = "local.timetracker"
    except Exception:
        pass

def notify(title, subtitle, message):
    """앱 아이콘을 단 알림. 아이콘 적용 실패 시 기본 알림으로 폴백."""
    ic = icon_file()
    try:
        if ic:
            rumps.notification(title, subtitle, message, icon=ic)
        else:
            rumps.notification(title, subtitle, message)
    except Exception:
        try:
            rumps.notification(title, subtitle, message)
        except Exception:
            pass


# ---------- 메뉴 아이콘(SF Symbol 이미지) ----------
def sf_image(name):
    """SF Symbol 템플릿 이미지를 반환(없으면 None). 메뉴바 톤에 맞춰 자동 색."""
    try:
        from AppKit import NSImage
        img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
        if img is None:
            return None
        img.setTemplate_(True)
        return img
    except Exception:
        return None

def MI(title, symbol=None, callback=None):
    """아이콘(SF Symbol)이 달린 rumps.MenuItem 생성. 이모지 대신 이미지 사용."""
    mi = rumps.MenuItem(title, callback=callback)
    if symbol:
        img = sf_image(symbol)
        if img is not None:
            try:
                mi._menuitem.setImage_(img)
            except Exception:
                pass
    return mi


# ---------- 데이터 (원자적 저장 + 백업 폴백) ----------
def _empty_db():
    return {"entries": [], "active": None, "tasks": []}

def load():
    # data.json이 깨졌으면 백업(.bak)에서 복구 시도
    for path in (DATA, DATA + ".bak"):
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and "entries" in d:
                db = _empty_db()
                db.update(d)
                db.setdefault("tasks", [])
                return db
        except FileNotFoundError:
            continue
        except Exception:
            # 손상된 파일 → 다음 후보(.bak)로
            continue
    return _empty_db()

def new_id():
    """할 일을 구분하는 안정적 고유 id. 이름이 같아도 서로 분리된다."""
    return uuid.uuid4().hex[:12]

def migrate(db):
    """이전 데이터 호환: 할 일에 id를 부여하고, 기존 기록·진행중 세션을
    '같은 이름의 현재 할 일'에 task_id로 연결한다. 한 번 연결되면 이후
    이름을 바꿔도 id로 따라가므로, 과거 같은 이름이던 기록과 섞이지 않는다.
    바뀐 게 있으면 True."""
    changed = False
    name_to_id = {}
    for t in db.get("tasks", []):
        if not t.get("id"):
            t["id"] = new_id()
            changed = True
        name_to_id[t["name"]] = t["id"]   # 현재 할 일은 이름이 유일
    for e in db.get("entries", []):
        if not e.get("task_id"):
            tid = name_to_id.get(e.get("name"))
            if tid:
                e["task_id"] = tid
                changed = True
    a = db.get("active")
    if a and not a.get("task_id"):
        tid = name_to_id.get(a.get("name"))
        if tid:
            a["task_id"] = tid
            changed = True
    return changed

def save(db):
    # 임시파일에 먼저 쓰고(fsync) → 기존본을 .bak으로 백업 → 원자적 교체
    tmp = DATA + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(DATA):
            try:
                shutil.copy2(DATA, DATA + ".bak")
            except Exception:
                pass
        os.replace(tmp, DATA)
    except Exception:
        # 저장 실패 시 임시파일 정리
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


# ---------- 중복 실행 방지 ----------
def _is_tracker_pid(pid):
    """해당 PID가 살아있고 실제로 이 앱(tracker.py) 프로세스인지 확인."""
    if pid <= 0 or pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)            # 살아있는지
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                # 살아있으나 내 소유 아님 → 실행 중으로 간주
    except OSError:
        return False
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, timeout=2).stdout
        return "tracker.py" in out
    except Exception:
        return True                # 확인 불가하면 안전하게 실행 중으로 간주

def already_running():
    """이미 인스턴스가 떠 있으면 True. 아니면 락에 내 PID를 기록."""
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

def _release_lock():
    """내가 쥔 락이면 정리."""
    try:
        with open(LOCK) as f:
            if int((f.read().strip() or "0")) == os.getpid():
                os.remove(LOCK)
    except Exception:
        pass


def fmt_clock(sec):
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def fmt_dur(sec):
    sec = int(sec)
    h, m = sec // 3600, (sec % 3600) // 60
    if h: return f"{h}시간 {m}분" if m else f"{h}시간"
    if m: return f"{m}분"
    return f"{sec}초"

def day_of(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def fmt_est(minutes):
    return fmt_dur(int(minutes) * 60)

def task_label(t):
    est = t.get("est")
    if est:
        return f"{t['name']}   (예상 {fmt_est(est)})"
    return f"{t['name']}"


# ---------- 입력 다이얼로그 (AppKit) ----------
_NS_FIRST_BUTTON = 1000   # NSAlertFirstButtonReturn

def _bring_front():
    try:
        from AppKit import NSApp
        NSApp.activateIgnoringOtherApps_(True)
    except Exception:
        pass

def idle_seconds():
    """키보드·마우스 입력이 없는 시간(초). 실패 시 0."""
    try:
        out = subprocess.run(["ioreg", "-c", "IOHIDSystem"],
                             capture_output=True, text=True, timeout=2).stdout
        m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if m:
            return int(m.group(1)) / 1e9
    except Exception:
        pass
    return 0.0

def alert3(title, message, b1, b2, b3):
    """버튼 3개 알림. 눌린 버튼 번호(1/2/3) 반환."""
    from AppKit import NSAlert
    a = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        a.setIcon_(ic)
    a.setMessageText_(str(title))
    a.setInformativeText_(str(message))
    a.addButtonWithTitle_(b1)
    a.addButtonWithTitle_(b2)
    a.addButtonWithTitle_(b3)
    _bring_front()
    r = a.runModal()
    return {1000: 1, 1001: 2, 1002: 3}.get(r, 0)

def parse_task_line(line):
    """'이름, 30' / '이름 30' / '이름' 한 줄을 (이름, 분)으로 파싱."""
    line = str(line).strip()
    if not line:
        return None, 0
    if "," in line:
        nm, _, rest = line.partition(",")
        digits = "".join(c for c in rest if c.isdigit())
        return nm.strip(), (int(digits) if digits else 0)
    parts = line.rsplit(None, 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0].strip(), int(parts[1])
    return line, 0

def batch_add_dialog():
    """여러 줄 입력으로 할 일 일괄 추가. 텍스트 반환(취소 시 None)."""
    from AppKit import (NSAlert, NSScrollView, NSTextView, NSView, NSMakeRect, NSFont)
    alert = NSAlert.alloc().init()
    _ic = app_icon()
    if _ic is not None:
        alert.setIcon_(_ic)
    alert.setMessageText_("할 일 여러 개 추가")
    alert.setInformativeText_(
        "한 줄에 하나씩.   형식:  이름, 예상분\n"
        "예)  영어 단어 외우기, 30\n"
        "      알고리즘 문제, 60\n"
        "      산책            ← 예상분은 생략 가능")
    alert.addButtonWithTitle_("추가")
    alert.addButtonWithTitle_("취소")

    width, ta_h = 340, 160
    scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, width, ta_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setBorderType_(2)   # NSBezelBorder
    tv = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, width, ta_h))
    tv.setFont_(NSFont.systemFontOfSize_(13))
    tv.setRichText_(False)
    tv.setAutomaticQuoteSubstitutionEnabled_(False)
    scroll.setDocumentView_(tv)

    alert.setAccessoryView_(scroll)
    _bring_front()
    try:
        alert.window().setInitialFirstResponder_(tv)
    except Exception:
        pass
    if alert.runModal() != _NS_FIRST_BUTTON:
        return None
    return str(tv.string())

def edit_task_dialog(name="", est=0, title="할 일 수정"):
    """이름·예상분을 한 다이얼로그에서 편집. dict 반환(취소 시 None)."""
    from AppKit import (NSAlert, NSTextField, NSView, NSMakeRect)
    alert = NSAlert.alloc().init()
    _ic = app_icon()
    if _ic is not None:
        alert.setIcon_(_ic)
    alert.setMessageText_(title)
    alert.addButtonWithTitle_("저장")
    alert.addButtonWithTitle_("취소")

    width, row, gap = 300, 24, 10
    h = row * 2 + gap
    cont = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, h))
    name_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - row, width, row))
    name_f.setStringValue_(name)
    name_f.setPlaceholderString_("할 일 이름")
    est_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, row))
    est_f.setStringValue_(str(est) if est else "")
    est_f.setPlaceholderString_("예상 소요시간(분) · 비우면 미설정")
    cont.addSubview_(name_f)
    cont.addSubview_(est_f)

    alert.setAccessoryView_(cont)
    _bring_front()
    try:
        alert.window().setInitialFirstResponder_(name_f)
    except Exception:
        pass
    if alert.runModal() != _NS_FIRST_BUTTON:
        return None
    nm = str(name_f.stringValue()).strip()
    if not nm:
        return None
    digits = "".join(ch for ch in str(est_f.stringValue()) if ch.isdigit())
    return {"name": nm, "est": int(digits) if digits else 0}

def edit_entry_dialog(name, dur_sec):
    """기록(이름·실제분) 수정 또는 삭제.
    ('save', {name,dur}) / ('delete', None) / None(취소) 반환."""
    from AppKit import (NSAlert, NSTextField, NSView, NSMakeRect)
    a = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        a.setIcon_(ic)
    a.setMessageText_("기록 수정")
    a.setInformativeText_("실제 시간(분)을 고치거나, 이 기록을 삭제할 수 있어요.")
    a.addButtonWithTitle_("저장")
    a.addButtonWithTitle_("삭제")
    a.addButtonWithTitle_("취소")

    width, row, gap = 300, 24, 10
    h = row * 2 + gap
    cont = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, h))
    name_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - row, width, row))
    name_f.setStringValue_(name)
    name_f.setPlaceholderString_("할 일 이름")
    min_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, row))
    min_f.setStringValue_(str(max(1, round(dur_sec / 60))))
    min_f.setPlaceholderString_("실제 소요시간(분)")
    cont.addSubview_(name_f)
    cont.addSubview_(min_f)

    a.setAccessoryView_(cont)
    _bring_front()
    try:
        a.window().setInitialFirstResponder_(min_f)
    except Exception:
        pass
    r = a.runModal()
    if r == 1001:           # 삭제
        return ("delete", None)
    if r != _NS_FIRST_BUTTON:  # 취소
        return None
    nm = str(name_f.stringValue()).strip()
    digits = "".join(c for c in str(min_f.stringValue()) if c.isdigit())
    mins = int(digits) if digits else 0
    if not nm or mins <= 0:
        return None
    return ("save", {"name": nm, "dur": mins * 60})

def alert(title="", message="", ok=None, cancel=None):
    """모래시계 아이콘이 달린 알림/확인창. OK=1, 취소=0 반환 (rumps.alert 호환)."""
    from AppKit import NSAlert
    a = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        a.setIcon_(ic)
    a.setMessageText_(str(title))
    a.setInformativeText_(str(message))
    a.addButtonWithTitle_(ok or "확인")
    if cancel is not None:
        a.addButtonWithTitle_(cancel if isinstance(cancel, str) else "취소")
    _bring_front()
    return 1 if a.runModal() == _NS_FIRST_BUTTON else 0


class Tracker(rumps.App):
    def __init__(self):
        super().__init__("시간기록", title="📕")
        self.quit_button = MI("앱 종료", "power")
        # Dock 아이콘은 숨기고 메뉴바에만 표시 (액세서리 앱)
        try:
            from AppKit import (NSApplication,
                                NSApplicationActivationPolicyAccessory)
            app = NSApplication.sharedApplication()
            app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            # 다이얼로그·Cmd-Tab에 쓰일 앱 아이콘(모래시계)으로 교체
            ic = app_icon()
            if ic is not None:
                app.setApplicationIconImage_(ic)
        except Exception:
            pass
        self._icon_reapplied = False
        self.db = load()
        if migrate(self.db):     # 이전 데이터에 id·task_id 부여(1회)
            save(self.db)
        # 진행 중 세션의 base(이전까지 누적)를 현재 모델 기준으로 보정.
        # 완료된 기록은 세션 중 변하지 않으므로 항상 total_of로 복원 가능.
        a = self.db.get("active")
        if a and a.get("name"):
            a["base"] = self.total_of(a["name"])
        self._task_map = {}
        self._del_map = {}
        self._edit_map = {}
        self._entry_map = {}
        self._done_map = {}
        self._reopen_map = {}
        self._cur_symbol = None   # 현재 메뉴바에 설정된 SF Symbol 이름
        self._cur_day = datetime.date.today()   # 자정 넘김 감지용
        self._startup_checked = False            # 재시작 시 오래된 세션 확인
        self._idle_notified = False              # 자리비움 알림 1회만
        self._idle_counter = 0                   # 유휴 확인 주기 카운터
        self.build_menu()
        self.timer = rumps.Timer(self.tick, 1)
        self.timer.start()
        self.refresh_title()

    # ----- 할 일 관리 서브메뉴 -----
    def _manage_menu(self):
        mng = MI("할 일 관리", "slider.horizontal.3")
        mng.add(MI("할 일 추가 (여러 개)", "plus", callback=self.add_tasks))
        all_tasks = self.db.get("tasks", [])
        todo = [t for t in all_tasks if not t.get("done")]   # 진행 중(미완료)
        done = [t for t in all_tasks if t.get("done")]       # 완료됨
        edit = MI("할 일 수정", "square.and.pencil")
        dele = MI("할 일 삭제", "trash")
        if todo:
            for t in todo:
                lbl = task_label(t)
                self._edit_map[lbl] = t
                edit.add(MI(lbl, TASK_ICON, callback=self.edit_task))
                self._del_map[lbl] = t
                dele.add(MI(lbl, TASK_ICON, callback=self.delete_task))
        else:
            edit.add(rumps.MenuItem("(진행 중인 할 일 없음)"))
            dele.add(rumps.MenuItem("(진행 중인 할 일 없음)"))
        mng.add(edit)
        mng.add(dele)
        mng.add(None)
        # 할 일 완료(목록에서 숨김) / 완료 취소(다시 진행)
        comp = MI("할 일 완료", "checkmark.circle")
        if todo:
            for t in todo:
                lbl = task_label(t)
                self._done_map[lbl] = t
                comp.add(MI(lbl, TASK_ICON, callback=self.complete_task))
        else:
            comp.add(rumps.MenuItem("(진행 중인 할 일 없음)"))
        mng.add(comp)
        if done:
            reopen = MI("완료 취소", "arrow.uturn.left")
            for t in done:
                lbl = task_label(t)
                self._reopen_map[lbl] = t
                reopen.add(MI(lbl, TASK_ICON, callback=self.reopen_task))
            mng.add(reopen)
        return mng

    # ----- 메뉴 구성 -----
    def build_menu(self):
        self.menu.clear()
        self._task_map = {}
        self._del_map = {}
        self._edit_map = {}
        self._entry_map = {}
        self._done_map = {}
        self._reopen_map = {}
        active = self.db.get("active")
        if active:
            verb = "이어서 진행 중" if active.get("base", 0) > 0 else "진행 중"
            status = MI(f"{verb}: {active['name']}", "circle.fill")
            self.menu = [
                status,
                MI("종료하고 저장", "stop.fill", callback=self.stop),
                MI("취소 (저장 안 함)", "xmark", callback=self.cancel),
                None,
                self._manage_menu(),
                None,
                MI("상세 보기", "chart.bar.xaxis", callback=self.open_report),
                MI("진행 현황 (누적)", "target", callback=self.progress_summary),
                MI("오늘 요약", "list.bullet.clipboard", callback=self.today_summary),
                self._entries_menu(),
            ]
        else:
            start = MI("시작 (할 일 선택)", "play.fill")
            todo = [t for t in self.db.get("tasks", []) if not t.get("done")]
            grand = self.grand_total()
            if grand > 0:
                start.add(rumps.MenuItem(f"총 누적 {fmt_dur(grand)}"))  # 헤더(비활성)
                start.add(None)
            if todo:
                for t in todo:
                    lbl = self.start_label(t)
                    self._task_map[lbl] = t
                    start.add(MI(lbl, TASK_ICON, callback=self.start_task))
            else:
                start.add(rumps.MenuItem("(먼저 '할 일 관리'에서 추가)"))
            self.menu = [
                start,
                None,
                self._manage_menu(),
                None,
                MI("상세 보기", "chart.bar.xaxis", callback=self.open_report),
                MI("진행 현황 (누적)", "target", callback=self.progress_summary),
                MI("오늘 요약", "list.bullet.clipboard", callback=self.today_summary),
                self._entries_menu(),
            ]

    # ----- 기록 수정/삭제 서브메뉴 (최근 기록) -----
    def _entries_menu(self):
        mng = MI("기록 수정/삭제", "arrow.uturn.backward")
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
            mng.add(rumps.MenuItem("(저장된 기록 없음)"))
        return mng

    # ----- 메뉴바 아이콘(SF Symbol) 설정 -----
    def _set_symbol(self, name):
        """상태바 버튼에 SF Symbol 이미지를 설정. 성공하면 True.
        이모지 텍스트는 일부 환경에서 안 보여서 이미지 아이콘을 쓴다."""
        try:
            from AppKit import NSImage
            btn = self._nsapp.nsstatusitem.button()
            if btn is None:
                return False
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
            if img is None:
                return False
            img.setTemplate_(True)   # 라이트/다크 메뉴바에 맞게 자동 색
            btn.setImage_(img)
            return True
        except Exception:
            return False

    # ----- 타이틀(메뉴바) 갱신 -----
    def refresh_title(self):
        a = self.db.get("active")
        want = "book" if a else "book.closed"   # 진행 중=펼친 책 / 평소=덮인 책
        if want != self._cur_symbol:
            if self._set_symbol(want):
                self._cur_symbol = want
        if a:
            # 누적(전체) 진행시간 = 이전까지 쌓인 시간 + 이번 세션 경과
            total = a.get("base", 0) + (time.time() - a["start"])
            name = a["name"]
            if len(name) > 14:
                name = name[:13] + "…"
            # 아이콘이 설정됐으면 이름·시간만 텍스트로, 실패 시 이모지로 폴백
            self.title = (f" {name} {fmt_clock(total)}"
                          if self._cur_symbol else
                          f"📖 {name} {fmt_clock(total)}")
        else:
            self.title = "" if self._cur_symbol else "📕"

    def tick(self, _):
        # 매초 호출: 실행 직후엔 아직 상태바 버튼이 없어 아이콘 설정이
        # 미뤄지므로, 여기서 다시 시도해 아이콘을 확실히 표시한다.
        self.refresh_title()
        # 자정을 넘기면 '오늘 누적' 표시가 새 날 기준이 되도록 메뉴를 갱신
        today = datetime.date.today()
        if today != self._cur_day:
            self._cur_day = today
            self.build_menu()
        # 런루프가 뜨면서 앱 아이콘이 번들(python) 것으로 되돌아갈 수 있어
        # 첫 tick에서 한 번 더 적용 (Cmd-Tab·rumps 기본 alert 아이콘용)
        if not self._icon_reapplied:
            self._icon_reapplied = True
            try:
                from AppKit import NSApplication
                ic = app_icon()
                if ic is not None:
                    NSApplication.sharedApplication().setApplicationIconImage_(ic)
            except Exception:
                pass
        # 첫 tick: 재시작 시 오래된 '진행 중' 세션이 있으면 확인
        if not self._startup_checked:
            self._startup_checked = True
            self._check_stale_active()
        # 자리비움(유휴) 감지: 진행 중일 때만, 약 20초마다
        if self.db.get("active"):
            self._idle_counter += 1
            if self._idle_counter >= 20:
                self._idle_counter = 0
                self._check_idle()
        else:
            self._idle_counter = 0
            self._idle_notified = False

    # ----- 재시작 시 오래된 세션 처리 -----
    def _check_stale_active(self):
        a = self.db.get("active")
        if not a:
            return
        elapsed = time.time() - a.get("start", time.time())
        today = datetime.date.today().strftime("%Y-%m-%d")
        if elapsed <= STALE_LIMIT and day_of(a["start"]) == today:
            return   # 최근(같은 날·1시간 이내) → 그대로 이어서
        r = alert3(
            "진행 중이던 기록이 있어요",
            f"'{a['name']}' 시작 후 {fmt_dur(elapsed)} 지났어요.\n"
            f"앱이 꺼져 있던 시간도 포함됐을 수 있어요. 어떻게 할까요?",
            "지금까지로 저장", "버리기", "계속 진행")
        if r == 1:
            self.stop(None)
        elif r == 2:
            self.cancel(None)
        # r == 3: 그대로 계속

    # ----- 자리비움 감지 -----
    def _check_idle(self):
        if idle_seconds() >= IDLE_LIMIT:
            if not self._idle_notified:
                self._idle_notified = True
                a = self.db.get("active")
                nm = a["name"] if a else ""
                notify(
                    "자리 비움 감지", f"'{nm}' 아직 기록 중이에요",
                    "한참 입력이 없네요. 멈추려면 '종료하고 저장'을 누르세요.")
        else:
            self._idle_notified = False

    # ----- 할 일 추가/수정/삭제 -----
    def add_tasks(self, _):
        text = batch_add_dialog()
        if text is None:
            return
        existing = {t["name"] for t in self.db.get("tasks", [])}
        added = skipped = 0
        for line in str(text).splitlines():
            nm, est = parse_task_line(line)
            if not nm:
                continue
            if nm in existing:        # 같은 이름 중복 방지
                skipped += 1
                continue
            existing.add(nm)
            self.db.setdefault("tasks", []).append(
                {"name": nm, "est": est, "done": False, "id": new_id()})
            added += 1
        if added:
            save(self.db)
            self.build_menu()
        if added or skipped:
            msg = f"{added}개 추가" + (f" · 중복 {skipped}개 건너뜀" if skipped else "")
            notify("할 일 추가됨", "", msg)

    def edit_task(self, sender):
        t = self._edit_map.get(sender.title)
        if not t:
            return
        old_name = t["name"]
        upd = edit_task_dialog(t.get("name", ""), t.get("est", 0))
        if not upd:
            return
        new_name = upd["name"]
        if new_name != old_name and any(
                o is not t and o.get("name") == new_name
                for o in self.db.get("tasks", [])):
            alert("이름 중복", f"'{new_name}' 은(는) 이미 있는 할 일이에요.")
            return
        t["name"], t["est"] = new_name, upd["est"]
        if new_name != old_name:
            # 이 할 일에 속한 기록만(task_id 기준) 함께 이름 변경.
            # 과거 같은 이름이던 다른 할 일의 기록은 task_id가 달라 건드리지 않음.
            tid = t.get("id")
            if tid:
                for e in self.db.get("entries", []):
                    if e.get("task_id") == tid:
                        e["name"] = new_name
                a = self.db.get("active")
                if a and a.get("task_id") == tid:
                    a["name"] = new_name
        save(self.db)
        self.build_menu()
        self.refresh_title()

    # ----- 기록 개별 수정/삭제 -----
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
            e["end"] = e.get("start", 0) + data["dur"]   # 시간 일관성 유지
        save(self.db)
        self.build_menu()

    def delete_task(self, sender):
        t = self._del_map.get(sender.title)
        if not t:
            return
        if alert(title="할 일 삭제",
                       message=f"'{t['name']}' 을(를) 목록에서 지울까요?\n(이미 기록된 시간은 그대로 남아요)",
                       ok="삭제", cancel="취소") == 1:
            try:
                self.db["tasks"].remove(t)
            except ValueError:
                pass
            save(self.db)
            self.build_menu()

    # ----- 할 일 완료 / 완료 취소 -----
    def complete_task(self, sender):
        t = self._done_map.get(sender.title)
        if not t:
            return
        # 지금 그 할 일을 진행 중이면 먼저 멈춰서 저장(누적에 반영)
        a = self.db.get("active")
        if a and a.get("name") == t["name"]:
            self.stop(None)
        t["done"] = True
        t["done_at"] = time.time()
        save(self.db)
        self.build_menu()
        self.refresh_title()
        total = self.total_of(t["name"])
        est = t.get("est", 0)
        cmp_txt = (f" · 예상 {fmt_est(est)} 대비 {round(total / (est * 60) * 100)}%"
                   if est else "")
        notify("할 일 완료 🎉", t["name"], f"누적 {fmt_dur(total)}{cmp_txt} · 수고했어요!")

    def reopen_task(self, sender):
        t = self._reopen_map.get(sender.title)
        if not t:
            return
        t["done"] = False
        t.pop("done_at", None)
        save(self.db)
        self.build_menu()

    # ----- 누적(전체) 실제 시간 -----
    def total_of(self, name):
        """이 할 일에 쓴 전체(누적) 실제 시간(초). 저장된 모든 기록의 합."""
        return sum(e["dur"] for e in self.db.get("entries", [])
                   if e.get("name") == name)

    # ----- 전체 할 일 합산 누적 시간 -----
    def grand_total(self):
        """모든 할 일에 쓴 총 누적 실제 시간(초) + 진행 중 세션 실시간 반영."""
        total = sum(e["dur"] for e in self.db.get("entries", []))
        a = self.db.get("active")
        if a:
            run = round(time.time() - a["start"])
            if run >= 1:
                total += run
        return total

    # ----- 오늘 누적 시간 (보조 표시용) -----
    def today_total(self, name):
        today = datetime.date.today().strftime("%Y-%m-%d")
        return sum(e["dur"] for e in self.db.get("entries", [])
                   if e.get("name") == name and day_of(e["start"]) == today)

    # ----- 예상 시간(분) 조회 -----
    def est_of(self, name):
        for t in self.db.get("tasks", []):
            if t.get("name") == name:
                return t.get("est", 0)
        return 0

    # ----- 시작 목록용 라벨: 이름 (총 누적 · 예상) -----
    def start_label(self, t):
        name = t["name"]
        parts = []
        total = self.total_of(name)
        if total > 0:
            parts.append(f"총 누적 {fmt_dur(total)}")
        if t.get("est"):
            parts.append(f"예상 {fmt_est(t['est'])}")
        return f"{name}   ({' · '.join(parts)})" if parts else name

    # ----- 시작 (목록에서 선택, 지금까지 누적한 만큼 이어서) -----
    def start_task(self, sender):
        t = self._task_map.get(sender.title)
        if not t:
            return
        # base = 지금까지 쌓인 전체 시간 → 진행 표시는 이 위에 이어서 누적
        self.db["active"] = {
            "name": t["name"], "task_id": t.get("id"), "start": time.time(),
            "base": self.total_of(t["name"]),
        }
        save(self.db)
        self.build_menu()
        self.refresh_title()

    # ----- 종료/저장 -----
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
        save(self.db)
        self.build_menu()
        self.refresh_title()
        total = a.get("base", 0) + dur   # 이번 세션까지 합한 전체(누적) 시간
        est = self.est_of(a["name"])
        if est:
            pct = round(total / (est * 60) * 100)
            cmp_txt = f" · 예상 {fmt_est(est)} 대비 {pct}%" + (" ⚠️초과" if total > est * 60 else "")
        else:
            cmp_txt = ""
        notify("기록 저장됨", a["name"],
               f"이번 {fmt_dur(dur)} · 누적 {fmt_dur(total)}{cmp_txt} 👍")

    def cancel(self, _):
        self.db["active"] = None
        save(self.db)
        self.build_menu()
        self.refresh_title()

    # ----- 진행 현황 (누적): 할 일별 실제 누적 vs 예상 -----
    def progress_summary(self, _):
        # 할 일별 누적 실제 시간(전체 기록 합) + 진행 중 세션 실시간 반영
        act = {}
        for e in self.db.get("entries", []):
            act[e["name"]] = act.get(e["name"], 0) + e["dur"]
        a = self.db.get("active")
        if a:
            run = round(time.time() - a["start"])
            if run >= 1:
                act[a["name"]] = act.get(a["name"], 0) + run
        tasks = self.db.get("tasks", [])
        rows = [t for t in tasks if act.get(t["name"], 0) > 0 or t.get("est")]
        if not rows:
            alert("진행 현황", "아직 기록된 할 일이 없어요.")
            return
        # 미완료 먼저, 그 안에서 실제 많은 순
        rows.sort(key=lambda t: (bool(t.get("done")), -act.get(t["name"], 0)))
        lines = []
        for t in rows:
            nm = t["name"]
            sec = act.get(nm, 0)
            est = t.get("est", 0)
            mark = "✅ " if t.get("done") else ""
            if est:
                pct = round(sec / (est * 60) * 100)
                over = sec > est * 60
                tag = (f"실제 {fmt_dur(sec)} / 예상 {fmt_est(est)} · {pct}%"
                       + (" ⚠️초과" if over else ""))
            else:
                tag = f"실제 {fmt_dur(sec)} · 예상 미설정"
            lines.append(f"• {mark}{nm}\n   {tag}")
        alert(title="🎯 진행 현황 (누적)", message="\n".join(lines))

    # ----- 오늘 요약 (오늘 한 일: 항목별 실제 / 비율) -----
    def today_summary(self, _):
        today = datetime.date.today().strftime("%Y-%m-%d")
        # 같은 항목끼리 오늘 실제 소요시간 누적
        by = {}
        for e in self.db["entries"]:
            if day_of(e["start"]) == today:
                by[e["name"]] = by.get(e["name"], 0) + e["dur"]
        # 진행 중인 세션도 실시간 반영
        a = self.db.get("active")
        if a and day_of(a["start"]) == today:
            run = round(time.time() - a["start"])
            if run >= 1:
                by[a["name"]] = by.get(a["name"], 0) + run
        if not by:
            alert("오늘 요약", "오늘은 아직 기록이 없어요.")
            return
        total = sum(by.values())
        lines = [f"오늘 총 {fmt_dur(total)}\n"]
        for name, sec in sorted(by.items(), key=lambda x: -x[1]):
            pct = round(sec / total * 100) if total else 0
            lines.append(f"• {name}\n   {fmt_dur(sec)} · 오늘의 {pct}%")
        lines.append("\n(예상 대비 누적은 '진행 현황'에서 볼 수 있어요)")
        alert(title="📋 오늘 요약", message="\n".join(lines))

    # ----- 상세 보기(HTML) -----
    def open_report(self, _):
        with open(REPORT, "w", encoding="utf-8") as f:
            f.write(build_report(self.db))
        webbrowser.open("file://" + REPORT)


# ---------- 상세 보기 HTML ----------
def build_report(db):
    data_json = json.dumps(db, ensure_ascii=False)
    return REPORT_HTML.replace("__DATA__", data_json).replace("__ACCENT__", ACCENT)


REPORT_HTML = r"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📕 내 업무 기록 — 상세</title>
<style>
:root{--bg:#0f1117;--card:#1a1d27;--card2:#232734;--line:#2c3140;--txt:#e7e9ee;--sub:#9aa1b1;--accent:#6366f1;--accent2:#8b5cf6;--green:#22c55e;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;background:var(--bg);color:var(--txt);padding:18px;max-width:780px;margin:0 auto;}
h1{font-size:20px;margin:4px 0 16px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:14px;}
.label{font-size:12px;color:var(--sub);margin-bottom:8px;font-weight:600;}
.datenav{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.datenav button{background:var(--card2);color:var(--txt);border:none;border-radius:10px;padding:8px 16px;font-size:18px;cursor:pointer;}
.cur{text-align:center;font-weight:600;font-size:15px;}.cur small{display:block;color:var(--sub);font-size:12px;font-weight:400;}
.total{display:flex;justify-content:space-between;align-items:baseline;}.total .big{font-size:28px;font-weight:700;}
.entry{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid var(--line);}.entry:last-child{border-bottom:none;}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}.entry .meta{flex:1;min-width:0;}
.entry .nm{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}.entry .tm{font-size:12px;color:var(--sub);}
.entry .dur{font-variant-numeric:tabular-nums;font-weight:600;}.empty{color:var(--sub);text-align:center;padding:20px 0;font-size:14px;}
.catstat{margin:10px 0;}.catstat .top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px;}
.catstat .bar{height:9px;border-radius:5px;background:var(--card2);overflow:hidden;}.catstat .fill{height:100%;border-radius:5px;}
.chart{display:flex;align-items:flex-end;gap:8px;height:150px;padding-top:8px;}
.chart .col{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;height:100%;justify-content:flex-end;cursor:pointer;}
.chart .barwrap{width:100%;flex:1;display:flex;align-items:flex-end;}
.chart .b{width:100%;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--accent),var(--accent2));min-height:2px;}
.chart .b.today{background:linear-gradient(180deg,var(--green),#15803d);}
.chart .lbl{font-size:11px;color:var(--sub);}.chart .val{font-size:10px;color:var(--sub);height:12px;}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.tab{padding:7px 14px;border-radius:20px;font-size:13px;cursor:pointer;background:var(--card2);border:1px solid var(--line);color:var(--sub);user-select:none;}
.tab.on{background:var(--accent);color:#fff;border-color:transparent;}
</style></head><body>
<h1>📕 내 업무 기록</h1>
<div class="card">
  <div class="tabs" id="tabs"></div>
  <div class="datenav">
    <button id="prev" onclick="move(-1)">‹</button>
    <div class="cur"><span id="vd"></span></div>
    <button id="next" onclick="move(1)">›</button>
  </div>
</div>
<div class="card"><div class="total"><div class="label" style="margin:0" id="totlbl">한 일</div><div class="big" id="tot">0분</div></div>
  <div id="list" style="margin-top:12px"></div></div>
<div class="card"><div class="label" id="chartlbl">추이</div><div class="chart" id="week"></div></div>
<div class="card"><div class="label" id="cmplbl">🎯 예상 vs 실제</div><div id="cmp"></div></div>
<script>
const DB=__DATA__;
const ACCENT="__ACCENT__";
const DOW=["일","월","화","수","목","금","토"];
const PERIODS=[["day","오늘"],["week","주"],["month","월"],["year","년"],["all","전체"]];
let mode="day";
let anchor=midnight(new Date());
function midnight(d){return new Date(d.getFullYear(),d.getMonth(),d.getDate());}
function sec(d){return d.getTime()/1000;}
function col(){return ACCENT;}
function fdur(s){s=Math.floor(s);const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);if(h)return m?h+"시간 "+m+"분":h+"시간";if(m)return m+"분";return s+"초";}
function tod(ts){const d=new Date(ts*1000);return String(d.getHours()).padStart(2,"0")+":"+String(d.getMinutes()).padStart(2,"0");}
function md(ts){const d=new Date(ts*1000);return (d.getMonth()+1)+"/"+d.getDate();}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function weekStart(d){const x=midnight(d);const wd=(x.getDay()+6)%7;x.setDate(x.getDate()-wd);return x;}
function range(){
  const a=anchor;
  if(mode==="day"){const s=midnight(a);return {s:sec(s),e:sec(s)+86400};}
  if(mode==="week"){const s=weekStart(a);const e=new Date(s);e.setDate(e.getDate()+7);return {s:sec(s),e:sec(e)};}
  if(mode==="month"){return {s:sec(new Date(a.getFullYear(),a.getMonth(),1)),e:sec(new Date(a.getFullYear(),a.getMonth()+1,1))};}
  if(mode==="year"){return {s:sec(new Date(a.getFullYear(),0,1)),e:sec(new Date(a.getFullYear()+1,0,1))};}
  return {s:0,e:Date.now()/1000+86400};
}
function setMode(m){mode=m;anchor=midnight(new Date());render();}
function move(n){
  if(mode==="all")return;
  const a=anchor;const shift=k=>{if(mode==="day")a.setDate(a.getDate()+k);else if(mode==="week")a.setDate(a.getDate()+7*k);else if(mode==="month")a.setMonth(a.getMonth()+k);else if(mode==="year")a.setFullYear(a.getFullYear()+k);};
  shift(n);
  if(range().s>Date.now()/1000){shift(-n);return;}
  render();
}
function periodLabel(){
  const a=anchor,now=new Date();
  if(mode==="day"){const diff=Math.round((midnight(a)-midnight(now))/86400000);
    if(diff===0)return "오늘";if(diff===-1)return "어제";if(diff===1)return "내일";
    return (a.getMonth()+1)+"월 "+a.getDate()+"일 ("+DOW[a.getDay()]+")";}
  if(mode==="week"){const s=weekStart(a),e=new Date(s);e.setDate(e.getDate()+6);
    const cur=weekStart(now).getTime()===s.getTime();
    return (cur?"이번 주 · ":"")+(s.getMonth()+1)+"/"+s.getDate()+" ~ "+(e.getMonth()+1)+"/"+e.getDate();}
  if(mode==="month"){const cur=a.getFullYear()===now.getFullYear()&&a.getMonth()===now.getMonth();
    return a.getFullYear()+"년 "+(a.getMonth()+1)+"월"+(cur?" · 이번 달":"");}
  if(mode==="year"){const cur=a.getFullYear()===now.getFullYear();return a.getFullYear()+"년"+(cur?" · 올해":"");}
  return "전체 기간";
}
function inRange(){const r=range();return DB.entries.filter(x=>x.start>=r.s&&x.start<r.e);}
function bucketSum(s,e){return DB.entries.filter(x=>x.start>=s&&x.start<e).reduce((a,x)=>a+x.dur,0);}
function render(){
  document.getElementById("tabs").innerHTML=PERIODS.map(p=>'<div class="tab'+(p[0]===mode?" on":"")+'" onclick="setMode(\''+p[0]+'\')">'+p[1]+'</div>').join("");
  document.getElementById("vd").textContent=periodLabel();
  const vis=mode==="all"?"hidden":"visible";
  document.getElementById("prev").style.visibility=vis;document.getElementById("next").style.visibility=vis;
  const list=inRange().sort((a,b)=>a.start-b.start);
  const total=list.reduce((s,e)=>s+e.dur,0);
  document.getElementById("totlbl").textContent=({day:"이 날 한 일",week:"이 주 한 일",month:"이 달 한 일",year:"이 해 한 일",all:"전체 한 일"})[mode];
  document.getElementById("tot").textContent=fdur(total);
  renderList(list);renderChart();renderCmp();
}
function renderList(list){
  const lb=document.getElementById("list");
  if(!list.length){lb.innerHTML='<div class="empty">기록이 없어요.</div>';return;}
  if(mode==="day"||mode==="week"){
    lb.innerHTML=list.map(e=>'<div class="entry"><span class="dot" style="background:'+col()+'"></span><div class="meta"><div class="nm">'+esc(e.name)+'</div><div class="tm">'+(mode==="week"?md(e.start)+" ":"")+tod(e.start)+'~'+tod(e.end)+'</div></div><div class="dur">'+fdur(e.dur)+'</div></div>').join("");
  }else{
    const agg={};list.forEach(e=>{const k=e.name;(agg[k]=agg[k]||{name:e.name,sec:0,n:0});agg[k].sec+=e.dur;agg[k].n++;});
    lb.innerHTML=Object.values(agg).sort((a,b)=>b.sec-a.sec).map(a=>'<div class="entry"><span class="dot" style="background:'+col()+'"></span><div class="meta"><div class="nm">'+esc(a.name)+'</div><div class="tm">'+a.n+'회</div></div><div class="dur">'+fdur(a.sec)+'</div></div>').join("");
  }
}
function renderChart(){
  const w=document.getElementById("week"),lbl=document.getElementById("chartlbl"),now=new Date();let b=[];
  if(mode==="day"){lbl.textContent="최근 7일";
    for(let i=6;i>=0;i--){const d=new Date(anchor);d.setDate(d.getDate()-i);const s=sec(midnight(d));b.push({l:DOW[d.getDay()],s,e:s+86400,hl:midnight(d).getTime()===midnight(now).getTime()});}}
  else if(mode==="week"){lbl.textContent="요일별";const ws=weekStart(anchor);
    for(let i=0;i<7;i++){const d=new Date(ws);d.setDate(d.getDate()+i);const s=sec(midnight(d));b.push({l:DOW[d.getDay()],s,e:s+86400,hl:midnight(d).getTime()===midnight(now).getTime()});}}
  else if(mode==="month"){lbl.textContent="일별";const y=anchor.getFullYear(),m=anchor.getMonth(),last=new Date(y,m+1,0).getDate();
    for(let day=1;day<=last;day++){const d=new Date(y,m,day),s=sec(d);b.push({l:String(day),s,e:s+86400,hl:midnight(now).getTime()===d.getTime(),sm:1});}}
  else if(mode==="year"){lbl.textContent="월별";const y=anchor.getFullYear();
    for(let mo=0;mo<12;mo++){b.push({l:(mo+1),s:sec(new Date(y,mo,1)),e:sec(new Date(y,mo+1,1)),hl:now.getFullYear()===y&&now.getMonth()===mo});}}
  else{lbl.textContent="최근 12개월";
    for(let i=11;i>=0;i--){const d=new Date(now.getFullYear(),now.getMonth()-i,1);b.push({l:(d.getMonth()+1),s:sec(d),e:sec(new Date(d.getFullYear(),d.getMonth()+1,1)),hl:i===0,sm:1});}}
  b.forEach(x=>x.sec=bucketSum(x.s,x.e));
  const max=Math.max(1,...b.map(x=>x.sec));
  w.innerHTML=b.map(x=>'<div class="col"><div class="val">'+(x.sec>0?(Math.round(x.sec/360)/10)+"h":"")+'</div><div class="barwrap"><div class="b'+(x.hl?" today":"")+'" style="height:'+Math.round(x.sec/max*100)+'%"></div></div><div class="lbl"'+(x.sm?' style="font-size:9px"':'')+'>'+x.l+'</div></div>').join("");
}
function renderCmp(){
  // 예상 vs 실제는 '할 일' 단위 누적(전체 기간) 기준 — 기간 선택과 무관
  const box=document.getElementById("cmp"),tasks=DB.tasks||[];
  document.getElementById("cmplbl").textContent="🎯 예상 vs 실제 (누적)";
  if(!tasks.length){box.innerHTML='<div class="empty">등록된 할 일이 없어요.</div>';return;}
  const actBy={};DB.entries.forEach(e=>{actBy[e.name]=(actBy[e.name]||0)+e.dur;});
  if(DB.active){const r=Math.max(0,Date.now()/1000-DB.active.start);actBy[DB.active.name]=(actBy[DB.active.name]||0)+r;}
  const rows=tasks.map(t=>({t,act:actBy[t.name]||0})).filter(r=>r.act>0||(r.t.est||0)>0)
    .sort((a,b)=>(a.t.done?1:0)-(b.t.done?1:0)||b.act-a.act);
  if(!rows.length){box.innerHTML='<div class="empty">아직 기록이 없어요.</div>';return;}
  box.innerHTML=rows.map(({t,act})=>{
    const est=(t.est||0)*60;let right,fillW,fillC;
    const nm=(t.done?'✅ ':'')+esc(t.name);
    if(est>0){const pct=Math.round(act/est*100),over=act>est,diff=Math.abs(act-est);
      right='실제 '+fdur(act)+' / 예상 '+fdur(est)+'  <b style="color:'+(over?"#ef4444":"#22c55e")+'">'+pct+'%</b>'+(act>0?' ('+(over?"+":"-")+fdur(diff)+')':'');
      fillW=Math.min(100,pct);fillC=over?"#ef4444":"#22c55e";}
    else{right='실제 '+fdur(act)+' · <span style="color:var(--sub)">예상 미설정</span>';fillW=act>0?100:0;fillC=col();}
    return '<div class="catstat"><div class="top"><span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+col()+';margin-right:6px"></span>'+nm+'</span><span style="color:var(--sub)">'+right+'</span></div><div class="bar"><div class="fill" style="width:'+fillW+'%;background:'+fillC+'"></div></div></div>';
  }).join("");
}
render();
</script></body></html>"""


if __name__ == "__main__":
    fix_bundle_identifier()   # 알림 아이콘이 Python 로켓으로 뜨지 않게
    if already_running():
        # 이미 메뉴바에 떠 있음 → 아이콘 중복 방지를 위해 조용히 종료
        sys.exit(0)
    Tracker().run()
