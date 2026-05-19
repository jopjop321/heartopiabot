import threading, time
try:
    import pydirectinput
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


class ChopBot:
    """กด F ตามจำนวนที่กำหนด รอ cooldown แล้ววนซ้ำ
    walk > 0 = โหมด 2 ต้น (เดินไป-ตัด-เดินกลับ)
    walk == 0 = โหมด 1 ต้น (ตัดที่เดิม)
    """

    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.chops = 0; self.start_time = None

    def _walk(self, k, d):
        if not HAS_LIBS: time.sleep(d); return
        if d <= 0: return
        pydirectinput.keyDown(k); time.sleep(d); pydirectinput.keyUp(k)

    def _press_f(self):
        if not HAS_LIBS: time.sleep(0.3); return
        pydirectinput.keyDown('f')
        time.sleep(0.08)
        pydirectinput.keyUp('f')

    def _chop_here(self, n_chop, label):
        self.log(f"🪓 กด F {n_chop} ครั้ง ({label})...")
        for i in range(n_chop):
            if self._stop.is_set(): return False
            self._press_f()
            self.log(f"   F ครั้งที่ {i+1}/{n_chop}")
            time.sleep(0.6)
        return True

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _run(self):
        self.start_time = time.time()
        n_chop = int(self.cfg.get("chop_times", 3))
        walk   = float(self.cfg.get("walk", 0.0))
        mode   = "2 ต้น" if walk > 0 else "1 ต้น"
        self.log(f"🪓 เริ่ม Chop bot ({mode}, F {n_chop} ครั้ง)... 3 วิ")
        for i in range(3, 0, -1):
            if self._stop.is_set(): return
            self.log(f"   {i}..."); time.sleep(1)

        cfg = self.cfg
        while not self._stop.is_set():
            self._tick()
            n_chop = int(cfg.get("chop_times", 3))
            walk   = float(cfg.get("walk", 0.0))

            if not self._chop_here(n_chop, "ต้นแรก"):
                break

            if self._stop.is_set(): break

            if walk > 0:
                self.log(f"🚶 ไปต้นสอง ({walk:.1f}s)")
                self._walk('w', walk)
                time.sleep(0.5)
                if self._stop.is_set(): break

                if not self._chop_here(n_chop, "ต้นสอง"):
                    break

                if self._stop.is_set(): break

                self.log(f"🚶 ถอยกลับ ({walk:.1f}s)")
                self._walk('s', walk)
                time.sleep(0.5)

            if self._stop.is_set(): break

            self.chops += 1
            self.stat("count", str(self.chops))
            self.log(f"✅ ตัดแล้ว ({self.chops}x)")

            cd = cfg["cooldown"]
            self.log(f"⏳ รอ respawn {cd:.0f}s...")
            t0 = time.time()
            while time.time() - t0 < cd and not self._stop.is_set():
                self.stat("cd", f"{int(cd-(time.time()-t0))}s"); time.sleep(1)
            self.stat("cd", "-")

        if HAS_LIBS:
            for k in ('w','s'): pydirectinput.keyUp(k)
        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()