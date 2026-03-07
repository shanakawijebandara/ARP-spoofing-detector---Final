
"""Core detection engine.  Responsibilities:
  • Discover network devices via active ARP scan
  • Sniff live ARP traffic in a background thread
  • Detect IP→MAC mapping changes (spoofing)
  • Rate-limit alerts and honour a user whitelist
  • Post all events to a thread-safe Queue consumed by the GUI
"""

import threading
import time
import socket
import subprocess
import platform
import queue
from datetime import datetime

try:
    from scapy.all import (
        sniff, ARP, Ether, srp, conf as scapy_conf, get_if_list
    )
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class DeviceInfo:
    """Represents one network device entry in the ARP table."""

    def __init__(self, ip: str, mac: str, interface: str = ""):
        self.ip           = ip
        self.mac          = mac.lower()
        self.first_seen   = datetime.now()
        self.last_seen    = datetime.now()
        self.packet_count = 1
        self.status       = "Normal"
        self.interface    = interface

    def touch(self, mac: str) -> None:
        self.last_seen     = datetime.now()
        self.packet_count += 1
        self.mac           = mac.lower()

    def to_row(self) -> tuple:
        return (
            self.ip,
            self.mac,
            self.first_seen.strftime("%H:%M:%S"),
            self.last_seen.strftime("%H:%M:%S"),
            self.packet_count,
            self.status,
        )


class AlertInfo:
    """Represents one detected ARP-spoofing event."""

    def __init__(self, ip: str, old_mac: str, new_mac: str, interface: str = ""):
        self.timestamp  = datetime.now()
        self.ip         = ip
        self.old_mac    = old_mac.lower()
        self.new_mac    = new_mac.lower()
        self.interface  = interface
        self.time_diff  = "–"

    def to_row(self) -> tuple:
        return (
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.ip,
            self.old_mac,
            self.new_mac,
            self.time_diff,
        )


class ARPDetector:
    """
    Main detection engine.

    Thread model
    ─────────────
    • GUI runs on the main (Tk) thread.
    • Scan runs in _scan_thread  (daemon).
    • Sniffer runs in _sniff_thread (daemon).
    • Both worker threads post events via self.event_queue.
    • The GUI polls event_queue with root.after(100, …).
    """

    COOLDOWN_SECS = 10

    def __init__(self, event_queue: queue.Queue = None):
        self.known_hosts: dict[str, DeviceInfo] = {}
        self.alerts:      list[AlertInfo]        = []
        self.whitelist:   set[str]               = set()
        self._cooldown:   dict[str, float]       = {}

        self.event_queue = event_queue if event_queue is not None else queue.Queue(maxsize=1000)

        self._stop_flag     = threading.Event()
        self._sniff_thread  = None
        self._scan_thread   = None

        self.interface            = None
        self.gateway_ip           = None
        self.gateway_mac          = None
        self.packets_processed    = 0
        self.monitoring_start_ts  = None
        self.is_monitoring        = False
        self.is_scanning          = False

    def get_interfaces(self) -> list[tuple[str, str]]:
        """
        Return [(display_name, scapy_iface_id), …]
        Filters out loopback / Bluetooth / virtual adapters.
        """
        if not SCAPY_AVAILABLE:
            return []

        SKIP = (
            "loopback", "npcap loopback",
            "bluetooth",
            "vmware", "virtualbox", "vethernet",
            "pseudo", "tunnel",
            "wan miniport",
            "wi-fi direct", "microsoft wi-fi direct",
            "software loopback",
        )

        PREFER = ("wi-fi", "wireless", "ethernet", "realtek", "intel",
                  "mediatek", "broadcom", "qualcomm", "killer", "atheros")

        result = []
        try:
            for iface_id, iface_obj in scapy_conf.ifaces.items():
                desc = (
                    getattr(iface_obj, "description", None)
                    or getattr(iface_obj, "name", None)
                    or str(iface_id)
                )
                desc_l = desc.lower()
                if any(kw in desc_l for kw in SKIP):
                    continue
                score = 0 if any(kw in desc_l for kw in PREFER) else 1
                result.append((score, desc, str(iface_id)))
        except Exception:
            pass

        result.sort(key=lambda x: (x[0], x[1]))
        result = [(desc, sid) for _, desc, sid in result]

        if not result:
            try:
                default = str(scapy_conf.iface)
                result = [(default, default)]
            except Exception:
                pass

        return result

    def get_gateway_ip(self) -> str:
        """Auto-detect default gateway IP address."""
        try:
            if platform.system() == "Windows":
                out = subprocess.run(
                    ["ipconfig"], capture_output=True, text=True, timeout=5
                ).stdout
                for line in out.splitlines():
                    if "Default Gateway" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            ip = parts[-1].strip()
                            if ip and self._valid_ip(ip):
                                return ip
            else:
                out = subprocess.run(
                    ["ip", "route", "show", "default"],
                    capture_output=True, text=True, timeout=5
                ).stdout
                tokens = out.split()
                if "via" in tokens:
                    return tokens[tokens.index("via") + 1]
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
        except Exception:
            return "192.168.1.1"

    def get_subnet(self, gateway: str = None) -> str:
        """Derive /24 subnet string from gateway IP."""
        gw     = gateway or self.gateway_ip or self.get_gateway_ip()
        parts  = gw.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

    @staticmethod
    def _valid_ip(ip: str) -> bool:
        try:
            parts = ip.split(".")
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except Exception:
            return False

    def scan_network(self, interface: str) -> list[DeviceInfo]:
        """
        Send ARP requests to every host in the /24 subnet and populate
        known_hosts with all responding devices.

        Three-pass strategy
        ───────────────────
        Pass 1 – Broadcast ARP sweep of the full /24 subnet.
                 Longer timeout (5 s) and 2 retries for slow WiFi / hotspot nets.
        Pass 2 – Targeted ARP directly to the gateway (always, not just on 0 results).
                 Many routers ignore /24 broadcasts but respond to direct requests.
        Pass 3 – Targeted sweep of common host suffixes (.1 .2 .3 .4 .5 .10
                 .100 .150 .200 .254) when fewer than 3 devices were found.
                 Catches devices that block broadcast ARP (e.g. iPhones on hotspot).

        Each device is posted as "new_device" in real-time so the GUI table
        populates progressively rather than waiting for the full scan to finish.

        Runs synchronously – call scan_in_thread() for non-blocking use.
        """
        if not SCAPY_AVAILABLE:
            self._post("error", "Scapy is not installed.  Run: pip install scapy")
            return []

        self.is_scanning = True
        self.interface   = interface
        self._post("log", "Network scan started…")

        devices   = []
        found_ips = set()

        def _register(ip: str, mac: str, label: str = "") -> None:
            """Add/update a device in known_hosts and notify the GUI."""
            if ip in found_ips:
                return
            found_ips.add(ip)
            dev = DeviceInfo(ip, mac, interface)
            if ip == self.gateway_ip:
                dev.status       = "Gateway"
                self.gateway_mac = mac
            self.known_hosts[ip] = dev
            devices.append(dev)
            self._post("new_device", dev)
            suffix = f"  [{label}]" if label else ""
            self._post("log", f"Found device  │  IP={ip}  MAC={mac}{suffix}")

        try:
            self.gateway_ip = self.get_gateway_ip()
            subnet          = self.get_subnet(self.gateway_ip)
            self._post("log", f"Gateway: {self.gateway_ip}  |  Subnet: {subnet}")

            try:
                pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
                answered, _ = srp(pkt, iface=interface,
                                   timeout=5, verbose=False, retry=2)
                for _, resp in answered:
                    _register(resp.psrc, resp.hwsrc.lower())
            except Exception as exc:
                self._post("log", f"Broadcast sweep error: {exc}")

            if self.gateway_ip and self.gateway_ip not in found_ips:
                try:
                    gw_pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                        pdst=self.gateway_ip)
                    gw_ans, _ = srp(gw_pkt, iface=interface,
                                    timeout=3, verbose=False)
                    for _, resp in gw_ans:
                        _register(resp.psrc, resp.hwsrc.lower(), "gateway probe")
                except Exception:
                    pass

            if len(devices) < 3:
                prefix  = ".".join(self.gateway_ip.split(".")[:3])
                offsets = [1, 2, 3, 4, 5, 6, 10, 20, 50,
                           100, 150, 200, 210, 220, 254]
                targets = [f"{prefix}.{i}" for i in offsets
                           if f"{prefix}.{i}" not in found_ips]
                if targets:
                    try:
                        t_pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                            pdst=targets)
                        t_ans, _ = srp(t_pkt, iface=interface,
                                       timeout=3, verbose=False)
                        for _, resp in t_ans:
                            _register(resp.psrc, resp.hwsrc.lower(),
                                      "targeted probe")
                    except Exception:
                        pass

            self._post("scan_complete", devices)
            self._post("log",
                f"Scan complete – {len(devices)} device(s) found"
                + (" (broadcast + targeted probes used)"
                   if len(devices) > 0 and len(found_ips) > 0
                      and len(devices) < 3 else ""))

        except Exception as exc:
            self._post("error", f"Scan error: {exc}")
        finally:
            self.is_scanning = False

        return devices

    def scan_in_thread(self, interface: str) -> threading.Thread:
        """Launch scan_network in a background daemon thread."""
        t = threading.Thread(
            target=self.scan_network,
            args=(interface,),
            daemon=True,
            name="ARPScanThread",
        )
        t.start()
        self._scan_thread = t
        return t

    def start_monitoring(self, interface: str) -> None:
        """Start background ARP sniffer thread."""
        if self.is_monitoring:
            return

        self.interface           = interface
        self.is_monitoring       = True
        self.monitoring_start_ts = time.time()
        self.packets_processed   = 0
        self._stop_flag.clear()

        self._sniff_thread = threading.Thread(
            target=self._sniff_loop,
            args=(interface,),
            daemon=True,
            name="ARPSniffThread",
        )
        self._sniff_thread.start()
        self._post("monitor_start", f"Monitoring started on: {interface}")
        self._post("log",           f"Monitoring started – interface: {interface}")

    def stop_monitoring(self) -> None:
        """Signal the sniffer thread to stop."""
        self._stop_flag.set()
        self.is_monitoring = False
        self._post("monitor_stop", "Monitoring stopped")
        self._post("log",          "Monitoring stopped by user")

    def _sniff_loop(self, interface: str) -> None:
        """Blocking Scapy sniff – runs inside the daemon thread."""
        try:
            sniff(
                iface=interface,
                filter="arp",
                prn=self._process_packet,
                store=False,
                stop_filter=lambda _p: self._stop_flag.is_set(),
            )
        except Exception as exc:
            self._post("error", f"Sniffer error: {exc}")
            self.is_monitoring = False

    def _process_packet(self, pkt) -> None:
        """
        Called by Scapy for every captured ARP packet.

        Detection logic
        ───────────────
        1. Extract src_ip / src_mac from ARP layer.
        2. Skip invalid / broadcast addresses.
        3. If IP is unknown → learn it (add to known_hosts).
        4. If IP is known  → compare stored MAC vs observed MAC.
           a. Match   → update timestamps & packet count (normal).
           b. Mismatch→ check whitelist & cooldown → raise Alert.
        5. Gateway attacks get an extra critical event posted.
        6. Post stats_update after every packet.
        """
        if not pkt.haslayer(ARP):
            return

        arp     = pkt[ARP]
        src_ip  = arp.psrc
        src_mac = arp.hwsrc.lower()

        if not src_ip or src_ip == "0.0.0.0":
            return
        if src_mac in ("ff:ff:ff:ff:ff:ff", "00:00:00:00:00:00"):
            return
        if src_mac.startswith("01:"):
            return

        self.packets_processed += 1

        if src_ip in self.known_hosts:
            device = self.known_hosts[src_ip]

            if device.mac == src_mac:
                device.touch(src_mac)
                self._post("device_update", device)

            else:
                if src_ip in self.whitelist:
                    device.touch(src_mac)
                    self._post("device_update", device)
                    return

                now        = time.time()
                last_alert = self._cooldown.get(src_ip, 0.0)
                if now - last_alert < self.COOLDOWN_SECS:
                    device.touch(src_mac)
                    return

                self._cooldown[src_ip] = now
                alert = AlertInfo(src_ip, device.mac, src_mac, self.interface or "")

                elapsed        = (alert.timestamp - device.first_seen).total_seconds()
                alert.time_diff = f"{elapsed:.1f}s"

                device.status = "⚠ ATTACK"
                device.touch(src_mac)

                self.alerts.append(alert)

                self._post("alert", alert)
                self._post("log",
                    f"ALERT │ ARP spoofing detected! "
                    f"IP={src_ip}  OLD={alert.old_mac}  NEW={src_mac}"
                )

                if src_ip == self.gateway_ip:
                    self._post("gateway_attack", alert)

        else:
            dev = DeviceInfo(src_ip, src_mac, self.interface or "")
            if src_ip == self.gateway_ip:
                dev.status       = "Gateway"
                self.gateway_mac = src_mac

            self.known_hosts[src_ip] = dev
            self._post("new_device", dev)
            self._post("log", f"New device  │  IP={src_ip}  MAC={src_mac}")

        self._post("stats_update", {
            "packets": self.packets_processed,
            "devices": len(self.known_hosts),
            "alerts":  len(self.alerts),
            "uptime":  self._uptime_str(),
        })

    def add_to_whitelist(self, ip: str) -> None:
        self.whitelist.add(ip)
        if ip in self.known_hosts:
            self.known_hosts[ip].status = "Whitelisted"
            self._post("device_update", self.known_hosts[ip])
        self._post("log", f"Whitelisted: {ip}")

    def remove_from_whitelist(self, ip: str) -> None:
        self.whitelist.discard(ip)
        if ip in self.known_hosts:
            dev        = self.known_hosts[ip]
            dev.status = "Gateway" if ip == self.gateway_ip else "Normal"
            self._post("device_update", dev)
        self._post("log", f"Removed from whitelist: {ip}")

    def simulate_attack(self, target_ip: str = None) -> None:
        """
        Inject a fake MAC-change event into the detection pipeline.
        Safe: no packets are sent onto the wire.
        """
        if not self.known_hosts:
            self._post("error", "No devices known.  Run a network scan first.")
            return

        if target_ip and target_ip in self.known_hosts:
            ip = target_ip
        elif self.gateway_ip and self.gateway_ip in self.known_hosts:
            ip = self.gateway_ip
        else:
            ip = next(iter(self.known_hosts))

        real_mac = self.known_hosts[ip].mac
        fake_mac = "de:ad:be:ef:00:01"

        self._cooldown.pop(ip, None)

        alert           = AlertInfo(ip, real_mac, fake_mac, self.interface or "")
        alert.time_diff = "simulated"

        self.known_hosts[ip].status = "⚠ ATTACK"
        self.known_hosts[ip].mac    = fake_mac
        self.alerts.append(alert)

        self._post("alert",         alert)
        self._post("device_update", self.known_hosts[ip])
        self._post("log",
            f"[SIMULATION] Spoof injected │ IP={ip}  "
            f"REAL={real_mac}  FAKE={fake_mac}"
        )
        self._post("stats_update", {
            "packets": self.packets_processed,
            "devices": len(self.known_hosts),
            "alerts":  len(self.alerts),
            "uptime":  self._uptime_str(),
        })

    def _uptime_str(self) -> str:
        if not self.monitoring_start_ts:
            return "00:00:00"
        e = int(time.time() - self.monitoring_start_ts)
        return f"{e // 3600:02d}:{(e % 3600) // 60:02d}:{e % 60:02d}"

    def _post(self, event_type: str, data) -> None:
        """Thread-safe: post an event to the GUI queue."""
        try:
            self.event_queue.put_nowait({"type": event_type, "data": data})
        except queue.Full:
            pass

    def reset(self) -> None:
        """Clear all session data."""
        self.known_hosts.clear()
        self.alerts.clear()
        self._cooldown.clear()
        self.packets_processed   = 0
        self.monitoring_start_ts = None
