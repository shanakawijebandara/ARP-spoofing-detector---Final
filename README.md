# ARP Spoofing Detection Tool

**PUSL3190 Computing Project**
**Author:** Angam Wijebandara | Plymouth ID: 10954873
**Degree:** BSc (Hons) Computer Networks
**Supervisor:** Mr. Chamara Dissanayake

---

## Overview

A real-time ARP Spoofing Detection Tool built with Python and Scapy. This tool monitors network traffic, detects ARP spoofing (Man-in-the-Middle) attacks, and alerts the user immediately through a professional dark-theme GUI.

---

## Features

- Real-time ARP packet sniffing using Scapy
- 3-pass network scanner for reliable device discovery
- Professional Grafana-dark themed GUI (Tkinter)
- Instant alert popup on attack detection
- IP Whitelist support
- Cooldown system to prevent alert flooding
- Gateway attack critical warning
- File logging (TXT + CSV export)
- Live dashboard with packet activity chart
- Attack simulator script for lab demonstration

---

## Project Structure

```
arp-spoofing-detector/
├── main.py          # Entry point
├── detector.py      # Core detection engine
├── gui.py           # Professional GUI
├── logger.py        # File logging & export
├── arp_attack.py    # Attack simulator (lab use only)
├── requirements.txt # Dependencies
└── logs/            # Auto-generated log files
```

---

## Requirements

- Python 3.9+
- Scapy
- Npcap (Windows) — https://npcap.com

```bash
pip install -r requirements.txt
```

---

## Usage

> **Must run as Administrator (Windows) or sudo (Linux/macOS)**

```bash
python main.py
```

### Steps:
1. Select your network interface
2. Click **Scan Network** to discover devices
3. Click **Start Monitoring** to begin detection
4. If an ARP spoofing attack is detected, an alert will appear immediately

---

## Attack Simulator (Lab Demo Only)

```bash
python arp_attack.py
```

Use only on networks you own. Sends real ARP spoofing packets to test the detector.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Core language |
| Scapy | Packet crafting & sniffing |
| Tkinter | GUI framework |
| Threading | Concurrent execution |
| Queue | Thread-safe communication |
| Logging | File-based event logging |
| CSV | Structured data export |
| Npcap | Windows raw socket access |

---

## License

For educational purposes only — PUSL3190 Computing Project, University of Plymouth.
