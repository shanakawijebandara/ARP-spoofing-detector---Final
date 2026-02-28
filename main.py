
"""
Startup sequence
────────────────
1. Check for admin / root privileges (required by Scapy for raw sockets).
2. Verify that Scapy is installed.
3. Show a 2-second splash screen.
4. Instantiate ARPDetector, EventLogger, and ARPDetectorGUI.
5. Hand control to the Tk event loop.

Run command (Windows – from an elevated terminal):
    python main.py

Run command (Linux / macOS):
    sudo python3 main.py
"""

import ctypes
import os
import queue
import sys
import tkinter as tk
from tkinter import messagebox

try:
    import scapy  # noqa: F401
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False

from detector import ARPDetector
from gui      import ARPDetectorGUI
from logger   import EventLogger




def _is_admin() -> bool:
    """Return True if the process has administrator / root privileges."""
    try:
        if sys.platform == "win32":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            return os.getuid() == 0
    except Exception:
        return False


def _relaunch_as_admin() -> None:
    """Re-launch this script with elevated privileges (Windows only)."""
    if sys.platform == "win32":
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas",
            sys.executable,
            " ".join(f'"{a}"' for a in sys.argv),
            None, 1,
        )


def _show_splash() -> None:
    """Display a brief splash window while the main app initialises."""
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#1a1a2e")

    w, h = 420, 240
    sw   = splash.winfo_screenwidth()
    sh   = splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

    # ── Content ──────────────────────────────────────────────────────────────
    tk.Label(splash, text="🛡",
             font=("Segoe UI Emoji", 44),
             bg="#1a1a2e", fg="#00d4aa").pack(pady=(28, 8))

    tk.Label(splash, text="ARP  SPOOFING  DETECTOR",
             font=("Segoe UI", 15, "bold"),
             bg="#1a1a2e", fg="#e0e0e0").pack()

    tk.Label(splash, text="Real-time Network Security Monitor",
             font=("Segoe UI", 9),
             bg="#1a1a2e", fg="#8892a4").pack(pady=4)

    progress_lbl = tk.Label(splash, text="Initialising…",
                             font=("Segoe UI", 8, "italic"),
                             bg="#1a1a2e", fg="#00d4aa")
    progress_lbl.pack(pady=6)

    tk.Label(splash,
             text="Angam Wijebandara  |  Plymouth ID: 10954873  |  PUSL3190",
             font=("Segoe UI", 7),
             bg="#1a1a2e", fg="#444466").pack(pady=(14, 0))

    # ── Animate progress text ────────────────────────────────────────────────
    steps = ["Initialising…", "Loading interfaces…",
             "Starting logger…", "Launching GUI…"]

    def _step(i: int = 0):
        if i < len(steps):
            progress_lbl.config(text=steps[i])
            splash.after(400, _step, i + 1)
        else:
            splash.destroy()

    splash.after(200, _step)
    splash.mainloop()


def main() -> None:

    if not _is_admin():
        _root = tk.Tk()
        _root.withdraw()
        answer = messagebox.askyesno(
            "Administrator Privileges Required",
            "ARP Spoofing Detector needs administrator / root privileges\n"
            "so that Scapy can access raw network sockets.\n\n"
            "• Click  YES  to restart with elevated privileges (Windows).\n"
            "• Click  NO   to continue anyway  "
            "(scanning / monitoring may fail).",
            icon="warning",
        )
        _root.destroy()

        if answer and sys.platform == "win32":
            _relaunch_as_admin()
            return

    if not SCAPY_OK:
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "Scapy Not Found",
            "The Scapy library is not installed.\n\n"
            "Install it by running (in an elevated terminal):\n\n"
            "    pip install scapy\n\n"
            "On Windows you also need Npcap:\n"
            "    https://npcap.com  →  download the installer\n"
            "    (enable 'WinPcap API-compatible Mode' during install)",
        )
        _root.destroy()
        return

    _show_splash()

    eq       = queue.Queue(maxsize=2000)
    logger   = EventLogger()
    detector = ARPDetector(event_queue=eq)

    # ── 5. Launch GUI ─────────────────────────────────────────────────────
    root = tk.Tk()
    app  = ARPDetectorGUI(root, detector, logger)

    logger.log_info("=" * 55)
    logger.log_info("Application started")
    logger.log_info(f"Python  : {sys.version.split()[0]}")
    logger.log_info(f"Platform: {sys.platform}")
    logger.log_info("=" * 55)

    app._log_append(
        "Application ready.  Select your interface → Scan Network → "
        "Start Monitoring.", "ok"
    )


    def _on_close():
        if detector.is_monitoring:
            if messagebox.askyesno(
                "Exit",
                "Monitoring is currently active.\nStop monitoring and exit?",
            ):
                detector.stop_monitoring()
                logger.log_info("Application closed by user (monitoring was active)")
                root.destroy()
        else:
            logger.log_info("Application closed by user")
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)

    # ── 7. Enter Tk event loop ────────────────────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    main()
