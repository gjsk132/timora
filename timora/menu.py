import rumps

from .assets import sf_image


def MI(title, symbol=None, callback=None):
    """A rumps.MenuItem with an optional SF Symbol image."""
    mi = rumps.MenuItem(title, callback=callback)
    if symbol:
        img = sf_image(symbol)
        if img is not None:
            try:
                mi._menuitem.setImage_(img)
            except Exception:
                pass
    return mi
