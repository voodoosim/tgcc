# ui/main.py
"""Veronica main execution file"""
import logging
import sys
import warnings

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow

# Ignore SSL warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*SSL.*")

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("veronica.log", encoding="utf-8"), logging.StreamHandler()],
)

# Adjust external library logging levels
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("pyrogram.crypto").setLevel(logging.ERROR)
logging.getLogger("pyrogram.session").setLevel(logging.ERROR)


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern style

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
