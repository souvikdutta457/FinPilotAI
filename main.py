"""
main.py
-------
FinPilot AI - Application Entry Point

Launches the GUI. Run this from the project root:

    python main.py
"""

import os
import sys

# Make src/ importable as flat modules (matches how gui.py imports,
# e.g. "from ai_engine import ...") without turning it into a package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    import gui  # noqa: F401  (gui.py builds and runs the window on import)
