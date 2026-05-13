import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from ui.web_main import run_web_ui

    run_web_ui()


if __name__ == "__main__":
    main()
