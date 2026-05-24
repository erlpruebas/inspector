from __future__ import annotations

from .desktop_user_ui import DesktopUserInterface


def main() -> int:
    DesktopUserInterface().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
