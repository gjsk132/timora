from .assets import app_icon
from .i18n import t

_NS_FIRST_BUTTON = 1000  # NSAlertFirstButtonReturn


def _bring_front():
    try:
        from AppKit import NSApp
        NSApp.activateIgnoringOtherApps_(True)
    except Exception:
        pass


def alert3(title, message, b1, b2, b3):
    """Three-button alert. Returns the pressed button number (1/2/3)."""
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


def alert(title="", message="", ok=None, cancel=None):
    """Alert/confirm dialog. Returns 1 for OK, 0 for cancel."""
    from AppKit import NSAlert
    a = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        a.setIcon_(ic)
    a.setMessageText_(str(title))
    a.setInformativeText_(str(message))
    a.addButtonWithTitle_(ok or t("ok"))
    if cancel is not None:
        a.addButtonWithTitle_(cancel if isinstance(cancel, str) else t("cancel"))
    _bring_front()
    return 1 if a.runModal() == _NS_FIRST_BUTTON else 0


def batch_add_dialog():
    """Multi-line dialog to add several tasks. Returns text, or None on cancel."""
    from AppKit import (NSAlert, NSScrollView, NSTextView, NSMakeRect, NSFont)
    alert = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        alert.setIcon_(ic)
    alert.setMessageText_(t("batch_title"))
    alert.setInformativeText_(t("batch_info"))
    alert.addButtonWithTitle_(t("add"))
    alert.addButtonWithTitle_(t("cancel"))

    width, ta_h = 340, 160
    scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, width, ta_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setBorderType_(2)
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


def edit_task_dialog(name="", est=0):
    """Edit a task's name and estimate. Returns dict, or None on cancel."""
    from AppKit import (NSAlert, NSTextField, NSView, NSMakeRect)
    alert = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        alert.setIcon_(ic)
    alert.setMessageText_(t("edit_task_title"))
    alert.addButtonWithTitle_(t("save"))
    alert.addButtonWithTitle_(t("cancel"))

    width, row, gap = 300, 24, 10
    h = row * 2 + gap
    cont = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, h))
    name_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - row, width, row))
    name_f.setStringValue_(name)
    name_f.setPlaceholderString_(t("ph_task_name"))
    est_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, row))
    est_f.setStringValue_(str(est) if est else "")
    est_f.setPlaceholderString_(t("ph_est"))
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
    """Edit or delete a record.
    Returns ('save', {name,dur}) / ('delete', None) / None (cancel)."""
    from AppKit import (NSAlert, NSTextField, NSView, NSMakeRect)
    a = NSAlert.alloc().init()
    ic = app_icon()
    if ic is not None:
        a.setIcon_(ic)
    a.setMessageText_(t("edit_record_title"))
    a.setInformativeText_(t("edit_record_info"))
    a.addButtonWithTitle_(t("save"))
    a.addButtonWithTitle_(t("del_ok"))
    a.addButtonWithTitle_(t("cancel"))

    width, row, gap = 300, 24, 10
    h = row * 2 + gap
    cont = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, h))
    name_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - row, width, row))
    name_f.setStringValue_(name)
    name_f.setPlaceholderString_(t("ph_task_name"))
    min_f = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, row))
    min_f.setStringValue_(str(max(1, round(dur_sec / 60))))
    min_f.setPlaceholderString_(t("ph_actual"))
    cont.addSubview_(name_f)
    cont.addSubview_(min_f)

    a.setAccessoryView_(cont)
    _bring_front()
    try:
        a.window().setInitialFirstResponder_(min_f)
    except Exception:
        pass
    r = a.runModal()
    if r == 1001:
        return ("delete", None)
    if r != _NS_FIRST_BUTTON:
        return None
    nm = str(name_f.stringValue()).strip()
    digits = "".join(c for c in str(min_f.stringValue()) if c.isdigit())
    mins = int(digits) if digits else 0
    if not nm or mins <= 0:
        return None
    return ("save", {"name": nm, "dur": mins * 60})
