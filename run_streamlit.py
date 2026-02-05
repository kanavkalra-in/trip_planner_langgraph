#!/usr/bin/env python3
"""Script to run the Streamlit app."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    streamlit_app = Path(__file__).parent / "src" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_app)])
