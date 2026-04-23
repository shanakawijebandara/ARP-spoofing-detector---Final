
"""
Handles all persistent logging for the ARP Spoofing Detector.

Output files (auto-created inside ./logs/)
  logs/arp_detector.log  – human-readable timestamped entries (Python logging)
  logs/arp_events.csv    – structured CSV: every detection event, one row each

Public API used by the GUI
  log_event(ip, old_mac, new_mac, status, interface)
  log_info(msg)  /  log_warning(msg)  /  log_error(msg)
  get_log_lines(max_lines)   → str   (for Log tab display)
  export_to_txt(path, hosts, alerts)  → bool
  export_to_csv(path, hosts, alerts)  → bool
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path


class EventLogger:
    """Manages all file-based logging for the application."""

    LOG_DIR  = "logs"
    LOG_FILE = os.path.join("logs", "arp_detector.log")
    CSV_FILE = os.path.join("logs", "arp_events.csv")

    CSV_HEADERS = [
        "timestamp", "ip_address", "old_mac",
        "new_mac", "status", "interface",
    ]

    def __init__(self):
        self._ensure_dirs()
        self._init_file_logger()
        self._init_csv()

    def _ensure_dirs(self) -> None:
        Path(self.LOG_DIR).mkdir(parents=True, exist_ok=True)

    def _init_file_logger(self) -> None:
        """Configure Python's logging module to write to LOG_FILE."""
        self._logger = logging.getLogger("ARPDetector")
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.handlers:
            fh = logging.FileHandler(self.LOG_FILE, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                fmt="%(asctime)s  [%(levelname)-8s]  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            self._logger.addHandler(fh)

    def _init_csv(self) -> None:
        """Create the CSV file with a header row if it does not exist."""
        if not os.path.exists(self.CSV_FILE):
            try:
                with open(self.CSV_FILE, "w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerow(self.CSV_HEADERS)
            except OSError as exc:
                self._logger.error(f"Cannot create CSV file: {exc}")

    def log_event(
        self,
        ip:        str,
        old_mac:   str,
        new_mac:   str,
        status:    str,
        interface: str = "",
    ) -> None:
        """
        Record a detection event to both the CSV and the .log file.
        status should be "ATTACK", "Normal", "Whitelisted", etc.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(self.CSV_FILE, "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(
                    [ts, ip, old_mac, new_mac, status, interface]
                )
        except OSError as exc:
            self._logger.error(f"CSV write failed: {exc}")

        msg = f"IP={ip:<16}  OLD={old_mac:<19}  NEW={new_mac:<19}  [{status}]"
        if status == "ATTACK":
            self._logger.warning(msg)
        else:
            self._logger.info(msg)

    def log_info(self, msg: str) -> None:
        self._logger.info(msg)

    def log_warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def log_error(self, msg: str) -> None:
        self._logger.error(msg)

    def get_log_lines(self, max_lines: int = 300) -> str:
        """Return the last *max_lines* lines of arp_detector.log as a string."""
        try:
            with open(self.LOG_FILE, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            return "".join(lines[-max_lines:])
        except FileNotFoundError:
            return "(No log entries yet.)\n"
        except OSError as exc:
            return f"(Cannot read log file: {exc})\n"

    def export_to_txt(self, filepath: str, hosts: dict, alerts: list) -> bool:
        """
        Write a human-readable report to *filepath*.
        Returns True on success, False on error.
        """
        try:
            with open(filepath, "w", encoding="utf-8") as fh:
                _w = fh.write

                _w("=" * 65 + "\n")
                _w("   ARP SPOOFING DETECTOR  –  SESSION EXPORT REPORT\n")
                _w(f"   Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                _w(f"   Author    : Angam Wijebandara  |  Plymouth ID: 10954873\n")
                _w("=" * 65 + "\n\n")

                _w(f"DEVICES DISCOVERED  ({len(hosts)})\n")
                _w("-" * 65 + "\n")
                hdr = f"{'IP Address':<18} {'MAC Address':<20} {'Status':<14} {'Packets':>7}\n"
                _w(hdr)
                _w("-" * 65 + "\n")
                for ip, dev in sorted(hosts.items()):
                    _w(
                        f"{ip:<18} {dev.mac:<20} {dev.status:<14} {dev.packet_count:>7}\n"
                    )

                _w(f"\n\nALERTS DETECTED  ({len(alerts)})\n")
                _w("-" * 65 + "\n")
                if not alerts:
                    _w("  No alerts recorded during this session.\n")
                for a in alerts:
                    _w(f"  [{a.timestamp.strftime('%H:%M:%S')}]  IP: {a.ip}\n")
                    _w(f"    Legitimate MAC : {a.old_mac}\n")
                    _w(f"    Spoofed MAC    : {a.new_mac}\n")
                    _w(f"    Time difference: {a.time_diff}\n")
                    _w(f"    Interface      : {a.interface}\n\n")

                _w("=" * 65 + "\n")
                _w("  END OF REPORT\n")
                _w("=" * 65 + "\n")

            self._logger.info(f"TXT export written → {filepath}")
            return True

        except OSError as exc:
            self._logger.error(f"TXT export failed: {exc}")
            return False

    def export_to_csv(self, filepath: str, hosts: dict, alerts: list) -> bool:
        """
        Write a structured CSV export to *filepath*.
        Returns True on success, False on error.
        """
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)

                w.writerow(["=== DEVICES ==="])
                w.writerow([
                    "IP Address", "MAC Address",
                    "First Seen", "Last Seen",
                    "Packet Count", "Status",
                ])
                for ip, dev in sorted(hosts.items()):
                    w.writerow([
                        ip,
                        dev.mac,
                        dev.first_seen.strftime("%H:%M:%S"),
                        dev.last_seen.strftime("%H:%M:%S"),
                        dev.packet_count,
                        dev.status,
                    ])

                w.writerow([])

                w.writerow(["=== ALERTS ==="])
                w.writerow([
                    "Timestamp", "IP Address",
                    "Old MAC", "New MAC",
                    "Time Diff", "Interface",
                ])
                for a in alerts:
                    w.writerow([
                        a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        a.ip,
                        a.old_mac,
                        a.new_mac,
                        a.time_diff,
                        a.interface,
                    ])

            self._logger.info(f"CSV export written → {filepath}")
            return True

        except OSError as exc:
            self._logger.error(f"CSV export failed: {exc}")
            return False
