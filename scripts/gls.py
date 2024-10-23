import sys
import pyperclip
from pathlib import Path


def worker(text, file):
    content = []
    if text is not None:
        items = text.split(",")
        for item in items:
            full, short = item.split("(")
            full = full.strip()
            short = short.strip(")")
            short_lower = short.lower()

            result = f"\\newacronym{{{short_lower}}}{{{short}}}{{{full}}}"
            print(result)
            content.append(result)

        print("copying to clipboard...")
        pyperclip.copy("\n".join(content))


def main():
    if len(sys.argv) == 1:
        print("No arguments provided")

    elif len(sys.argv) == 2:
        if Path(sys.argv[1]).exists():
            worker(None, sys.argv[1])
        else:
            text = "".join(sys.argv[1:])
            worker(text, None)

    print("Exiting...")
    raise SystemExit


if __name__ == "__main__":
    main()
