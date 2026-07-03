import sys

from .assets import fix_bundle_identifier
from .instance import already_running
from .app import Tracker


def main():
    fix_bundle_identifier()
    if already_running():
        sys.exit(0)
    Tracker().run()


if __name__ == "__main__":
    main()
