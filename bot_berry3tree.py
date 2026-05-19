"""
bot_berry3tree.py — TripleBerryBot
เก็บเบอร์รี่ 3 ต้น: ต้น1 → W → ต้น2 → W+A/D → ต้น3 → กลับ → cooldown
"""
import threading, time

try:
    import pyautogui, pydirectinput
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


class TripleBerryBot:
    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.berries = 0; self.start_time = None

    def _walk(self, key, duration):
        if not HAS_LIBS: time.sleep(duration); return
        if duration <= 0: return
        pydirectinput.keyDown(key); time.sleep(duration); pydirectinput.keyUp(key)

    def _walk2(self, key1, dur1, key2, dur2):
        """เดิน 2 ปุ่มพร้อมกัน แล้วปล่อยทีละปุ่มตามเวลา"""
        if not HAS_LIBS: time.sleep(max(dur1, dur2)); return
        if dur1 <= 0 and dur2 <= 0: return
        pydirectinput.keyDown(key1)
        pydirectinput.keyDown(key2)
        time.sleep(min(dur1, dur2))
        if dur1 < dur2:
            pydirectinput.keyUp(key1)
            time.sleep(dur2 - dur1)
            pydirectinput.keyUp(key2)
        else:
            pydirectinput.keyUp(key2)
            time.sleep(dur1 - dur2)
            pydirectinput.keyUp(key1)

    def _find_button(self):
        if not HAS_LIBS: return True
        try:
            reg = self.cfg.get("region")
            loc = pyautogui.locateOnScreen(
                self.cfg["target_image"], confidence=self.cfg["confidence"], region=reg)
            return pyautogui.center(loc) if loc else None
        except: return None

    def _has_button(self):
        if not HAS_LIBS: return True
        try:
            reg = self.cfg.get("region")
            loc = pyautogui.locateOnScreen(
                self.cfg["target_image"], confidence=self.cfg["confidence"], region=reg)
            return loc is not None
        except: return False

    def _scan_and_align(self):
        self.log("🔍 scan หาตำแหน่ง...")
        if self._has_button(): return True
        for _ in range(3):
            if self._stop.is_set(): return False
            self._walk('w', 0.2); time.sleep(0.2)
            if self._has_button(): return True
        self._walk('s', 1.0); time.sleep(0.2)
        for _ in range(5):
            if self._stop.is_set(): return False
            if self._has_button(): return True
            self._walk('w', 0.2); time.sleep(0.2)
        self.log("❌ หาตำแหน่งไม่เจอ")
        return False

    def _collect_once(self):
        if not HAS_LIBS: time.sleep(1.0); return True
        try:
            reg = self.cfg.get("region")
            # เพิ่ม region=reg เข้าไปตรงนี้ 👇
            loc = pyautogui.locateOnScreen(self.cfg["target_image"], confidence=self.cfg["confidence"], region=reg)
            if not loc: return False
            pt = pyautogui.center(loc)
            
            # เมาส์ขยับไปคลิกได้เลย ไม่ต้องบวกพิกัดเพิ่ม
            pyautogui.moveTo(pt.x, pt.y, duration=0.1)
            time.sleep(0.1)
            for _ in range(3):
                # แก้จังหวะคลิกให้เสถียรขึ้น
                pydirectinput.mouseDown(); time.sleep(0.08); pydirectinput.mouseUp(); time.sleep(0.05)
            pydirectinput.moveTo(10, 10); return True
        except: return False

    def _wait_collect(self, label, max_wait=8.0):
        self.log(f"⏳ รอ {label}...")
        t0 = time.time()
        while time.time() - t0 < max_wait:
            if self._stop.is_set(): return False
            if self._collect_once(): return True
            time.sleep(0.3)
        self.log(f"❌ ไม่เจอปุ่ม {label}"); return False

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _run(self):
        self.start_time = time.time()
        cfg = self.cfg
        w12   = cfg["walk_1_2"]      # W ต้น1→2
        w23_w = cfg["walk_2_3_w"]    # W ต้น2→3
        w23_s = cfg["walk_2_3_side"] # A หรือ D ต้น2→3
        side  = cfg["walk_2_3_key"]  # "a" หรือ "d"
        cd    = cfg["cooldown"]

        self.log(f"🌿 เริ่ม 3-ต้น... (รอ 3 วิ)")
        for i in range(3, 0, -1):
            if self._stop.is_set(): return
            self.log(f"   {i}..."); time.sleep(1)

        while not self._stop.is_set():
            self._tick()

            # ── ต้น 1 ───────────────────────────────────────────────
            if self._wait_collect("ต้น 1"):
                self.berries += 1; self.stat("count", str(self.berries))
                self.log(f"✅ ต้น 1  ({self.berries} รวม)")
                time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self._walk('w', 0.1); time.sleep(0.5); continue

            if self._stop.is_set(): break

            # ── W ไปต้น 2 ──────────────────────────────────────────
            self.log(f"🚶 W ไปต้น 2 ({w12:.1f}s)")
            self._walk('w', w12); time.sleep(0.5)

            if self._stop.is_set(): break

            # ── ต้น 2 ───────────────────────────────────────────────
            if self._wait_collect("ต้น 2"):
                self.berries += 1; self.stat("count", str(self.berries))
                self.log(f"✅ ต้น 2  ({self.berries} รวม)")
                time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self._walk('w', 0.3); time.sleep(0.5)
                self._walk('s', 0.3); time.sleep(0.5)

            if self._stop.is_set(): break

            # ── W+A/D ไปต้น 3 ──────────────────────────────────────
            self.log(f"🚶 W+{side.upper()} ไปต้น 3 (W={w23_w:.1f}s {side.upper()}={w23_s:.1f}s)")
            self._walk2('w', w23_w, side, w23_s); time.sleep(0.5)

            if self._stop.is_set(): break

            # ── ต้น 3 ───────────────────────────────────────────────
            if self._wait_collect("ต้น 3"):
                self.berries += 1; self.stat("count", str(self.berries))
                self.log(f"✅ ต้น 3  ({self.berries} รวม)")
                time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self._walk('w', 0.3); time.sleep(0.5)
                self._walk('s', 0.3); time.sleep(0.5)

            if self._stop.is_set(): break

            # ── กลับต้น 1 ──────────────────────────────────────────
            back_side = 'd' if side == 'a' else 'a'
            self.log(f"🚶 S กลับต้น 1 ({w12:.1f}s)")
            self._walk('s', w12+0.03); 
            self.log(f"🚶 S+{back_side.upper()} กลับ ({w23_w:.1f}s {w23_s:.1f}s)")
            self._walk2('s', w23_w, back_side, w23_s-0.01); time.sleep(0.3)
            

            if self._stop.is_set(): break

            # ── Cooldown ────────────────────────────────────────────
            self.log(f"⏳ cooldown {cd:.0f}s")
            t0 = time.time()
            while time.time() - t0 < cd and not self._stop.is_set():
                self.stat("cd", f"{int(cd-(time.time()-t0))}s"); time.sleep(1)
            self.stat("cd", "-")
            if not self._stop.is_set():
                self._scan_and_align()

        if HAS_LIBS:
            for k in ('w', 's', 'a', 'd'): pydirectinput.keyUp(k)
        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()