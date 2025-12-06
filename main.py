"""Entry point for UniProtKB Protein Finder application.

This script launches the GUI application. It ensures all required modules
can be imported by adjusting the Python path.

Usage:
    python main.py

Requirements:
    - Python 3.7+
    - requests (install via: pip install -r requirements.txt)
    - Tkinter (usually included with Python)
"""

import sys
from pathlib import Path

# Ensure the application module is in the path
app_path = Path(__file__).parent
sys.path.insert(0, str(app_path))

try:
    from ui import run_gui
except ImportError as e:
    print(f"Error: Could not import UI module: {e}", file=sys.stderr)
    print("Make sure all dependencies are installed:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


def main():
    """Main entry point for the application."""
    try:
        print("Starting UniProtKB Protein Finder...")
        run_gui()
    except ImportError as e:
        print(f"Error: Missing dependency: {e}", file=sys.stderr)
        print("Install missing packages with: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error launching application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

