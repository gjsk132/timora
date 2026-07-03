import os

from .config import BUNDLE_ICON, BUNDLE_ID, PROJECT_DIR

_APP_ICON = None
_ICON_FILE = None


def make_app_icon(size=512):
    """Blue-to-indigo squircle with a white hourglass. Returns NSImage or None."""
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


def app_icon():
    global _APP_ICON
    if _APP_ICON is None:
        _APP_ICON = make_app_icon()
    return _APP_ICON


def icon_file():
    """File path of the app icon for notifications (cached)."""
    global _ICON_FILE
    if _ICON_FILE is not None:
        return _ICON_FILE or None
    if os.path.exists(BUNDLE_ICON):
        _ICON_FILE = BUNDLE_ICON
        return _ICON_FILE
    try:
        from AppKit import NSBitmapImageRep
        img = app_icon()
        if img is not None:
            rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
            png = rep.representationUsingType_properties_(4, None)
            out = os.path.join(PROJECT_DIR, ".appicon.png")
            png.writeToFile_atomically_(out, True)
            _ICON_FILE = out
            return _ICON_FILE
    except Exception:
        pass
    _ICON_FILE = ""
    return None


def fix_bundle_identifier():
    """Make notifications show Timora's icon instead of the Python rocket."""
    try:
        from Foundation import NSBundle
        info = NSBundle.mainBundle().infoDictionary()
        if info is not None:
            info["CFBundleIdentifier"] = BUNDLE_ID
    except Exception:
        pass


def sf_image(name):
    """Return an SF Symbol template image (or None)."""
    try:
        from AppKit import NSImage
        img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
        if img is None:
            return None
        img.setTemplate_(True)
        return img
    except Exception:
        return None
