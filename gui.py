# =============================================================================
#  gui.py  –  Professional GUI  (v4.0  –  Grafana-Dark style)
#  Project : ARP Spoofing Detection Tool
#  Author  : Angam Wijebandara  |  Plymouth ID: 10954873
#  Module  : PUSL3190 Computing Project
# =============================================================================

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

try:
    import winsound
    _WINSOUND = True
except ImportError:
    _WINSOUND = False


# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

# ── Backgrounds ──────────────────────────────────────────────────────────────
BG0 = "#111217"   # window base
BG1 = "#181b1f"   # panels / toolbar
BG2 = "#1f2228"   # cards / inputs
BG3 = "#272b33"   # hover
BG4 = "#2e3340"   # strong elevated

# ── Borders ───────────────────────────────────────────────────────────────────
BD0 = "#1e2229"   # hairline
BD1 = "#2a2f3a"   # normal
BD2 = "#3a4154"   # emphasized

# ── Brand / Semantic ──────────────────────────────────────────────────────────
BLUE   = "#4d9cf6"   # primary action
TEAL   = "#00c9b0"   # accent / info
GREEN  = "#5fbe7a"   # success / normal / safe
RED    = "#e05460"   # danger / alert / attack
AMBER  = "#e89d3a"   # warning / simulation
PURPLE = "#a07fe0"   # gateway / special
PINK   = "#d970a8"   # sim highlight

# ── Text ──────────────────────────────────────────────────────────────────────
TX0 = "#cdd2d9"   # primary
TX1 = "#737c8a"   # secondary / dimmed
TX2 = "#3d4554"   # muted / placeholder

# ── Header gradient ───────────────────────────────────────────────────────────
HDR_TOP = "#0d1117"
HDR_BOT = "#111c2d"
HDR_LINE = BLUE      # 2px accent under header

# ── Fonts ─────────────────────────────────────────────────────────────────────
F_TITLE  = ("Segoe UI",  15, "bold")
F_SUB    = ("Segoe UI",   8)
F_LABEL  = ("Segoe UI",   9)
F_BOLD   = ("Segoe UI",   9, "bold")
F_MONO   = ("Consolas",   9)
F_MONO_S = ("Consolas",   8)
F_NUM_LG = ("Segoe UI",  26, "bold")
F_NUM_SM = ("Segoe UI",  11, "bold")
F_ICON   = ("Segoe UI Emoji", 14)
F_ICON_S = ("Segoe UI Emoji", 10)

# ── Treeview row tags ─────────────────────────────────────────────────────────
ROW_TAGS = {
    "normal":     {"foreground": GREEN,  "background": BG1},
    "attack":     {"foreground": RED,    "background": "#260e10"},
    "gateway":    {"foreground": PURPLE, "background": "#18143a"},
    "whitelist":  {"foreground": TEAL,   "background": "#0e1e28"},
    "alert_live": {"foreground": RED,    "background": "#260e10"},
    "alert_sim":  {"foreground": AMBER,  "background": "#241a08"},
}


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY
# ══════════════════════════════════════════════════════════════════════════════

def lerp_color(a: str, b: str, t: float) -> str:
    """Linearly interpolate between two #rrggbb colours."""
    ra, ga, ba = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    rb, gb, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
    )

def _sep_h(parent, color=BD1, pady=0):
    """1-px horizontal separator."""
    f = tk.Frame(parent, bg=color, height=1)
    f.pack(fill=tk.X, pady=pady)
    return f

def _sep_v(parent, color=BD1):
    """1-px vertical separator packed into a row."""
    f = tk.Frame(parent, bg=color, width=1)
    f.pack(side=tk.LEFT, fill=tk.Y, padx=8)
    return f


# ══════════════════════════════════════════════════════════════════════════════
#  REUSABLE WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class Btn(tk.Frame):
    """
    Professional flat button.
    border_color drives the 1-px outline and the hover glow.
    """
    def __init__(self, parent, text, command,
                 fg=TX0, bg=BG2, border=BD1,
                 active_bg=BG3, padx=14, pady=5,
                 font=F_BOLD, state="normal", width=None, **kw):
        super().__init__(parent, bg=border, **kw)
        self._bg     = bg
        self._hover  = active_bg
        self._border = border
        self._cmd    = command
        self._on     = state == "normal"

        self._inner = tk.Frame(self, bg=bg if self._on else BG1,
                                padx=padx, pady=pady)
        self._inner.pack(padx=1, pady=1)

        lkw = dict(bg=bg if self._on else BG1,
                   fg=fg if self._on else TX2,
                   font=font, cursor="hand2" if self._on else "arrow")
        if width:
            lkw["width"] = width
        self._lbl = tk.Label(self._inner, text=text, **lkw)
        self._lbl.pack()

        if self._on:
            self._bind_hover()

    def _bind_hover(self):
        for w in (self, self._inner, self._lbl):
            w.bind("<Enter>",   lambda _e: self._set_bg(self._hover))
            w.bind("<Leave>",   lambda _e: self._set_bg(self._bg))
            w.bind("<Button-1>",lambda _e: self._set_bg(self._border))
            w.bind("<ButtonRelease-1>", lambda _e: (self._set_bg(self._bg), self._cmd()))

    def _set_bg(self, c):
        self._inner.config(bg=c)
        self._lbl.config(bg=c)

    def set_state(self, state):
        self._on = state == "normal"
        bg  = self._bg  if self._on else BG1
        fg  = TX0        if self._on else TX2
        cur = "hand2"    if self._on else "arrow"
        self._inner.config(bg=bg)
        self._lbl.config(bg=bg, fg=fg, cursor=cur)
        for w in (self, self._inner, self._lbl):
            for ev in ("<Enter>","<Leave>","<Button-1>","<ButtonRelease-1>"):
                w.unbind(ev)
        if self._on:
            self._bind_hover()

    def set_text(self, t):
        self._lbl.config(text=t)


class StatCard(tk.Frame):
    """
    Compact horizontal stat card.
    ┌──────────────────────────────────┐
    │ ▌  ICON   NUMBER                 │
    │ ▌         label                  │
    └──────────────────────────────────┘
    Left stripe changes colour per card.
    """
    def __init__(self, parent, icon, label, value="0", color=BLUE, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self._color = color

        # Left accent stripe
        tk.Frame(self, bg=color, width=3).pack(side=tk.LEFT, fill=tk.Y)

        body = tk.Frame(self, bg=BG2, padx=14, pady=10)
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top_row = tk.Frame(body, bg=BG2)
        top_row.pack(anchor="w")

        tk.Label(top_row, text=icon, font=F_ICON_S,
                 bg=BG2, fg=color).pack(side=tk.LEFT, padx=(0, 8))

        right = tk.Frame(top_row, bg=BG2)
        right.pack(side=tk.LEFT)

        self._num = tk.Label(right, text=value, font=F_NUM_LG,
                              bg=BG2, fg=TX0)
        self._num.pack(anchor="w")

        tk.Label(right, text=label, font=F_SUB,
                 bg=BG2, fg=TX1).pack(anchor="w")

    def update(self, v):
        self._num.config(text=str(v))


class TabBar(tk.Frame):
    """
    Flat tab bar with blue underline indicator and count badge.
    Active tab → white text + 2 px BLUE bottom border.
    Inactive   → muted text, highlights on hover.
    """
    def __init__(self, parent, on_select, **kw):
        super().__init__(parent, bg=BG1, **kw)
        self._cb    = on_select
        self._tabs  = {}   # name → dict
        self._cur   = None

    def add(self, name, text):
        col = tk.Frame(self, bg=BG1)
        col.pack(side=tk.LEFT)

        inner = tk.Frame(col, bg=BG1, padx=20, pady=10, cursor="hand2")
        inner.pack()

        lbl = tk.Label(inner, text=text, font=F_BOLD, bg=BG1, fg=TX1)
        lbl.pack()

        # 2-px underline (hidden until active)
        bar = tk.Frame(col, bg=BLUE, height=2)

        for w in (col, inner, lbl):
            w.bind("<Button-1>", lambda _e, n=name: self.select(n))
            w.bind("<Enter>",  lambda _e, l=lbl: l.config(fg=TX0)
                   if self._cur != name else None)
            w.bind("<Leave>",  lambda _e, l=lbl, n=name:
                   l.config(fg=TX0 if self._cur == n else TX1))

        self._tabs[name] = {"lbl": lbl, "bar": bar}

    def select(self, name):
        if self._cur and self._cur in self._tabs:
            t = self._tabs[self._cur]
            t["lbl"].config(fg=TX1)
            t["bar"].pack_forget()
        self._cur = name
        t = self._tabs[name]
        t["lbl"].config(fg=TX0)
        t["bar"].pack(fill=tk.X)
        self._cb(name)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN GUI
# ══════════════════════════════════════════════════════════════════════════════

class ARPDetectorGUI:
    """Professional dark-theme GUI for ARP Spoofing Detector."""

    def __init__(self, root: tk.Tk, detector, logger):
        self.root     = root
        self.detector = detector
        self.logger   = logger
        self.eq       = detector.event_queue

        self._iface_var   = tk.StringVar()
        self._sound_var   = tk.BooleanVar(value=True)
        self._iface_map   = {}
        self._dot_on      = True
        self._frames      = {}   # tab name → Frame

        self._setup_window()
        self._setup_styles()
        self._build()
        self._load_ifaces()
        self._start_timers()

    # ─────────────────────────────────────────────────────────────────────────
    #  Window & TTK styles
    # ─────────────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("ARP Spoofing Detector  ·  PUSL3190")
        self.root.geometry("1240x800")
        self.root.minsize(1000, 660)
        self.root.configure(bg=BG0)
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"1240x800+{(sw-1240)//2}+{(sh-800)//2}")

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".",
            background=BG1, foreground=TX0,
            fieldbackground=BG2, troughcolor=BG1,
            bordercolor=BD1, darkcolor=BG1, lightcolor=BD0,
            selectbackground=BLUE, selectforeground="#ffffff",
            relief="flat", font=F_LABEL)
        # Treeview
        s.configure("T.Treeview",
            background=BG1, foreground=TX0,
            fieldbackground=BG1, rowheight=32,
            borderwidth=0, font=F_MONO)
        s.configure("T.Treeview.Heading",
            background=BG2, foreground=TX1,
            font=F_BOLD, relief="flat", borderwidth=0)
        s.map("T.Treeview",
            background=[("selected", BG4)],
            foreground=[("selected", TX0)])
        # Scrollbar
        for o in ("Vertical", "Horizontal"):
            s.configure(f"{o}.TScrollbar",
                background=BG2, arrowcolor=TX1,
                troughcolor=BG0, relief="flat", borderwidth=0)
        # Combobox
        s.configure("Pro.TCombobox",
            background=BG2, foreground=TX0,
            fieldbackground=BG2, selectbackground=BG3,
            arrowcolor=TX1, padding=(8, 6))
        s.map("Pro.TCombobox",
            fieldbackground=[("readonly", BG2)],
            selectbackground=[("readonly", BG3)])

    # ─────────────────────────────────────────────────────────────────────────
    #  Build top-level structure
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        # Status bar must be packed BEFORE main so it anchors at bottom
        self._build_statusbar()
        self._build_header()
        self._build_toolbar()
        _sep_h(self.root, BD1)
        self._build_stats()
        _sep_h(self.root, BD0)
        self._build_tabs()

    # ═════════════════════════════════════════════════════════════════════════
    #  STATUS BAR  (bottom, packed first so it anchors correctly)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG0, height=24)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)

        _sep_h(bar, BD0)

        row = tk.Frame(bar, bg=BG0)
        row.pack(fill=tk.X, padx=14)

        def item(text, fg=TX2):
            l = tk.Label(row, text=text, font=("Segoe UI", 7),
                         bg=BG0, fg=fg)
            l.pack(side=tk.LEFT, padx=(0, 16))
            return l

        self._sb_iface   = item("Interface: —")
        item("·", TX2)
        self._sb_packets = item("Packets: 0")
        item("·", TX2)
        self._sb_uptime  = item("Uptime: 00:00:00")

        tk.Label(bar,
                 text="Angam Wijebandara  ·  Plymouth 10954873  ·  BSc (Hons) Computer Networks",
                 font=("Segoe UI", 7), bg=BG0, fg=TX2
                 ).pack(side=tk.RIGHT, padx=14)

    # ═════════════════════════════════════════════════════════════════════════
    #  HEADER  (gradient canvas)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_header(self):
        self._hdr = tk.Canvas(self.root, height=64,
                               bd=0, highlightthickness=0)
        self._hdr.pack(fill=tk.X)
        self._hdr.bind("<Configure>", self._draw_header_bg)

        # ── Left: logo + title ────────────────────────────────────────────
        lf = tk.Frame(self._hdr, bg=HDR_TOP)
        self._hdr.create_window(18, 32, window=lf, anchor="w", tags="left")

        tk.Label(lf, text="🛡", font=("Segoe UI Emoji", 26),
                 bg=HDR_TOP, fg=BLUE).pack(side=tk.LEFT, padx=(0, 12))

        tf = tk.Frame(lf, bg=HDR_TOP)
        tf.pack(side=tk.LEFT)
        tk.Label(tf, text="ARP  SPOOFING  DETECTOR",
                 font=F_TITLE, bg=HDR_TOP, fg=TX0).pack(anchor="w")
        tk.Label(tf, text="Real-time Network Security Monitor  ·  PUSL3190",
                 font=F_SUB, bg=HDR_TOP, fg=TX1).pack(anchor="w")

        # ── Right: status badge ───────────────────────────────────────────
        rf = tk.Frame(self._hdr, bg=HDR_TOP)
        self._hdr.create_window(-18, 32, window=rf,
                                 anchor="e", tags="right")

        badge = tk.Frame(rf, bg=BG2, padx=14, pady=6)
        badge.pack(side=tk.RIGHT, padx=4)
        # thin border frame
        tk.Frame(rf, bg=BD1, padx=1, pady=1).pack(side=tk.RIGHT)

        self._dot = tk.Label(badge, text="●", font=("Segoe UI", 11),
                              bg=BG2, fg=RED)
        self._dot.pack(side=tk.LEFT, padx=(0, 7))

        self._status_lbl = tk.Label(badge, text="STOPPED",
                                     font=F_BOLD, bg=BG2, fg=RED)
        self._status_lbl.pack(side=tk.LEFT)

        # Blue accent line
        tk.Frame(self.root, bg=HDR_LINE, height=2).pack(fill=tk.X)

    def _draw_header_bg(self, _e=None):
        cv = self._hdr
        w, h = cv.winfo_width(), cv.winfo_height()
        cv.delete("bg")
        for i in range(h):
            c = lerp_color(HDR_TOP, HDR_BOT, i / max(h-1, 1))
            cv.create_rectangle(0, i, w, i+1, fill=c, outline="", tags="bg")
        cv.lower("bg")
        cv.coords("right", w - 18, h // 2)

    # ═════════════════════════════════════════════════════════════════════════
    #  TOOLBAR
    # ═════════════════════════════════════════════════════════════════════════

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=BG1, height=54)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        row = tk.Frame(bar, bg=BG1)
        row.pack(side=tk.LEFT, fill=tk.Y, padx=16)

        # ── Interface selector ────────────────────────────────────────────
        igroup = tk.Frame(row, bg=BG1)
        igroup.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(igroup, text="INTERFACE", font=("Segoe UI", 7, "bold"),
                 bg=BG1, fg=TX2).pack(anchor="w", pady=(8, 2))

        cb_border = tk.Frame(igroup, bg=BD1, padx=1, pady=1)
        cb_border.pack(anchor="w")

        self._iface_combo = ttk.Combobox(
            cb_border, textvariable=self._iface_var,
            state="readonly", style="Pro.TCombobox",
            font=F_LABEL, width=32)
        self._iface_combo.pack()

        _sep_v(row)

        # ── Scan ─────────────────────────────────────────────────────────
        sg = self._vcenter(row)
        self._btn_scan = Btn(sg, "  🔍  Scan Network  ", self._on_scan,
                              fg=BLUE, bg=BG2, border=BLUE,
                              active_bg=BG3, padx=14, pady=6)
        self._btn_scan.pack(side=tk.LEFT)

        _sep_v(row)

        # ── Monitoring ────────────────────────────────────────────────────
        mg = self._vcenter(row)
        self._btn_start = Btn(mg, "  ▶  Start  ", self._on_start,
                               fg=GREEN, bg=BG2, border=GREEN,
                               active_bg="#1a2e1e", padx=14, pady=6)
        self._btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_stop = Btn(mg, "  ■  Stop  ", self._on_stop,
                              fg=TX2, bg=BG1, border=BD1,
                              active_bg="#2a1214", padx=14, pady=6,
                              state="disabled")
        self._btn_stop.pack(side=tk.LEFT)

        _sep_v(row)

        # ── Export ────────────────────────────────────────────────────────
        eg = self._vcenter(row)
        for label, cmd in (("  📄 TXT  ", self._on_export_txt),
                            ("  📊 CSV  ", self._on_export_csv)):
            Btn(eg, label, cmd,
                fg=TX0, bg=BG2, border=BD1,
                active_bg=BG3, padx=12, pady=6
                ).pack(side=tk.LEFT, padx=(0, 4))

        _sep_v(row)

        # ── Right side: sound + reset ────────────────────────────────────
        rg = self._vcenter(row)

        self._snd_frame = tk.Frame(rg, bg=BG2, padx=10, pady=6,
                                    cursor="hand2")
        self._snd_frame.pack(side=tk.LEFT, padx=(0, 4))
        self._snd_lbl = tk.Label(self._snd_frame, text="🔔",
                                  font=F_ICON_S, bg=BG2, fg=TX1,
                                  cursor="hand2")
        self._snd_lbl.pack()
        for w in (self._snd_frame, self._snd_lbl):
            w.bind("<Button-1>", self._toggle_sound)
            w.bind("<Enter>",  lambda e, f=self._snd_frame: f.config(bg=BG3))
            w.bind("<Leave>",  lambda e, f=self._snd_frame: f.config(bg=BG2))

        Btn(rg, "  ↺  Reset  ", self._on_reset,
            fg=TX1, bg=BG1, border=BD0,
            active_bg="#280c0e", padx=12, pady=6
            ).pack(side=tk.LEFT)

    @staticmethod
    def _vcenter(parent):
        """Frame that centers its children vertically."""
        f = tk.Frame(parent, bg=BG1)
        f.pack(side=tk.LEFT, fill=tk.Y)
        return f

    # ═════════════════════════════════════════════════════════════════════════
    #  STATS STRIP
    # ═════════════════════════════════════════════════════════════════════════

    def _build_stats(self):
        strip = tk.Frame(self.root, bg=BG0, pady=10)
        strip.pack(fill=tk.X, padx=14)

        self._sc_dev = StatCard(strip, "🖥", "Devices Found",   "0",        BLUE)
        self._sc_pkt = StatCard(strip, "📦", "Packets Captured","0",        TEAL)
        self._sc_alt = StatCard(strip, "🚨", "Alerts Raised",   "0",        RED)
        self._sc_upt = StatCard(strip, "⏱", "Uptime",          "00:00:00", GREEN)

        for card in (self._sc_dev, self._sc_pkt, self._sc_alt, self._sc_upt):
            card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    # ═════════════════════════════════════════════════════════════════════════
    #  TABS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tabs(self):
        wrap = tk.Frame(self.root, bg=BG0)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Tab bar
        self._tabs = TabBar(wrap, self._switch_tab)
        self._tabs.pack(fill=tk.X, side=tk.TOP)
        _sep_h(wrap, BD1)

        for name, txt in (("devices",   "  📡  Devices  "),
                           ("alerts",    "  🚨  Alerts  "),
                           ("dashboard", "  📊  Dashboard  "),
                           ("log",       "  📋  Log  ")):
            self._tabs.add(name, txt)

        # Content area
        self._content = tk.Frame(wrap, bg=BG0)
        self._content.pack(fill=tk.BOTH, expand=True)

        self._build_tab_devices()
        self._build_tab_alerts()
        self._build_tab_dashboard()
        self._build_tab_log()

        self._tabs.select("devices")

    def _switch_tab(self, name):
        for n, f in self._frames.items():
            if n == name:
                f.pack(fill=tk.BOTH, expand=True)
            else:
                f.pack_forget()

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 1 – DEVICES
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_devices(self):
        frame = tk.Frame(self._content, bg=BG0)
        self._frames["devices"] = frame

        # ── Sub-header ────────────────────────────────────────────────────
        hdr = self._tab_header(frame)

        tk.Label(hdr, text="Network Devices",
                 font=F_BOLD, bg=BG1, fg=TX0).pack(side=tk.LEFT, padx=16)

        self._dev_badge = tk.Label(hdr, text="0 devices",
                                    font=("Segoe UI", 8),
                                    bg=BG3, fg=TX1, padx=8, pady=2)
        self._dev_badge.pack(side=tk.LEFT)

        tk.Label(hdr, text="Right-click a row for options",
                 font=("Segoe UI", 7, "italic"),
                 bg=BG1, fg=TX2).pack(side=tk.RIGHT, padx=16)

        # ── Tree ──────────────────────────────────────────────────────────
        cols   = ("No", "IP Address", "MAC Address",
                  "First Seen", "Last Seen", "Packets", "Status")
        widths = (42, 130, 168, 88, 88, 68, 110)
        self._dev_tree = self._make_tree(frame, cols, widths)

        # ── Context menu ──────────────────────────────────────────────────
        self._ctx = tk.Menu(self.root, tearoff=0,
                             bg=BG2, fg=TX0,
                             activebackground=BLUE,
                             activeforeground="#ffffff",
                             font=F_LABEL, bd=0, relief="flat")
        for label, cmd in (
            ("✅  Whitelist this IP",         self._ctx_whitelist),
            ("❌  Remove from Whitelist",      self._ctx_rm_whitelist),
            (None, None),
            ("📋  Copy IP Address",            self._ctx_copy_ip),
            ("📋  Copy MAC Address",           self._ctx_copy_mac),
        ):
            if label is None:
                self._ctx.add_separator()
            else:
                self._ctx.add_command(label=label, command=cmd)

        self._dev_tree.bind("<Button-3>", self._show_ctx)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 2 – ALERTS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_alerts(self):
        frame = tk.Frame(self._content, bg=BG0)
        self._frames["alerts"] = frame

        hdr = self._tab_header(frame)
        tk.Label(hdr, text="ARP Spoofing Alerts",
                 font=F_BOLD, bg=BG1, fg=RED).pack(side=tk.LEFT, padx=16)

        self._alert_badge = tk.Label(hdr, text="0 alerts",
                                      font=("Segoe UI", 8),
                                      bg="#260e10", fg=RED, padx=8, pady=2)
        self._alert_badge.pack(side=tk.LEFT)

        Btn(hdr, " Clear All ", self._clear_alerts,
            fg=TX1, bg=BG1, border=BD0, active_bg=BG3,
            padx=10, pady=3
            ).pack(side=tk.RIGHT, padx=16)

        cols   = ("No", "Timestamp", "IP Address",
                  "Old MAC  (Legitimate)", "New MAC  (Spoofed)", "Elapsed")
        widths = (42, 162, 128, 175, 175, 88)
        self._alert_tree = self._make_tree(frame, cols, widths)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 3 – DASHBOARD
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_dashboard(self):
        frame = tk.Frame(self._content, bg=BG0)
        self._frames["dashboard"] = frame

        hdr = self._tab_header(frame)
        tk.Label(hdr, text="Live Activity Dashboard",
                 font=F_BOLD, bg=BG1, fg=TX0).pack(side=tk.LEFT, padx=16)

        # ── Two-column body ───────────────────────────────────────────────
        body = tk.Frame(frame, bg=BG0)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        # Left: chart panel
        lp = tk.Frame(body, bg=BG1)
        lp.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7))

        ch = tk.Frame(lp, bg=BG1, pady=10)
        ch.pack(fill=tk.X, padx=16)
        tk.Label(ch, text="ARP Packet Activity — Top 8 Hosts",
                 font=F_BOLD, bg=BG1, fg=TX0).pack(side=tk.LEFT)
        self._chart_info = tk.Label(ch, text="", font=F_SUB,
                                     bg=BG1, fg=TX1)
        self._chart_info.pack(side=tk.RIGHT)

        _sep_h(lp, BD0)

        self._chart = tk.Canvas(lp, bg=BG1,
                                 highlightthickness=0, height=320)
        self._chart.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)
        self._chart.bind("<Configure>", lambda _: self._draw_chart())

        # Right: recent-alerts panel
        rp = tk.Frame(body, bg=BG1, width=280)
        rp.pack(side=tk.LEFT, fill=tk.Y, padx=(7, 0))
        rp.pack_propagate(False)

        rh = tk.Frame(rp, bg=BG1, pady=10)
        rh.pack(fill=tk.X, padx=16)
        tk.Label(rh, text="Recent Alerts", font=F_BOLD,
                 bg=BG1, fg=RED).pack(side=tk.LEFT)

        _sep_h(rp, BD0)

        # Scrollable list
        lf = tk.Frame(rp, bg=BG1)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._da_canvas = tk.Canvas(lf, bg=BG1, highlightthickness=0)
        da_sb = ttk.Scrollbar(lf, orient="vertical",
                               command=self._da_canvas.yview)
        self._da_inner = tk.Frame(self._da_canvas, bg=BG1)
        self._da_inner.bind("<Configure>",
            lambda _e: self._da_canvas.configure(
                scrollregion=self._da_canvas.bbox("all")))
        self._da_canvas.create_window((0, 0), window=self._da_inner,
                                       anchor="nw")
        self._da_canvas.configure(yscrollcommand=da_sb.set)
        self._da_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        da_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._da_empty = tk.Label(
            self._da_inner,
            text="No alerts recorded.\nNetwork appears clean ✓",
            font=("Segoe UI", 9, "italic"),
            bg=BG1, fg=TX1, justify="center")
        self._da_empty.pack(pady=24)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 4 – LOG
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_log(self):
        frame = tk.Frame(self._content, bg=BG0)
        self._frames["log"] = frame

        hdr = self._tab_header(frame)
        tk.Label(hdr, text="System Event Log",
                 font=F_BOLD, bg=BG1, fg=TX0).pack(side=tk.LEFT, padx=16)

        for lbl, cmd, fg in (("Refresh", self._refresh_log, TEAL),
                              ("Clear",   self._clear_log,   TX1)):
            Btn(hdr, f"  {lbl}  ", cmd,
                fg=fg, bg=BG1, border=BD0, active_bg=BG2,
                padx=10, pady=3
                ).pack(side=tk.RIGHT, padx=(0, 8))

        lf = tk.Frame(frame, bg=BG0)
        lf.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 14))

        self._log = tk.Text(
            lf, bg=BG1, fg=TX0,
            font=F_MONO, insertbackground=BLUE,
            selectbackground=BG4,
            relief="flat", bd=0, wrap=tk.WORD,
            state="disabled", padx=14, pady=10)

        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=vsb.set)
        self._log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags
        self._log.tag_configure("ts",   foreground=TX2)
        self._log.tag_configure("err",  foreground=RED)
        self._log.tag_configure("warn", foreground=AMBER)
        self._log.tag_configure("ok",   foreground=GREEN)
        self._log.tag_configure("info", foreground=TX0)
        self._log.tag_configure("dim",  foreground=TX1)
        self._log.tag_configure("sim",  foreground=PINK)

    # ─────────────────────────────────────────────────────────────────────────
    #  Shared factory helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _tab_header(parent):
        """Sub-header strip at top of each tab content frame."""
        h = tk.Frame(parent, bg=BG1, height=40)
        h.pack(fill=tk.X)
        h.pack_propagate(False)
        return h

    def _make_tree(self, parent, cols, widths):
        """Build a T.Treeview with scrollbars and colour tags."""
        wrap = tk.Frame(parent, bg=BG0)
        wrap.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 12))

        tree = ttk.Treeview(wrap, style="T.Treeview",
                             columns=cols, show="headings",
                             selectmode="browse")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col, anchor="w")
            tree.column(col, width=w, minwidth=40, anchor="w")

        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        for tag, cfg in ROW_TAGS.items():
            tree.tag_configure(tag, **cfg)

        return tree

    # ─────────────────────────────────────────────────────────────────────────
    #  Interface loading
    # ─────────────────────────────────────────────────────────────────────────

    def _load_ifaces(self):
        ifaces = self.detector.get_interfaces()
        if not ifaces:
            self._iface_combo["values"] = ["(no interfaces found)"]
            self._iface_var.set("(no interfaces found)")
            return
        names = []
        for disp, sid in ifaces:
            self._iface_map[disp] = sid
            names.append(disp)
        self._iface_combo["values"] = names
        self._iface_var.set(names[0])

    def _get_iface(self):
        d = self._iface_var.get()
        return self._iface_map.get(d, d)

    # ─────────────────────────────────────────────────────────────────────────
    #  Button handlers
    # ─────────────────────────────────────────────────────────────────────────

    def _on_scan(self):
        iface = self._get_iface()
        if not iface or "no interface" in iface.lower():
            messagebox.showwarning("No Interface",
                                   "Please select a valid network interface.")
            return
        self._btn_scan.set_text("  🔍  Scanning…  ")
        self._btn_scan.set_state("disabled")
        self._log_append(f"Network scan started — {self._iface_var.get()}", "ok")
        self._sb_iface.config(text=f"Interface: {self._iface_var.get()}")
        self.detector.scan_in_thread(iface)

    def _on_start(self):
        iface = self._get_iface()
        if not iface or "no interface" in iface.lower():
            messagebox.showwarning("No Interface",
                                   "Please select a valid network interface.")
            return
        self.detector.start_monitoring(iface)
        self._btn_start.set_state("disabled")
        self._btn_stop.set_state("normal")
        self._dot.config(fg=GREEN)
        self._status_lbl.config(text="MONITORING", fg=GREEN)
        self._sb_iface.config(text=f"Interface: {self._iface_var.get()}")

    def _on_stop(self):
        self.detector.stop_monitoring()
        self._btn_start.set_state("normal")
        self._btn_stop.set_state("disabled")
        self._dot.config(fg=RED)
        self._status_lbl.config(text="STOPPED", fg=RED)
        self._dot_on = True

    def _on_export_txt(self):
        p = filedialog.asksaveasfilename(
            title="Export as TXT", defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            ok = self.logger.export_to_txt(
                p, self.detector.known_hosts, self.detector.alerts)
            (messagebox.showinfo if ok else messagebox.showerror)(
                "Export" + (" Complete" if ok else " Failed"),
                f"Saved to:\n{p}" if ok else "Could not write file.")

    def _on_export_csv(self):
        p = filedialog.asksaveasfilename(
            title="Export as CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if p:
            ok = self.logger.export_to_csv(
                p, self.detector.known_hosts, self.detector.alerts)
            (messagebox.showinfo if ok else messagebox.showerror)(
                "Export" + (" Complete" if ok else " Failed"),
                f"Saved to:\n{p}" if ok else "Could not write file.")

    def _on_reset(self):
        if messagebox.askyesno("Reset", "Clear all devices, alerts, and log?"):
            self.detector.reset()
            self._clear_log()
            self._clear_alerts()
            for i in self._dev_tree.get_children():
                self._dev_tree.delete(i)
            self._dev_badge.config(text="0 devices")
            self._update_stats(
                {"packets": 0, "devices": 0, "alerts": 0, "uptime": "00:00:00"})
            self._draw_chart()
            self._log_append("Session data cleared.", "warn")

    def _toggle_sound(self, _e=None):
        self._sound_var.set(not self._sound_var.get())
        self._snd_lbl.config(text="🔔" if self._sound_var.get() else "🔕")

    # ─────────────────────────────────────────────────────────────────────────
    #  Context menu (devices tab)
    # ─────────────────────────────────────────────────────────────────────────

    def _show_ctx(self, event):
        r = self._dev_tree.identify_row(event.y)
        if r:
            self._dev_tree.selection_set(r)
            self._ctx.post(event.x_root, event.y_root)

    def _sel_ip(self):
        s = self._dev_tree.selection()
        return str(self._dev_tree.item(s[0])["values"][1]) if s else None

    def _ctx_whitelist(self):
        ip = self._sel_ip()
        if ip:
            self.detector.add_to_whitelist(ip)
            self._refresh_devices()

    def _ctx_rm_whitelist(self):
        ip = self._sel_ip()
        if ip:
            self.detector.remove_from_whitelist(ip)
            self._refresh_devices()

    def _ctx_copy_ip(self):
        ip = self._sel_ip()
        if ip:
            self.root.clipboard_clear()
            self.root.clipboard_append(ip)

    def _ctx_copy_mac(self):
        s = self._dev_tree.selection()
        if s:
            mac = str(self._dev_tree.item(s[0])["values"][2])
            self.root.clipboard_clear()
            self.root.clipboard_append(mac)

    # ─────────────────────────────────────────────────────────────────────────
    #  Event queue polling
    # ─────────────────────────────────────────────────────────────────────────

    def _poll(self):
        try:
            while True:
                try:
                    ev = self.eq.get_nowait()
                    self._dispatch(ev)
                except queue.Empty:
                    break
                except Exception as ex:
                    print(f"[dispatch] {ex}")
        finally:
            self.root.after(100, self._poll)

    def _dispatch(self, ev):
        t, d = ev.get("type",""), ev.get("data")
        if   t == "new_device":    self._add_dev_row(d)
        elif t == "device_update": self._upd_dev_row(d)
        elif t == "scan_complete":
            self._btn_scan.set_text("  🔍  Scan Network  ")
            self._btn_scan.set_state("normal")
            self._refresh_devices()
            self._draw_chart()
        elif t == "alert":          self._handle_alert(d)
        elif t == "gateway_attack": self._gw_warning(d)
        elif t == "stats_update":   self._update_stats(d)
        elif t == "monitor_start":  self._log_append(str(d), "ok")
        elif t == "monitor_stop":   self._log_append(str(d), "warn")
        elif t == "log":
            self._log_append(str(d))
            self.logger.log_info(str(d))
        elif t == "error":
            self._log_append(f"ERROR: {d}", "err")
            messagebox.showerror("Error", str(d))

    # ─────────────────────────────────────────────────────────────────────────
    #  Device table helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _row_tag(self, status):
        s = str(status)
        if "ATTACK" in s:      return "attack"
        if "Gateway" in s:     return "gateway"
        if "Whitelisted" in s: return "whitelist"
        return "normal"

    def _make_dev_vals(self, n, dev):
        return (n, dev.ip, dev.mac,
                dev.first_seen.strftime("%H:%M:%S"),
                dev.last_seen.strftime("%H:%M:%S"),
                dev.packet_count, dev.status)

    def _add_dev_row(self, dev):
        tag = self._row_tag(dev.status)
        for item in self._dev_tree.get_children():
            if str(self._dev_tree.item(item)["values"][1]) == dev.ip:
                n = self._dev_tree.item(item)["values"][0]
                self._dev_tree.item(item,
                    values=self._make_dev_vals(n, dev), tags=(tag,))
                return
        n = len(self._dev_tree.get_children()) + 1
        self._dev_tree.insert("", tk.END,
                               values=self._make_dev_vals(n, dev),
                               tags=(tag,))
        self._dev_badge.config(text=f"{n} device(s)")

    def _upd_dev_row(self, dev):
        tag = self._row_tag(dev.status)
        for item in self._dev_tree.get_children():
            if str(self._dev_tree.item(item)["values"][1]) == dev.ip:
                n = self._dev_tree.item(item)["values"][0]
                self._dev_tree.item(item,
                    values=self._make_dev_vals(n, dev), tags=(tag,))
                return
        self._add_dev_row(dev)

    def _refresh_devices(self):
        for i in self._dev_tree.get_children():
            self._dev_tree.delete(i)
        for n, dev in enumerate(self.detector.known_hosts.values(), 1):
            self._dev_tree.insert("", tk.END,
                values=self._make_dev_vals(n, dev),
                tags=(self._row_tag(dev.status),))
        cnt = len(self.detector.known_hosts)
        self._dev_badge.config(text=f"{cnt} device(s)")

    # ─────────────────────────────────────────────────────────────────────────
    #  Alert handling
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_alert(self, alert):
        n   = len(self._alert_tree.get_children()) + 1
        tag = "alert_sim" if alert.time_diff == "simulated" else "alert_live"
        self._alert_tree.insert("", tk.END, values=(
            n,
            alert.timestamp.strftime("%Y-%m-%d  %H:%M:%S"),
            alert.ip, alert.old_mac, alert.new_mac, alert.time_diff,
        ), tags=(tag,))
        cnt = len(self._alert_tree.get_children())
        self._alert_badge.config(text=f"{cnt} alert(s)")

        self.logger.log_event(
            alert.ip, alert.old_mac, alert.new_mac, "ATTACK", alert.interface)

        if alert.ip in self.detector.known_hosts:
            self._upd_dev_row(self.detector.known_hosts[alert.ip])

        self._add_dash_card(alert)

        if self._sound_var.get() and _WINSOUND:
            threading.Thread(
                target=lambda: winsound.MessageBeep(winsound.MB_ICONEXCLAMATION),
                daemon=True).start()

        self._tabs.select("alerts")
        self._alert_popup(alert)

    def _add_dash_card(self, alert):
        """Add a mini alert card to the Dashboard recent-alerts list."""
        try:
            self._da_empty.destroy()
        except Exception:
            pass

        card = tk.Frame(self._da_inner, bg=BG2)
        card.pack(fill=tk.X, pady=(0, 4))

        tk.Frame(card, bg=RED, width=3).pack(side=tk.LEFT, fill=tk.Y)

        body = tk.Frame(card, bg=BG2, padx=10, pady=8)
        body.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(body, text=f"⚠  {alert.ip}",
                 font=F_BOLD, bg=BG2, fg=RED).pack(anchor="w")
        tk.Label(body, text=f"OLD: {alert.old_mac}",
                 font=F_MONO_S, bg=BG2, fg=TX1).pack(anchor="w")
        tk.Label(body, text=f"NEW: {alert.new_mac}",
                 font=F_MONO_S, bg=BG2, fg=AMBER).pack(anchor="w")

        ts = alert.timestamp.strftime("%H:%M:%S")
        sim = "  [simulation]" if alert.time_diff == "simulated" else ""
        tk.Label(body, text=f"{ts}{sim}",
                 font=("Segoe UI", 7), bg=BG2, fg=TX2).pack(anchor="e")

        self._da_canvas.update_idletasks()
        self._da_canvas.configure(
            scrollregion=self._da_canvas.bbox("all"))

    def _clear_alerts(self):
        for i in self._alert_tree.get_children():
            self._alert_tree.delete(i)
        self._alert_badge.config(text="0 alerts")

    # ─────────────────────────────────────────────────────────────────────────
    #  Alert popup  (professional modal)
    # ─────────────────────────────────────────────────────────────────────────

    def _alert_popup(self, alert):
        pop = tk.Toplevel(self.root)
        pop.title("Attack Detected")
        pop.geometry("520x330")
        pop.configure(bg=BG0)
        pop.resizable(False, False)
        pop.grab_set()

        pop.update_idletasks()
        rx = self.root.winfo_x() + (self.root.winfo_width()  - 520) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - 330) // 2
        pop.geometry(f"+{rx}+{ry}")

        # ── Red top stripe ────────────────────────────────────────────────
        tk.Frame(pop, bg=RED, height=3).pack(fill=tk.X)

        # ── Header ────────────────────────────────────────────────────────
        hf = tk.Frame(pop, bg=BG1, pady=16)
        hf.pack(fill=tk.X)
        tk.Label(hf, text="⚠", font=("Segoe UI Emoji", 26),
                 bg=BG1, fg=RED).pack(side=tk.LEFT, padx=(20, 12))
        tf = tk.Frame(hf, bg=BG1)
        tf.pack(side=tk.LEFT)
        tk.Label(tf, text="ARP SPOOFING DETECTED",
                 font=("Segoe UI", 13, "bold"),
                 bg=BG1, fg=RED).pack(anchor="w")
        tk.Label(tf,
                 text="A device MAC address has changed unexpectedly.",
                 font=F_SUB, bg=BG1, fg=TX1).pack(anchor="w")

        _sep_h(pop, BD1)

        # ── Detail grid ───────────────────────────────────────────────────
        gf = tk.Frame(pop, bg=BG0, padx=24, pady=16)
        gf.pack(fill=tk.X)

        def row(r, lbl, val, vfg=TX0):
            tk.Label(gf, text=lbl, font=F_BOLD, bg=BG0, fg=TX1,
                     width=20, anchor="w").grid(row=r, column=0,
                     sticky="w", pady=5)
            tk.Label(gf, text=val, font=F_MONO, bg=BG0,
                     fg=vfg).grid(row=r, column=1, sticky="w", padx=12,
                     pady=5)

        row(0, "Target IP Address",   alert.ip,       AMBER)
        row(1, "Legitimate MAC",      alert.old_mac,  GREEN)
        row(2, "Attacker MAC",        alert.new_mac,  RED)
        row(3, "Detected at",
            alert.timestamp.strftime("%Y-%m-%d  %H:%M:%S"), TX0)

        _sep_h(pop, BD1)

        # ── Buttons ───────────────────────────────────────────────────────
        bf = tk.Frame(pop, bg=BG0, pady=14)
        bf.pack()

        Btn(bf, "  ✅  Whitelist this IP  ",
            lambda: [self.detector.add_to_whitelist(alert.ip),
                     self._refresh_devices(), pop.destroy()],
            fg=GREEN, bg=BG2, border=GREEN,
            active_bg="#1a2e1e", padx=16, pady=8
            ).pack(side=tk.LEFT, padx=10)

        Btn(bf, "  ✖  Dismiss  ",
            pop.destroy,
            fg=RED, bg=BG2, border=RED,
            active_bg="#2a1214", padx=16, pady=8
            ).pack(side=tk.LEFT, padx=10)

    def _gw_warning(self, alert):
        messagebox.showwarning(
            "CRITICAL — Gateway Spoofed",
            f"Your default gateway ({alert.ip}) is under attack!\n\n"
            f"Legitimate MAC : {alert.old_mac}\n"
            f"Attacker MAC   : {alert.new_mac}\n\n"
            "This is a Man-in-the-Middle (MITM) attack.\n"
            "All network traffic may be intercepted!",
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  Dashboard chart
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_chart(self):
        cv = self._chart
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 60 or h < 60:
            return

        devs = sorted(self.detector.known_hosts.values(),
                      key=lambda d: d.packet_count, reverse=True)[:8]

        if not devs:
            cv.create_text(w // 2, h // 2,
                text="Scan the network to populate this chart.",
                fill=TX1, font=("Segoe UI", 11), justify="center")
            self._chart_info.config(text="")
            return

        self._chart_info.config(
            text=f"{len(devs)} host(s)  ·  "
                 f"{sum(d.packet_count for d in devs)} total packets")

        max_p  = max(d.packet_count for d in devs) or 1
        ml, mr, mt, mb = 52, 16, 24, 50
        cw     = w - ml - mr
        ch     = h - mt - mb
        n      = len(devs)
        gap    = 12
        bar_w  = max(18, (cw - gap * (n + 1)) // n)

        PALETTE = [BLUE, TEAL, GREEN, PURPLE, AMBER, PINK, RED, "#74b9ff"]

        # Grid lines
        for i in range(6):
            gy  = mt + ch * i // 5
            val = int(max_p * (5 - i) / 5)
            cv.create_line(ml, gy, w - mr, gy, fill=BD1, dash=(2, 6))
            cv.create_text(ml - 6, gy, text=str(val),
                           fill=TX2, font=F_MONO_S, anchor="e")

        # Bars
        for i, dev in enumerate(devs):
            x0    = ml + gap + i * (bar_w + gap)
            x1    = x0 + bar_w
            xm    = (x0 + x1) // 2
            ratio = dev.packet_count / max_p
            y0    = mt + int(ch * (1 - ratio))
            y1    = mt + ch
            col   = RED if "ATTACK" in dev.status else PALETTE[i % len(PALETTE)]

            # Background track
            cv.create_rectangle(x0, mt, x1, y1, fill=BG2, outline="")

            # Bar
            if y0 < y1:
                cv.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
                # Top highlight strip
                hi = lerp_color(col, "#ffffff", 0.28)
                cv.create_rectangle(x0, y0, x1, min(y0+4, y1),
                                    fill=hi, outline="")

            # Value above bar
            cv.create_text(xm, y0 - 10, text=str(dev.packet_count),
                           fill=col, font=("Segoe UI", 8, "bold"))

            # IP label (last 2 octets)
            parts  = dev.ip.split(".")
            ip_lbl = f".{parts[-2]}.{parts[-1]}" if len(parts)==4 else dev.ip
            cv.create_text(xm, y1 + 14, text=ip_lbl,
                           fill=TX1, font=F_MONO_S)

            # Status dot
            dot_col = RED if "ATTACK" in dev.status else col
            cv.create_oval(xm-3, y1+26, xm+3, y1+32,
                           fill=dot_col, outline="")

        # X-axis
        cv.create_line(ml, mt+ch, w-mr, mt+ch, fill=BD2, width=1)

    # ─────────────────────────────────────────────────────────────────────────
    #  Stats update
    # ─────────────────────────────────────────────────────────────────────────

    def _update_stats(self, stats):
        try:
            if "devices" in stats:
                self._sc_dev.update(stats["devices"])
            if "packets" in stats:
                self._sc_pkt.update(stats["packets"])
                self._sb_packets.config(text=f"Packets: {stats['packets']}")
            if "alerts" in stats:
                self._sc_alt.update(stats["alerts"])
            if "uptime" in stats:
                self._sc_upt.update(stats["uptime"])
                self._sb_uptime.config(text=f"Uptime: {stats['uptime']}")
            self._draw_chart()
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    #  Log helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _log_append(self, msg: str, tag: str = "info"):
        if tag == "info":
            ml = msg.lower()
            if any(k in ml for k in ("alert","attack","spoof","error")):
                tag = "err"
            elif any(k in ml for k in ("stopped","warning","cleared")):
                tag = "warn"
            elif any(k in ml for k in ("started","complete","found",
                                        "new device","ready")):
                tag = "ok"
            elif "[simulation]" in ml:
                tag = "sim"

        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log.insert(tk.END, f"[{ts}]  ", "ts")
        self._log.insert(tk.END, f"{msg}\n", tag)
        self._log.see(tk.END)
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", tk.END)
        self._log.configure(state="disabled")

    def _refresh_log(self):
        content = self.logger.get_log_lines()
        self._log.configure(state="normal")
        self._log.delete("1.0", tk.END)
        self._log.insert(tk.END, content)
        self._log.see(tk.END)
        self._log.configure(state="disabled")

    # ─────────────────────────────────────────────────────────────────────────
    #  Timers
    # ─────────────────────────────────────────────────────────────────────────

    def _start_timers(self):
        self._poll()
        self._tick_dot()
        self._tick_uptime()

    def _tick_dot(self):
        """Blink the status dot every 600 ms when monitoring."""
        try:
            if self.detector.is_monitoring:
                self._dot_on = not self._dot_on
                self._dot.config(fg=GREEN if self._dot_on else BG1)
            else:
                self._dot.config(fg=RED)
                self._dot_on = True
        except Exception:
            pass
        finally:
            self.root.after(600, self._tick_dot)

    def _tick_uptime(self):
        """Update uptime display every second independently."""
        try:
            if self.detector.is_monitoring:
                up = self.detector._uptime_str()
                self._sc_upt.update(up)
                self._sb_uptime.config(text=f"Uptime: {up}")
        except Exception:
            pass
        finally:
            self.root.after(1000, self._tick_uptime)
