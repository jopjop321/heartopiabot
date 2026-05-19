"""
bot_berry.py — BerryBot และ SingleBerryBot
"""
import threading, time

try:
    import pyautogui, pydirectinput
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


class BerryBot:
    
    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.berries = 0; self.start_time = None

    def _walk(self, k, d):
        if not HAS_LIBS: time.sleep(d); return
        if d <= 0: return
        pydirectinput.keyDown(k); time.sleep(d); pydirectinput.keyUp(k)

    def _has_button(self):
        if not HAS_LIBS: return True
        try:
            reg = self.cfg.get("region")
            loc = pyautogui.locateOnScreen(self.cfg["target_image"], confidence=self.cfg["confidence"], region=reg)
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
                pydirectinput.mouseDown(); time.sleep(0.08); pydirectinput.mouseUp(); time.sleep(0.1)
            pydirectinput.moveTo(10, 10); return True
        except: return False

    def _wait_collect(self, label, max_wait=8.0):
        self.log(f"⏳ รอ {label}...")
        t0 = time.time()
        while time.time() - t0 < max_wait:
            if self._stop.is_set(): return False
            if self._collect_once(): return True
            time.sleep(0.3)
        self.log(f"❌ ไม่เจอ {label}"); return False

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _run(self):
        self.start_time = time.time()
        self.log("🌿 เริ่ม... (รอ 3 วิ)")
        for i in range(3, 0, -1):
            if self._stop.is_set(): return
            self.log(f"   {i}..."); time.sleep(1)
        cfg = self.cfg
        while not self._stop.is_set():
            self._tick()
            if self._wait_collect("ต้นแรก"):
                self.berries += 1; self.stat("count", str(self.berries))
                self.log("✅ เก็บต้นแรก"); time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self._walk('w', 0.1); time.sleep(0.5); continue
            if self._stop.is_set(): break
            self.log(f"🚶 ไปต้นสอง ({cfg['walk']:.1f}s)")
            self._walk('w', cfg["walk"]); time.sleep(0.5)
            if self._stop.is_set(): break
            if self._wait_collect("ต้นสอง"):
                self.berries += 1; self.stat("count", str(self.berries))
                self.log("✅ เก็บต้นสอง"); time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self._walk('w', 0.3); time.sleep(0.5); self._walk('s', 0.3); time.sleep(0.5)
            if self._stop.is_set(): break
            self.log(f"🚶 ถอยกลับ ({cfg['walk']:.1f}s)")
            self._walk('s', cfg["walk"]); time.sleep(0.5)
            cd = cfg["cooldown"]
            self.log(f"⏳ cooldown {cd:.0f}s")
            t0 = time.time()
            while time.time() - t0 < cd and not self._stop.is_set():
                self.stat("cd", f"{int(cd-(time.time()-t0))}s"); time.sleep(1)
            self.stat("cd", "-")
            if not self._stop.is_set():
                self._scan_and_align()
        if HAS_LIBS:
            for k in ('w','s','a','d'): pydirectinput.keyUp(k)
        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()


class SingleBerryBot:
    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.berries = 0; self.start_time = None

    def _collect_once(self):
        if not HAS_LIBS: time.sleep(1.0); return True
        try:
            loc = pyautogui.locateOnScreen(self.cfg["target_image"], confidence=self.cfg["confidence"])
            if not loc: return False
            pt = pyautogui.center(loc)
            pyautogui.moveTo(pt.x, pt.y, duration=0.2); time.sleep(0.1)
            for _ in range(3):
                pydirectinput.mouseDown(); time.sleep(0.1); pydirectinput.mouseUp(); time.sleep(0.05)
            pydirectinput.moveTo(10, 10); return True
        except: return False

    def _wait_collect(self, max_wait=8.0):
        self.log("⏳ รอปุ่ม interact...")
        t0 = time.time()
        while time.time() - t0 < max_wait:
            if self._stop.is_set(): return False
            if self._collect_once(): return True
            time.sleep(0.3)
        self.log("❌ ไม่เจอปุ่ม"); return False

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _run(self):
        self.start_time = time.time()
        self.log("🫐 เริ่ม Single Berry... (รอ 3 วิ)")
        for i in range(3, 0, -1):
            if self._stop.is_set(): return
            self.log(f"   {i}..."); time.sleep(1)
        cfg = self.cfg
        while not self._stop.is_set():
            self._tick()
            if self._wait_collect():
                self.berries += 1; self.stat("count", str(self.berries))
                self.log(f"✅ เก็บแล้ว ({self.berries} ครั้ง)")
                time.sleep(cfg["collect_wait"])
            else:
                if self._stop.is_set(): break
                self.log("🔍 หาไม่เจอ รอแล้วลองใหม่...")
            if self._stop.is_set(): break
            cd = cfg["cooldown"]
            self.log(f"⏳ รอ respawn {cd:.0f}s...")
            t0 = time.time()
            while time.time() - t0 < cd and not self._stop.is_set():
                self.stat("cd", f"{int(cd-(time.time()-t0))}s"); time.sleep(1)
            self.stat("cd", "-")
        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()
