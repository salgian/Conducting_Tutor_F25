# This is going to be the overall main.
# Launches the Tkinter UI instead of the command-line interface

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tkinter as tk
from src.views._window import MainWindow

def main():
    """Launch the Conducting Tutor UI application."""
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
