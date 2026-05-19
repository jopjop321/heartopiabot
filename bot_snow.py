"""
bot_snow.py — SnowBot
"""
import threading, time

try:
    import pyautogui, pydirectinput
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


class SnowBot:
    GRID = 60

    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.rounds = 0; self.start_time = None
        self._clicked = set()

    def _snap(self, v): return (v // self.GRID) * self.GRID
    def _already(self, x, y): return (self._snap(x), self._snap(y)) in self._clicked
    def _mark(self, x, y):    self._clicked.add((self._snap(x), self._snap(y)))

    def _click(self, x, y):
        if not HAS_LIBS: return
        reg = self.cfg.get("region")
        
        if reg:
            x += reg[0]
            y += reg[1]
            
        # 1. เติม duration ให้เมาส์วิ่งไปหาหิมะ ไม่วาร์ปจนเกมตกใจ (0.03 วินาที กำลังสวย)
        pyautogui.moveTo(x, y, duration=0.03)
        
        # 2. หยุดเบรกเมาส์ให้เป้านิ่งสนิท ก่อนสับไก
        time.sleep(0.02) 
        
        # 3. จังหวะปาหิมะ (กดค้างนิดนึงให้ชัวร์ว่าเกมรับคำสั่ง)
        pydirectinput.mouseDown()
        time.sleep(0.05) 
        pydirectinput.mouseUp()
        
        # 4. รอให้หิมะแตกเสี้ยววินาที ก่อนวิ่งไปก้อนต่อไป
        time.sleep(0.02)

    def _locate(self, ss, path, conf, gray=True):
        if not HAS_LIBS: return None
        try: return pyautogui.locate(path, ss, confidence=conf, grayscale=gray)
        except Exception as e: self.log(f"⚠️ locate {path}: {e}"); return None

    def _locate_all(self, ss, path, conf, gray=False):
        if not HAS_LIBS: return []
        try: return list(pyautogui.locateAll(path, ss, confidence=conf, grayscale=gray))
        except Exception as e: self.log(f"⚠️ locateAll {path}: {e}"); return []

    def _click_all_snow(self, buttons):
        unique = []; seen = []
        for btn in buttons:
            cx, cy = pyautogui.center(btn)
            if not any(abs(cx-sx) < self.GRID and abs(cy-sy) < self.GRID for sx, sy in seen):
                unique.append(btn); seen.append((cx, cy))
        unique.sort(key=lambda b: (self._snap(pyautogui.center(b).x),self._snap(pyautogui.center(b).y))) #yx เรียงซ้ายไปขวา  xy เรียงขวาไปซ้าย
        clicked = 0
        for btn in unique:
            cx, cy = pyautogui.center(btn)
            if self._already(cx, cy): continue
            self._click(cx, cy); self._mark(cx, cy); clicked += 1
        return clicked

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _run(self):
        cfg = self.cfg; self.start_time = time.time()
        self.log("❄️ เริ่ม Snow bot...")
        notfind = 0
        while not self._stop.is_set():
            self._tick()
            if not HAS_LIBS:
                time.sleep(1); self.log("❄️ [Demo] ปั่นหิมะ...")
                self.rounds += 1; self.stat("rounds", str(self.rounds)); time.sleep(2); continue
            try:
                reg = cfg.get("region")
                ss = pyautogui.screenshot(region=reg) if reg else pyautogui.screenshot()

                # หิมะ — priority สูงสุด
                snow_btns = self._locate_all(ss, cfg["snow_image"], 0.72, gray=True)
                if snow_btns:
                    pending = [b for b in snow_btns if not self._already(*pyautogui.center(b))]
                    if pending:
                        n = self._click_all_snow(pending)
                        if n > 0:
                            self.stat("snow", str(n))
                            self.log(f"❄️ กด {n} จุด")
                            t0 = time.time()
                            while time.time() - t0 < 0.5 and not self._stop.is_set():
                                chk = pyautogui.screenshot(region=reg) if reg else pyautogui.screenshot()
                                rem = [r for r in self._locate_all(chk, cfg["snow_image"], 0.65, gray=True)
                                       if not self._already(*pyautogui.center(r))]
                                if not rem: break
                                # time.sleep(0.05)
                            self._clicked.clear()
                            notfind = 0
                    continue

                # start
                b = self._locate(ss, cfg["start_image"], 0.6)
                if b:
                    cx, cy = pyautogui.center(b)
                    self.log(f"▶ start ({cx},{cy})")
                    self._click(cx, cy); self._clicked.clear(); notfind = 0; continue

                # confirm
                b = self._locate(ss, cfg["start2_image"], 0.8)
                if b:
                    cx, cy = pyautogui.center(b)
                    self.log(f"▶ confirm ({cx},{cy})")
                    self._click(cx, cy); self._clicked.clear(); notfind = 0; continue

                # end
                found_end = False
                for ekey in ("end_image", "end_image2", "end_image3"):
                    # 🚨 แก้ตรงนี้: ดัน confidence ขึ้นเป็น 0.85 และปิด gray=False ให้มันเช็คสีและรูปทรงแบบเป๊ะๆ
                    b = self._locate(ss, cfg[ekey], 0.85, gray=False) 
                    if b:
                        cx, cy = pyautogui.center(b)
                        self.log(f"✅ end ({cx},{cy})")
                        time.sleep(0.5) 
                        self._click(cx, cy)
                        time.sleep(0.1)
                        self._click(cx, cy)
                        self.rounds += 1; self.stat("rounds", str(self.rounds))
                        self._clicked.clear(); found_end = True; break
                        
                if not found_end:
                    time.sleep(0.05)
                    notfind += 1
                    if notfind % 10 == 0: self.log(f"🔍 หาไม่เจอ ({notfind})")
                    if notfind >= 100:
                        self.log("⚠️ หาไม่เจอ 100 รอบ → กด back")
                        b_back = self._locate(ss, cfg.get("back_image"), 0.75)
                        if b_back:
                            cx, cy = pyautogui.center(b_back)
                            self._click(cx, cy)
                            self.log(f"◀ กด back ({cx},{cy})")
                        else:
                            self.log("◀ หา back ไม่เจอด้วย")
                        self._clicked.clear(); notfind = 0
                else:
                    notfind = 0

            except Exception as e:
                self.log(f"⚠️ error: {e}"); time.sleep(0.5)

        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()