import rumps

from .assets import icon_file


def notify(title, subtitle, message):
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
