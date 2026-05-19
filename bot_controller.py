"""
bot_controller.py — GUI only, import bots from separate files
"""
import tkinter as tk
import threading, time, math, os, sys, json

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    
try:
    import pygetwindow as gw
    HAS_GW = True
except ImportError:
    HAS_GW = False

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def img(name): return os.path.join(BASE_DIR, 'images', name)
def img_berry(name): return os.path.join(BASE_DIR, "images", "berry", name)
def img_cooking(name): return os.path.join(BASE_DIR, "images", "cooking", name)
def img_snow(name): return os.path.join(BASE_DIR, "images", "snow", name)

sys.path.insert(0, BASE_DIR)
from bot_berry      import BerryBot, SingleBerryBot
from bot_berry3tree import TripleBerryBot
from bot_cooking import CookingBot
from bot_snow    import SnowBot
from bot_chop    import ChopBot

# ══════════════════════════════════════════════════════════════════
W, H    = 460, 820
BG      = "#1a1628"
CARD    = "#241e38"
CARD2   = "#2e2648"
BORDER  = "#3d3460"
P_LILAC = "#c4b5fd"
P_PINK  = "#f9a8d4"
P_MINT  = "#6ee7b7"
P_SKY   = "#93c5fd"
P_RED   = "#fca5a5"
P_WHITE = "#f1f0f8"
P_SUB   = "#a89ec0"
P_DIM   = "#5a5278"
P_ICE   = "#bae6fd"

COOKING_MENUS = [
    {"name": "สลัดคันทรี",        "image": "menu_salad.png"},
    {"name": "แยมรวมมิตร",        "image": "menu_mixjam.png"},
    {"name": "แยมราสเบอร์รี่",    "image": "menu_rasjam.png"},
    {"name": "ซอสมะเขือเทศ",      "image": "menu_tomato.png"},
    {"name": "แยมบลูเบอร์รี่",    "image": "menu_bluejam.png"},
    {"name": "แยมแอปเปิล",        "image": "menu_applejam.png"},
    {"name": "แยมส้ม",            "image": "menu_orangejam.png"},
    {"name": "แยมสตรอว์เบอร์รี่", "image": "menu_strawjam.png"},
    {"name": "แยมสับปะรด",        "image": "menu_pineapplejam.png"},
    {"name": "แยมองุ่น",          "image": "menu_grapejam.png"},
    {"name": "ฟิชแอนด์ชิปส์",    "image": "menu_fish_and_chips.png"},
    {"name": "ชีสเค้ก",           "image": "menu_cheesecake.png"},
]

BOTS = {
    "berry": {
        "label":  "🍒  Berry",
        "accent": P_LILAC,
        "hotkey": "F9",
        "stats":  [("count","BERRIES","🍒"), ("time","ELAPSED","⏱"), ("cd","COOLDOWN","⏳")],
    },
    "cooking": {
        "label":  "🍳  Cooking",
        "accent": P_MINT,
        "hotkey": "F10",
        "stats":  [("count","COOKED","🍳"), ("time","ELAPSED","⏱")],
    },
    "snow": {
        "label":  "❄️  Snow",
        "accent": P_ICE,
        "hotkey": "F11",
        "stats":  [("rounds","ROUNDS","❄️"), ("time","ELAPSED","⏱")],
    },
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bot Heartopia")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.geometry(f"{W}x{H}")
        self._active_bot  = None
        self._active_key  = None
        self._running     = False
        self._current_tab = "berry"
        self._stat_vars   = {}
        self._tab_btns    = {}
        self._tab_frames  = {}
        self._orb_t       = 0.0
        self._build()
        self._switch_tab("berry")
        self._tick_orbs()
        self.after(100, self._refresh_preset_btns)
        self.after(100, lambda: self._refresh_triple_preset_btns() if hasattr(self, '_t_preset_btns') else None)
        if HAS_KEYBOARD:
            keyboard.add_hotkey("f9",  lambda: self.after(0, lambda: self._hotkey("berry")))
            keyboard.add_hotkey("f10", lambda: self.after(0, lambda: self._hotkey("cooking")))
            keyboard.add_hotkey("f11", lambda: self.after(0, lambda: self._hotkey("snow")))
        if not HAS_KEYBOARD:
            self._log("pip install keyboard for hotkeys")

    def _tick_orbs(self):
        self._orb_t += 0.012
        t = self._orb_t
        x1 = 60  + math.sin(t * 0.7) * 30
        y1 = 80  + math.cos(t * 0.5) * 20
        x2 = W - 70 + math.cos(t * 0.6) * 35
        y2 = H - 90  + math.sin(t * 0.4) * 25
        self._cv.coords("orb1", x1-110, y1-110, x1+110, y1+110)
        self._cv.coords("orb2", x2-90,  y2-90,  x2+90,  y2+90)
        self.after(40, self._tick_orbs)

    def _build(self):
        self._cv = tk.Canvas(self, width=W, height=H, bg=BG, highlightthickness=0)
        self._cv.place(x=0, y=0)
        self._cv.create_oval(-60,-60,220,220, fill="#2a1f45", outline="", tags="orb1")
        self._cv.create_oval(0,0,180,180,     fill="#1a2a3a", outline="", tags="orb2")
        for gx in range(20, W, 38):
            for gy in range(20, H, 38):
                self._cv.create_oval(gx-1, gy-1, gx+1, gy+1, fill="#2a2440", outline="")

        tk.Label(self, text="✦ Heartopia",
                 font=("Segoe UI", 15, "bold"), bg=BG, fg=P_WHITE).place(x=20, y=14)
        # ---- จัดกลุ่มมุมขวาบน (เป็นกล่องๆ เรียงกัน ไม่ทับแน่นอน) ----
        # 1. สร้างกล่องหลักไปวางชิดขวาบน
        top_right_frame = tk.Frame(self, bg=BG)
        top_right_frame.place(x=W-16, y=14, anchor="ne")

        # 2. กล่องปุ่ม "ล็อคเป้าใหม่" (สีม่วง)
        relock_btn = tk.Label(top_right_frame, text="🔄 ล็อคเป้าใหม่", 
                              font=("Segoe UI", 8, "bold"), bg=CARD2, fg=P_LILAC, 
                              cursor="hand2", padx=10, pady=4)
        relock_btn.pack(side="left", padx=(0, 8)) # เรียงจากซ้าย เว้นระยะห่าง 8 px
        relock_btn.bind("<Button-1>", lambda e: self._find_window())

        # 3. กล่องสถานะ "idle / running" (สีทึบ)
        self._status_lbl = tk.Label(top_right_frame, text="idle", 
                                    font=("Segoe UI", 9, "bold"), bg=CARD, fg=P_DIM, 
                                    padx=12, pady=3)
        self._status_lbl.pack(side="left") # เรียงต่อกันไป
        # --------------------------------------------------------
        self._region = None
        self._target_game = "Heartopia" # กำหนดชื่อเกมไว้ในตัวแปรธรรมดา
        self.after(500, self._find_window)
        # -----------------------------
        tk.Frame(self, bg=BORDER, height=1).place(x=0, y=50, width=W)

        tab_bar = tk.Frame(self, bg=BG)
        tab_bar.place(x=16, y=60)
        for key, meta in BOTS.items():
            btn = tk.Label(tab_bar, text=meta["label"],
                           font=("Segoe UI", 10, "bold"),
                           bg=CARD, fg=P_DIM, padx=20, pady=8, cursor="hand2")
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
        tk.Frame(self, bg=BORDER, height=1).place(x=0, y=100, width=W)

        container = tk.Frame(self, bg=BG, width=W-32, height=430)
        container.place(x=16, y=108)
        container.pack_propagate(False)
        self._tab_frames["berry"]   = self._build_berry_tab(container)
        self._tab_frames["cooking"] = self._build_cooking_tab(container)
        self._tab_frames["snow"]    = self._build_snow_tab(container)
        for f in self._tab_frames.values():
            f.place(x=0, y=0, width=W-32, height=430)

        self._start_btn = tk.Button(
            self, text="▶   START  (F9)",
            font=("Segoe UI", 13, "bold"),
            bg=P_LILAC, fg=BG, activebackground=P_PINK, activeforeground=BG,
            relief="flat", bd=0, cursor="hand2", command=self._toggle)
        self._start_btn.place(x=16, y=548, width=W-32, height=52)

        log_y = 610; log_h = H - log_y - 20
        self._log_frame = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        self._log_frame.place(x=16, y=log_y, width=W-32, height=log_h)
        top_row = tk.Frame(self._log_frame, bg=CARD)
        top_row.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(top_row, text="LOG", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(side="left")
        clr = tk.Label(top_row, text="✕ clear", font=("Segoe UI", 8),
                       bg=CARD, fg=P_DIM, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self._clear_log())
        self._logbox = tk.Text(self._log_frame, font=("Consolas", 9),
                               bg=CARD, fg=P_SUB, insertbackground=P_WHITE,
                               relief="flat", bd=0, wrap="word",
                               state="disabled", selectbackground=CARD2)
        self._logbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        hint = "F9=Berry  F10=Cooking  F11=Snow" if HAS_KEYBOARD else "pip install keyboard for hotkeys"
        tk.Label(self, text=hint, font=("Segoe UI", 8),
                 bg=BG, fg=P_DIM).place(x=W//2, y=H-10, anchor="center")

    # ── Berry tab ────────────────────────────────────────────────
    def _build_berry_tab(self, parent):
        ac = BOTS["berry"]["accent"]
        frame = tk.Frame(parent, bg=BG)

        sf = tk.Frame(frame, bg=BG)
        sf.pack(fill="x", pady=(4, 6))
        for i, (k, lbl, icon) in enumerate(BOTS["berry"]["stats"]):
            vk = f"berry_{k}"
            self._stat_vars[vk] = tk.StringVar(value="-")
            card = tk.Frame(sf, bg=CARD, highlightbackground=ac, highlightthickness=1)
            card.grid(row=0, column=i, padx=(0 if i==0 else 5, 0), sticky="nsew")
            sf.columnconfigure(i, weight=1)
            tk.Label(card, text=f"{icon} {lbl}", font=("Segoe UI", 8),
                     bg=CARD, fg=P_DIM).pack(pady=(8, 0))
            tk.Label(card, textvariable=self._stat_vars[vk],
                     font=("Segoe UI", 16, "bold"), bg=CARD, fg=ac).pack(pady=(2, 8))

        self._berry_mode    = tk.StringVar(value="double")
        self._single_action = tk.StringVar(value="collect")
        # ── NEW: action สำหรับ 2 ต้น ─────────────────────────
        self._double_action = tk.StringVar(value="collect")

        mode_row = tk.Frame(frame, bg=BG)
        mode_row.pack(fill="x", pady=(0, 4))

        def make_mode_btn(parent, text, value, var, cmd):
            btn = tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                           bg=CARD, fg=P_DIM, padx=14, pady=5, cursor="hand2")
            btn.pack(side="left", padx=(0, 5))
            btn.bind("<Button-1>", lambda e: [var.set(value), cmd()])
            return btn

        self._mode_btn_double = make_mode_btn(mode_row, "🍒🍒  2 ต้น", "double",
                                               self._berry_mode, lambda: _refresh())
        self._mode_btn_single = make_mode_btn(mode_row, "🍒  1 ต้น", "single",
                                               self._berry_mode, lambda: _refresh())
        self._mode_btn_triple = make_mode_btn(mode_row, "🍒🍒🍒  3 ต้น", "triple",
                                               self._berry_mode, lambda: _refresh())

        # action row สำหรับ 1 ต้น (เดิม)
        self._action_row = tk.Frame(frame, bg=BG)
        self._action_btn_collect = make_mode_btn(self._action_row, "🍒 เก็บ", "collect",
                                                  self._single_action, lambda: _refresh())
        self._action_btn_chop    = make_mode_btn(self._action_row, "🪓 ตัด", "chop",
                                                  self._single_action, lambda: _refresh())

        # ── NEW: action row สำหรับ 2 ต้น ──────────────────────
        self._action_row_double = tk.Frame(frame, bg=BG)
        self._action_btn_double_collect = make_mode_btn(
            self._action_row_double, "🍒 เก็บ", "collect",
            self._double_action, lambda: _refresh())
        self._action_btn_double_chop = make_mode_btn(
            self._action_row_double, "🪓 ตัด", "chop",
            self._double_action, lambda: _refresh())

        cfg_card = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        cfg_card.pack(fill="x")

        self._preset_section = tk.Frame(cfg_card, bg=CARD)
        hdr = tk.Frame(self._preset_section, bg=CARD)
        hdr.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(hdr, text="CONFIG", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(side="left")
        tk.Label(hdr, text="คลิก=โหลด  คลิกขวา=บันทึก",
                 font=("Segoe UI", 7), bg=CARD, fg=P_DIM).pack(side="right")
        self._preset_btns = []
        prow = tk.Frame(self._preset_section, bg=CARD)
        prow.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(prow, text="PRESET", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(side="left", padx=(0, 8))
        for i in range(1, 6):
            btn = tk.Label(prow, text=f"{i}", font=("Segoe UI", 8, "bold"),
                           bg=CARD2, fg=P_DIM, width=5, pady=3, cursor="hand2")
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, n=i: self._load_preset(n))
            btn.bind("<Button-3>", lambda e, n=i: self._save_preset(n))
            self._preset_btns.append(btn)

        self._cfg_label = tk.Frame(cfg_card, bg=CARD)
        tk.Label(self._cfg_label, text="  CONFIG", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(anchor="w", pady=(8, 2))

        self._b_walk       = tk.DoubleVar(value=5.7)
        self._b_cd         = tk.DoubleVar(value=98.0)
        self._b_conf       = tk.DoubleVar(value=0.70)
        self._b_cwait      = tk.DoubleVar(value=1.5)
        self._b_chop_times = tk.IntVar(value=3)

        # triple mode vars
        self._t_cd       = tk.DoubleVar(value=98.0)
        self._t_walk12   = tk.DoubleVar(value=5.7)
        self._t_walk23_w = tk.DoubleVar(value=5.7)
        self._t_walk23_s = tk.DoubleVar(value=1.8)
        self._t_side     = tk.StringVar(value="a")
        self._t_side_btns = {}

        slider_frame = tk.Frame(cfg_card, bg=CARD)

        for lbl, var, lo, hi, step, fmt in [
            ("Walk / Back (s)",  self._b_walk,  0.0,  15.0,  0.1,  "{:.1f}"),
            ("Cooldown (s)",     self._b_cd,    30.0, 300.0, 1.0,  "{:.0f}"),
            ("Confidence",       self._b_conf,  0.40, 0.99,  0.01, "{:.2f}"),
            ("Collect Wait (s)", self._b_cwait, 0.0,  10.0,  0.1,  "{:.1f}"),
        ]:
            self._slider_row(slider_frame, lbl, var, lo, hi, step, fmt, ac)

        self._chop_row = tk.Frame(slider_frame, bg=CARD)
        self._slider_row(self._chop_row, "Chop Times",
                         self._b_chop_times, 1, 3, 1, "{:d}", ac)

        # ── Triple mode config ────────────────────────────────────
        self._triple_section = tk.Frame(cfg_card, bg=CARD)
        t_hdr = tk.Frame(self._triple_section, bg=CARD)
        t_hdr.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(t_hdr, text="CONFIG", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(side="left")
        tk.Label(t_hdr, text="คลิก=โหลด  คลิกขวา=บันทึก",
                 font=("Segoe UI", 7), bg=CARD, fg=P_DIM).pack(side="right")
        self._t_preset_btns = []
        t_prow = tk.Frame(self._triple_section, bg=CARD)
        t_prow.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(t_prow, text="PRESET", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=P_DIM).pack(side="left", padx=(0, 8))
        for i in range(1, 6):
            btn = tk.Label(t_prow, text=f"{i}", font=("Segoe UI", 8, "bold"),
                           bg=CARD2, fg=P_DIM, width=5, pady=3, cursor="hand2")
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, n=i: self._load_triple_preset(n))
            btn.bind("<Button-3>", lambda e, n=i: self._save_triple_preset(n))
            self._t_preset_btns.append(btn)
            
        triple_slider_frame = tk.Frame(cfg_card, bg=CARD)
        self._slider_row(triple_slider_frame, "Cooldown (s)",
                         self._t_cd, 30.0, 300.0, 1.0, "{:.0f}", ac)
        self._slider_row(triple_slider_frame, "Walk 1→2 W (s)",
                         self._t_walk12, 0.0, 15.0, 0.1, "{:.1f}", ac)
        self._slider_row(triple_slider_frame, "Walk 2→3 W (s)",
                         self._t_walk23_w, 0.0, 15.0, 0.1, "{:.1f}", ac)

        # A/D selector + slider
        side_row = tk.Frame(triple_slider_frame, bg=CARD)
        side_row.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(side_row, text="ทิศทาง 2→3", font=("Segoe UI", 9),
                 bg=CARD, fg=P_SUB).pack(side="left")
        for skey, slbl in [("a", "◀ A"), ("d", "D ▶")]:
            sb = tk.Label(side_row, text=slbl, font=("Segoe UI", 8, "bold"),
                          bg=CARD2, fg=P_DIM, padx=10, pady=2, cursor="hand2")
            sb.pack(side="right", padx=(4, 0))
            sb.bind("<Button-1>", lambda e, k=skey: self._set_triple_side(k))
            self._t_side_btns[skey] = sb
        self._set_triple_side("a")

        self._slider_row(triple_slider_frame, "Walk 2→3 A/D (s)",
                         self._t_walk23_s, 0.0, 10.0, 0.1, "{:.1f}", ac)

        tk.Frame(cfg_card, bg=CARD, height=4).pack()

        def _refresh():
            mode          = self._berry_mode.get()
            single_action = self._single_action.get()
            double_action = self._double_action.get()

            self._mode_btn_double.config(bg=CARD2 if mode=="double" else CARD,
                                         fg=ac    if mode=="double" else P_DIM)
            self._mode_btn_single.config(bg=CARD2 if mode=="single" else CARD,
                                         fg=ac    if mode=="single" else P_DIM)
            self._mode_btn_triple.config(bg=CARD2 if mode=="triple" else CARD,
                                         fg=ac    if mode=="triple" else P_DIM)

            # single action buttons
            self._action_btn_collect.config(bg=CARD2 if single_action=="collect" else CARD,
                                            fg=ac    if single_action=="collect" else P_DIM)
            self._action_btn_chop.config(   bg=CARD2 if single_action=="chop"    else CARD,
                                            fg=ac    if single_action=="chop"    else P_DIM)

            # ── NEW: double action buttons ─────────────────────
            self._action_btn_double_collect.config(
                bg=CARD2 if double_action=="collect" else CARD,
                fg=ac    if double_action=="collect" else P_DIM)
            self._action_btn_double_chop.config(
                bg=CARD2 if double_action=="chop"    else CARD,
                fg=ac    if double_action=="chop"    else P_DIM)

            # show/hide action rows
            self._action_row.pack_forget()
            self._action_row_double.pack_forget()
            if mode == "single":
                self._action_row.pack(fill="x", pady=(0, 4), after=mode_row)
            elif mode == "double":
                self._action_row_double.pack(fill="x", pady=(0, 4), after=mode_row)

            # show/hide chop row (single chop only)
            if mode == "single" and single_action == "chop":
                self._chop_row.pack(fill="x")
            # ── NEW: double chop ก็แสดง chop_row ──────────────
            elif mode == "double" and double_action == "chop":
                self._chop_row.pack(fill="x")
            else:
                self._chop_row.pack_forget()

            # swap config sections
            self._preset_section.pack_forget()
            self._cfg_label.pack_forget()
            slider_frame.pack_forget()
            self._triple_section.pack_forget()
            triple_slider_frame.pack_forget()

            if mode == "double":
                self._preset_section.pack(fill="x")
                slider_frame.pack(fill="x")
            elif mode == "triple":
                self._triple_section.pack(fill="x")
                triple_slider_frame.pack(fill="x")
            else:
                self._cfg_label.pack(fill="x")
                slider_frame.pack(fill="x")

            # resize container
            if (mode == "single" and single_action == "chop") or \
               (mode == "double" and double_action == "chop"):
                container_h = 460
            elif mode == "triple":
                container_h = 480
            else:
                container_h = 430
            frame.master.config(height=container_h)
            frame.place(width=W-32, height=container_h)
            if hasattr(self, '_start_btn'):
                self._start_btn.place(x=16, y=container_h+108+10, width=W-32, height=52)
            if hasattr(self, '_log_frame'):
                log_start = container_h + 108 + 10 + 52 + 8
                self._log_frame.place(x=16, y=log_start, width=W-32,
                                      height=H - log_start - 20)

            # defaults (only reset when switching mode, not action)
            if mode == "double" and double_action == "collect":
                self._b_walk.set(5.7); self._b_cd.set(98); self._b_cwait.set(1.5)
            elif mode == "double" and double_action == "chop":
                self._b_walk.set(5.7); self._b_cd.set(98)
            elif mode == "single":
                self._b_walk.set(0); self._b_cd.set(120); self._b_cwait.set(0)

        _refresh()
        return frame

    # ── Cooking tab ───────────────────────────────────────────────
    def _build_cooking_tab(self, parent):
        ac = BOTS["cooking"]["accent"]
        frame = tk.Frame(parent, bg=BG)

        # ── Stat cards ───────────────────────────────────────────
        sf = tk.Frame(frame, bg=BG)
        sf.pack(fill="x", pady=(4, 8))
        for i, (k, lbl, icon) in enumerate(BOTS["cooking"]["stats"]):
            vk = f"cooking_{k}"
            self._stat_vars[vk] = tk.StringVar(value="-")
            card = tk.Frame(sf, bg=CARD, highlightbackground=ac, highlightthickness=1)
            card.grid(row=0, column=i, padx=(0 if i == 0 else 5, 0), sticky="nsew")
            sf.columnconfigure(i, weight=1)
            tk.Label(card, text=f"{icon} {lbl}", font=("Segoe UI", 8),
                     bg=CARD, fg=P_DIM).pack(pady=(8, 0))
            tk.Label(card, textvariable=self._stat_vars[vk],
                     font=("Segoe UI", 16, "bold"), bg=CARD, fg=ac).pack(pady=(2, 8))

        # ── Mode sub-tabs ────────────────────────────────────────
        self._cook_mode = tk.StringVar(value="safe")
        self._cook_mode_btns = {}
        mode_row = tk.Frame(frame, bg=BG)
        mode_row.pack(fill="x", pady=(0, 6))
        for mode_key, mode_label in [("safe",  "🔥  Mode 1  (Safe)"),
                                      ("multi", "🔥🔥  Mode 2  (Multi-fire)")]:
            btn = tk.Label(mode_row, text=mode_label,
                           font=("Segoe UI", 9, "bold"),
                           bg=CARD, fg=P_DIM, padx=14, pady=6, cursor="hand2")
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda e, m=mode_key: self._set_cook_mode(m))
            self._cook_mode_btns[mode_key] = btn

        # ── Menu toggle buttons ───────────────────────────────────
        tk.Label(frame, text="เมนู", font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=P_DIM).pack(anchor="w", pady=(6, 2))

        menu_grid = tk.Frame(frame, bg=BG)
        menu_grid.pack(fill="x")

        self._menu_btns = {}  # name -> Label widget
        self._cook_selected = []
        
        def toggle_menu(name, ipath):
            for i, (n, _) in enumerate(self._cook_selected):
                if n == name:
                    self._cook_selected.pop(i)
                    _refresh_menu_btns()
                    return
            self._cook_selected.append((name, img(ipath)))
            _refresh_menu_btns()

        def _refresh_menu_btns():
            selected_names = {n for n, _ in self._cook_selected}
            for name, btn in self._menu_btns.items():
                if name in selected_names:
                    btn.config(bg=ac, fg=BG)
                else:
                    btn.config(bg=CARD, fg=P_DIM)

        COLS = 4
        for i, m in enumerate(COOKING_MENUS):
            r, c = divmod(i, COLS)
            btn = tk.Label(menu_grid, text=m["name"],
                           font=("Segoe UI", 8),
                           bg=CARD, fg=P_DIM,
                           padx=6, pady=4, cursor="hand2",
                           wraplength=90, justify="center")
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            menu_grid.columnconfigure(c, weight=1)
            btn.bind("<Button-1>",
                     lambda e, n=m["name"], p=m["image"]: toggle_menu(n, p))
            self._menu_btns[m["name"]] = btn

        self._set_cook_mode("safe")
        return frame

    def _set_cook_mode(self, mode):
        self._cook_mode.set(mode)
        ac = BOTS["cooking"]["accent"]
        for k, btn in self._cook_mode_btns.items():
            btn.config(bg=CARD2 if k == mode else CARD,
                       fg=ac   if k == mode else P_DIM)

    def _set_triple_side(self, key):
        self._t_side.set(key)
        ac = BOTS["berry"]["accent"]
        for k, btn in self._t_side_btns.items():
            btn.config(bg=CARD2 if k == key else CARD,
                       fg=ac   if k == key else P_DIM)

    def _t_presets_path(self): return img_berry("berry3_presets.json")

    def _load_t_presets_file(self):
        p = self._t_presets_path()
        if not os.path.exists(p): return {}
        with open(p) as f: return json.load(f)

    def _save_t_presets_file(self, data):
        with open(self._t_presets_path(), "w") as f: json.dump(data, f, indent=2)

    def _get_triple_cfg(self):
        return {"cd": self._t_cd.get(), "walk12": self._t_walk12.get(),
                "walk23_w": self._t_walk23_w.get(), "walk23_s": self._t_walk23_s.get(),
                "side": self._t_side.get()}

    def _apply_triple_cfg(self, cfg):
        self._t_cd.set(cfg.get("cd", 98.0))
        self._t_walk12.set(cfg.get("walk12", 5.7))
        self._t_walk23_w.set(cfg.get("walk23_w", 5.7))
        self._t_walk23_s.set(cfg.get("walk23_s", 1.8))
        self._set_triple_side(cfg.get("side", "a"))

    def _save_triple_preset(self, n):
        data = self._load_t_presets_file()
        data[str(n)] = self._get_triple_cfg()
        self._save_t_presets_file(data)
        self._refresh_triple_preset_btns()
        self._log(f"✅ บันทึก Triple Preset {n}")

    def _load_triple_preset(self, n):
        data = self._load_t_presets_file()
        cfg  = data.get(str(n))
        if not cfg:
            self._log(f"❌ Triple Preset {n} ยังว่าง"); return
        self._apply_triple_cfg(cfg)
        self._log(f"📂 โหลด Triple Preset {n}")

    def _refresh_triple_preset_btns(self):
        data = self._load_t_presets_file()
        ac   = BOTS["berry"]["accent"]
        for i, btn in enumerate(self._t_preset_btns, 1):
            has = str(i) in data
            btn.config(bg=ac if has else CARD2, fg=BG if has else P_DIM)

    # ── Snow tab ──────────────────────────────────────────────────
    def _build_snow_tab(self, parent):
        ac = BOTS["snow"]["accent"]
        frame = tk.Frame(parent, bg=BG)
        sf = tk.Frame(frame, bg=BG)
        sf.pack(fill="x", pady=(4, 10))
        for i, (k, lbl, icon) in enumerate(BOTS["snow"]["stats"]):
            vk = f"snow_{k}"
            self._stat_vars[vk] = tk.StringVar(value="-")
            card = tk.Frame(sf, bg=CARD, highlightbackground=ac, highlightthickness=1)
            card.grid(row=0, column=i, padx=(0 if i==0 else 5, 0), sticky="nsew")
            sf.columnconfigure(i, weight=1)
            tk.Label(card, text=f"{icon} {lbl}", font=("Segoe UI", 8),
                     bg=CARD, fg=P_DIM).pack(pady=(8, 0))
            tk.Label(card, textvariable=self._stat_vars[vk],
                     font=("Segoe UI", 16, "bold"), bg=CARD, fg=ac).pack(pady=(2, 8))
        tk.Frame(frame, bg=BG, height=8).pack()
        return frame

    # ── Slider ───────────────────────────────────────────────────
    def _slider_row(self, parent, label, var, lo, hi, step, fmt, accent):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=12, pady=2)
        top = tk.Frame(row, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=label, font=("Segoe UI", 9),
                 bg=CARD, fg=P_SUB).pack(side="left")
        badge = tk.Label(top, text=fmt.format(var.get()),
                         font=("Segoe UI", 10, "bold"),
                         bg=accent, fg=BG, padx=10, pady=2)
        badge.pack(side="right")
        var.trace_add("write", lambda *_: badge.config(text=fmt.format(var.get())))
        tk.Scale(row, variable=var, from_=lo, to=hi, resolution=step,
                 orient="horizontal", showvalue=False,
                 bg=CARD, troughcolor=CARD2, activebackground=accent,
                 highlightthickness=0, sliderrelief="flat", sliderlength=18,
                 fg=P_WHITE).pack(fill="x", pady=(2, 0))

    # ── Tab switch ───────────────────────────────────────────────
    def _switch_tab(self, key):
        if self._running: return
        self._current_tab = key
        ac = BOTS[key]["accent"]
        self._tab_frames[key].tkraise()
        for k, btn in self._tab_btns.items():
            btn.config(bg=CARD2 if k==key else CARD, fg=ac if k==key else P_DIM)
        self._start_btn.config(
            text=f"▶   START  ({BOTS[key]['hotkey']})",
            bg=ac, activebackground=P_PINK if key=="berry" else P_SKY)

    # ── Toggle ───────────────────────────────────────────────────
    def _toggle(self):
        if not self._running: self._start()
        else:                  self._stop_bot()

    def _start(self):
        key  = self._current_tab
        meta = BOTS[key]
        ac   = meta["accent"]
        for k, btn in self._tab_btns.items():
            if k != key: btn.config(state="disabled", fg=BORDER, cursor="")
            else:        btn.config(state="disabled")
        self._running = True; self._active_key = key
        self._status_lbl.config(text=f"{meta['label']} running", fg=ac)
        self._start_btn.config(text=f"STOP  ({meta['hotkey']})",
                               bg=P_RED, activebackground="#fca5a5")

        def log(msg):  self.after(0, lambda m=msg: self._log(m))
        def stat(k,v): self.after(0, lambda kk=k,vv=v: self._stat_vars[f"{key}_{kk}"].set(vv))

        if key == "berry":
            mode   = self._berry_mode.get()
            action = self._single_action.get()
            cfg = {"target_image": img_berry("interact_btn01.png"),
                   "confidence":   self._b_conf.get(),
                   "walk":         self._b_walk.get(),
                   "cooldown":     self._b_cd.get(),
                   "collect_wait": self._b_cwait.get()}
            if mode == "triple":
                cfg = {"target_image":   img_berry("interact_btn01.png"),
                       "confidence":     self._b_conf.get(),
                       "collect_wait":   self._b_cwait.get(),
                       "cooldown":       self._t_cd.get(),
                       "walk_1_2":       self._t_walk12.get(),
                       "walk_2_3_w":     self._t_walk23_w.get(),
                       "walk_2_3_side":  self._t_walk23_s.get(),
                       "walk_2_3_key":   self._t_side.get()}
                self._active_bot = TripleBerryBot(cfg, log, stat)
            elif mode == "single" and action == "chop":
                cfg["chop_times"] = self._b_chop_times.get()
                self._active_bot = ChopBot(cfg, log, stat)
            elif mode == "single":
                self._active_bot = SingleBerryBot(cfg, log, stat)
            elif mode == "double" and self._double_action.get() == "chop":
                cfg["chop_times"] = self._b_chop_times.get()
                self._active_bot = ChopBot(cfg, log, stat)
            else:
                self._active_bot = BerryBot(cfg, log, stat)

        elif key == "cooking":
            # ถ้าไม่เลือกเมนูเลย = ทำแค่เมนูล่าสุดในเกม
            if not self._cook_selected:
                menu_queue = [{"name": "latest", "image": None}]
            else:
                menu_queue = [{"name": n, "image": p} for n, p in self._cook_selected]

            cfg = {
                "start_image":   img_cooking("start001.png"),
                "start2_image":  img_cooking("start2.png"),
                "cook1_image":   img_cooking("cook1.png"),
                "endcook_image": img_cooking("endcook.png"),
                "end_image":     img_cooking("end.png"),
                "mode":          self._cook_mode.get(),
                "menu_queue":    menu_queue,
            }
            self._active_bot = CookingBot(cfg, log, stat)

        else:
            cfg = {"start_image":  img("snow_start.png"),
                   "start2_image": img("snow_confirm.png"),
                   "snow_image":   img("snow_hit.png"),
                   "end_image":    img("snow_end.png"),
                   "end_image2":   img("snow_end2.png"),
                   "end_image3":   img("snow_end3.png")}
            self._active_bot = SnowBot(cfg, log, stat)
        cfg["region"] = getattr(self, "_region", None)
        self._active_bot.start()

    def _stop_bot(self):
        if self._active_bot: self._active_bot.stop(); self._active_bot = None
        self._running = False
        key = self._active_key or self._current_tab
        for k, btn in self._tab_btns.items():
            btn.config(state="normal", cursor="hand2")
        self._switch_tab(key)
        self._status_lbl.config(text="idle", fg=P_DIM)

    def _hotkey(self, key):
        if self._running and self._active_key == key: self._stop_bot()
        elif not self._running: self._switch_tab(key); self._start()

    def _log(self, msg):
        self._logbox.config(state="normal")
        self._logbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self._logbox.see("end")
        self._logbox.config(state="disabled")

    def _clear_log(self):
        self._logbox.config(state="normal")
        self._logbox.delete("1.0", "end")
        self._logbox.config(state="disabled")

    def _get_current_cfg(self):
        return {"mode": self._berry_mode.get(), "walk": self._b_walk.get(),
                "cooldown": self._b_cd.get(), "confidence": self._b_conf.get(),
                "collect_wait": self._b_cwait.get()}

    def _apply_cfg(self, cfg):
        self._berry_mode.set(cfg.get("mode", "double"))
        self._b_walk.set(cfg.get("walk", 5.7))
        self._b_cd.set(cfg.get("cooldown", 98.0))
        self._b_conf.set(cfg.get("confidence", 0.70))
        self._b_cwait.set(cfg.get("collect_wait", 1.5))

    def _presets_path(self): return img_berry("berry_presets.json")

    def _load_presets_file(self):
        p = self._presets_path()
        if not os.path.exists(p): return {}
        with open(p) as f: return json.load(f)

    def _save_presets_file(self, data):
        with open(self._presets_path(), "w") as f: json.dump(data, f, indent=2)

    def _save_preset(self, n):
        data = self._load_presets_file()
        data[str(n)] = self._get_current_cfg()
        self._save_presets_file(data)
        self._refresh_preset_btns()
        self._log(f"✅ บันทึก Preset {n}")

    def _load_preset(self, n):
        data = self._load_presets_file()
        cfg  = data.get(str(n))
        if not cfg:
            self._log(f"❌ Preset {n} ยังว่าง (คลิกขวาเพื่อบันทึก)"); return
        self._apply_cfg(cfg)
        self._log(f"📂 โหลด Preset {n}  walk={cfg.get('walk')}s  cd={cfg.get('cooldown')}s")

    def _refresh_preset_btns(self):
        data = self._load_presets_file()
        ac   = BOTS["berry"]["accent"]
        for i, btn in enumerate(self._preset_btns, 1):
            has = str(i) in data
            btn.config(bg=ac if has else CARD2, fg=BG if has else P_DIM)

    def on_close(self):
        if self._active_bot: self._active_bot.stop()
        if HAS_KEYBOARD: keyboard.unhook_all()
        self.destroy()

    def _find_window(self):
        if not HAS_GW: return
        
        title = getattr(self, "_target_game", "Heartopia") 
        
        # 🚨 แก้ตรงนี้: ค้นหาหน้าต่างที่มีคำว่า Heartopia แต่ "ต้องไม่มี" คำว่า Bot และ Visual Studio
        windows = [
            w for w in gw.getWindowsWithTitle(title) 
            if "Bot" not in w.title and "Visual Studio" not in w.title
        ]
        
        if not windows:
            self._log(f"❌ หาหน้าต่างเกม '{title}' ไม่เจอ (เปิดเกมหรือยัง?)")
            self._region = None
            return
            
        win = windows[0]
        self._region = (win.left, win.top, win.width, win.height)
        self._log(f"🎯 ล็อคเป้า '{win.title}' เรียบร้อย")
    # -----------------------------
    
if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
