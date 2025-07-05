#!/usr/bin/env python
"""
Veronica Project Launcher
Simple launcher script to run from project root
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from ui.main import main

        main()

    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("\nPlease make sure you have installed all requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)
