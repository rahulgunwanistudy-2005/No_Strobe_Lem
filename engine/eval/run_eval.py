"""Compatibility entry point; the installed runner is exposed as nostrobe eval."""

from nostrobe.cli import app

if __name__ == "__main__":
    app(["eval"])
