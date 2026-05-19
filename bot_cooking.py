"""
bot_cooking.py — CookingBot
mode = "safe"  : กด cook1 แค่ครั้งเดียวต่อรอบ
mode = "multi" : กด cook1 ทุกครั้งที่โผล่ใหม่ รอให้หายก่อนหาใหม่ จนเจอ endcook
queue          : menu_queue = [{"name":..., "image":...}, ...]
                 index 0 = เมนูล่าสุด (ไม่ต้องคลิก)
                 index 1+ = คลิกในหน้าสูตรอาหารเมื่อวัตถุดิบหมด (end_image)
"""
import threading, time

try:
    import pyautogui, pydirectinput
    HAS_LIBS = True
    
    pyautogui.PAUSE = 0.0
    pydirectinput.PAUSE = 0.0
except ImportError:
    HAS_LIBS = False

RETRY_AFTER = 4.0   # ลดจาก 10.0 → กด retry endcook ถ้ายังไม่หายหลัง N วิ

# ── cooldown แต่ละปุ่ม (วินาที) ──────────────────────────────────────────────
# ป้องกันกดซ้ำก่อนที่ปุ่มจะหายจากหน้าจอจริงๆ
COOLDOWN = {
    "s":  1.5,   # start
    "s2": 1.0,   # start2
    "c1": 0.1,   # cook1
    "ec": 10.0,   # endcook
}


class CookingBot:
    def __init__(self, cfg, log, stat):
        self.cfg = cfg; self.log = log; self.stat = stat
        self._stop = threading.Event()
        self.cooked = 0; self.start_time = None

    def _locate(self, ss, path, conf, gray=True):
        if not HAS_LIBS or not path: return None
        try: return pyautogui.locate(path, ss, confidence=conf, grayscale=gray)
        except: return None

    def _locatecommon(self, ss, path, conf, gray=True):
        try: return pyautogui.locate(path, ss, confidence=conf, grayscale=gray)
        except: return None

    def _click(self, pt, px, py):
        # ดึงพิกัด x, y ที่ AI หาเจอ (ซึ่งเป็นพิกัดอิงจากภาพที่ถูกตัดขอบแล้ว)
        x, y = pt.x, pt.y
        
        # ถ้ามีการกำหนดโซนหน้าจอ (หั่นขอบ) ให้บวกพิกัด x, y กลับไปที่หน้าจอหลัก
        if hasattr(self, "active_region") and self.active_region:
            x += self.active_region[0]
            y += self.active_region[1]
            
        # เลื่อนเมาส์ไปที่เป้าหมาย (ใช้เวลา 0.1 วิ)
        pyautogui.moveTo(x, y, duration=0.1)
        
        # สั่งคลิก โดยมีการหน่วงเวลาตอนกดเมาส์ลงเล็กน้อย ป้องกันเกมรันคำสั่งไม่ทัน
        pydirectinput.mouseDown()
        time.sleep(0.1) 
        pydirectinput.mouseUp()
        time.sleep(0.05)
        
        # ขยับเมาส์หลบไปที่พิกัด (px, py) เพื่อไม่ให้มีหลอดหรือข้อความ Tooltip เด้งมาบังจอ
        pydirectinput.moveTo(px, py)

    def _tick(self):
        e = int(time.time() - self.start_time)
        self.stat("time", f"{e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d}")

    def _reset_visible(self):
        return {"s": False, "s2": False, "c1": False, "ec": False}

    def _reset_last_click(self):
        return {"s": 0.0, "s2": 0.0, "c1": 0.0, "ec": 0.0}

    def _can_click(self, key, last):
        """กดได้ก็ต่อเมื่อผ่าน cooldown แล้วเท่านั้น"""
        return (time.time() - last[key]) >= COOLDOWN[key]

    def _should_click(self, key, vis, last):
        """กดได้ถ้า: โผล่ใหม่ หรือ กดแล้วไม่หายเกิน RETRY_AFTER วิ
           และ ผ่าน cooldown แล้ว (ป้องกันกดซ้ำทันที)"""
        passed_cooldown = self._can_click(key, last)
        is_new          = not vis[key]
        is_stuck        = (time.time() - last[key]) >= RETRY_AFTER
        return passed_cooldown and (is_new or is_stuck)
    
    def _run(self):
        cfg = self.cfg; self.start_time = time.time()
        mode       = cfg.get("mode", "safe")
        menu_queue = list(cfg.get("menu_queue", []))
        q_idx      = 0

        self.log(f"🍳 เริ่ม cooking bot... mode={mode}  queue={len(menu_queue)} เมนู")

        cook = check2 = check3 = check4 = notfind = start2_count = 0
        px, py = 10, 10
        vis  = self._reset_visible()
        last = self._reset_last_click()

        while not self._stop.is_set():
            self._tick()

            if not HAS_LIBS:
                time.sleep(1); self.log("🍳 [Demo] cook...")
                self.cooked += 1; self.stat("count", str(self.cooked)); time.sleep(2); continue

            try:
                # --- แก้เป็น 2 บรรทัดนี้ ---
                # ---- 🎯 โซนจับภาพตรงกลางถึงขวาล่าง ----
                reg = cfg.get("region")
                if reg:
                    # ตัดขอบซ้าย 15% และขอบบน 15% ทิ้งไป
                    # แต่เอาความกว้าง 85% และสูง 85% (ลากยาวจนสุดขอบขวาล่าง)
                    w = int(reg[2] * 0.85)
                    h = int(reg[3] * 0.85)
                    x = reg[0] + int(reg[2] * 0.15)
                    y = reg[1] + int(reg[3] * 0.15)
                    self.active_region = (x, y, w, h)
                else:
                    sw, sh = pyautogui.size()
                    w, h = int(sw * 0.85), int(sh * 0.85)
                    x, y = int(sw * 0.15), int(sh * 0.15)
                    self.active_region = (x, y, w, h)

                ss = pyautogui.screenshot(region=self.active_region)
                # ------------------------------------
                b_s  = self._locate(ss, cfg["start_image"],   0.6)
                b_s2 = self._locate(ss, cfg["start2_image"],  0.8)
                b_c1 = self._locate(ss, cfg["cook1_image"],   0.6, gray=True)
                b_ec = self._locate(ss, cfg["endcook_image"], 0.8)
                b_e  = self._locate(ss, cfg["end_image"],     0.9) if start2_count >= 1 else None

                new_vis = {
                    "s":  b_s  is not None,
                    "s2": b_s2 is not None,
                    "c1": b_c1 is not None,
                    "ec": b_ec is not None,
                }
                
                if cook == 1 :
                    # ── กด cook1 ─────────────────────────────────────────────────
                    if b_c1:
                        if mode == "safe":
                            # แก้: แทน not vis["c1"] ด้วย _can_click
                            if check3 == 0 and self._can_click("c1", last):
                                pt = pyautogui.center(b_c1)
                                self.log(f"🍳 cook1 safe ({pt.x},{pt.y})")
                                self._click(pt, px, py); check3 += 1; start2_count = 0; notfind = 0 ;check4 = 1
                                last["c1"] = time.time()
                        else:
                            # เปลี่ยนจาก _can_click เป็น _should_click 
                            # เพื่อดักว่าต้องเป็น "ปุ่มก้อนใหม่ที่เพิ่งโผล่มา" เท่านั้นถึงจะกด
                            if self._should_click("c1", vis, last):
                                pt = pyautogui.center(b_c1)
                                self.log(f"🔥 cook1 multi ({pt.x},{pt.y})")
                                
                                gx, gy = pt.x, pt.y
                                if hasattr(self, "active_region") and self.active_region:
                                    gx += self.active_region[0]
                                    gy += self.active_region[1]
                                    
                                dodge_x = gx
                                dodge_y = gy + 60
                                
                                self._click(pt, dodge_x, dodge_y)
                                
                                start2_count = 0 ;check4 = 1
                                notfind = 0
                                last["c1"] = time.time()
                    # ── else: ไม่เจอ cook1 ───────────────────────────────────────
                    elif b_ec and self._should_click("ec", vis, last):
                            pt = pyautogui.center(b_ec)
                            retry = " (retry)" if vis["ec"] else ""
                            self.log(f"✅ endcook{retry} ({pt.x},{pt.y})")
                            self._click(pt, px, py)
                            
                            # ✅ แก้ตรงนี้: รีเซ็ตเฉพาะตัวแปรลอจิกการทำอาหาร
                            cook = 0; check2 = 0; check3 = 0; start2_count = 0 
                            
                            # ✅ บันทึก "เวลาที่กดจริงๆ" จะได้ติด Cooldown อย่างถูกต้อง
                            last["ec"] = time.time()
                            
                            self.cooked += 1; self.stat("count", str(self.cooked))
     
                    # ── วัตถุดิบหมด → เปลี่ยนเมนูถัดไปใน queue ──────────────────
                    elif b_e and check4 == 0:
                        q_idx += 1
                        if q_idx >= len(menu_queue):
                            self.log("🏁 queue หมดแล้ว จบ!"); break
                        next_menu = menu_queue[q_idx]
                        self.log(f"📦 วัตถุดิบหมด → หาเมนู: {next_menu['name']}")
                        cook = check2 = check3 = notfind = start2_count = 0
                        vis = self._reset_visible(); last = self._reset_last_click()
                        while not self._stop.is_set():
                            ss2 = pyautogui.screenshot(region=getattr(self, "active_region", None))
                            if not next_menu.get("image"):
                                self.log("🍽 ใช้เมนูล่าสุดในเกม"); break
                            b_menu = self._locate(ss2, next_menu["image"], 0.80)
                            if b_menu:
                                pt = pyautogui.center(b_menu)
                                self._click(pt, px, py)
                                self.log(f"🍽 คลิกเมนู {next_menu['name']} ({pt.x},{pt.y})")
                                break
                            time.sleep(0.2)
                        vis = self._reset_visible(); last = self._reset_last_click()
                        continue
                       
                    elif not b_ec:
                        notfind += 1
                        if notfind % 10 == 0: self.log(f"🔍 หาไม่เจอ ({notfind})")
                        if notfind >= 300:
                            self.log("⚠️ หาไม่เจอ 100 รอบ → กด back")
                            b_back = self._locate(ss, cfg.get("back_image"), 0.75)
                            if b_back:
                                pt = pyautogui.center(b_back)
                                self._click(pt, px, py)
                                self.log(f"◀ กด back ({pt.x},{pt.y})")
                            else:
                                self.log("◀ หา back ไม่เจอด้วย")
                            
                            cook = check2 = check3 = notfind = start2_count = 0
                            # กรณีหาหน้าจอไม่เจอจนหลุดจริงๆ ค่อย reset state
                            vis = self._reset_visible(); last = self._reset_last_click()         
                        
                else:
                    # ── กด start ─────────────────────────────────────────────────
                    if b_s  and self._should_click("s", vis, last):
                        pt = pyautogui.center(b_s)
                        retry = " (retry)" if vis["s"] else ""
                        self.log(f"▶ start{retry} ({pt.x},{pt.y})")
                        
                        # 1. แปลงพิกัดปุ่มให้เป็นพิกัดบนจอจริง เพื่อใช้คำนวณจุดหลบเมาส์ (px, py)
                        gx, gy = pt.x, pt.y
                        if hasattr(self, "active_region") and self.active_region:
                            gx += self.active_region[0]
                            gy += self.active_region[1]
                            
                        px = gx + 150  # ให้เมาส์หลบไปทางขวา 150 px จากปุ่ม
                        py = gy
                        
                        # 2. ส่งให้ฟังก์ชัน _click จัดการแทน
                        self._click(pt, px, py)
                        
                        start2_count = 0
                        last["s"] = time.time()

                    # ── กด start2 ────────────────────────────────────────────────
                    # แก้: เพิ่ม _can_click แทน not vis["s2"] เพื่อป้องกันกดซ้ำทันที
                    elif b_s2  and check2 < 1 and self._can_click("s2", last):
                        pt = pyautogui.center(b_s2)
                        self.log(f"▶ start2 ({pt.x},{pt.y}) [{start2_count + 1}]")
                        self._click(pt, px, py); cook = 1; check3 = 0; check2 += 1 ;check4 = 0
                        start2_count += 1
                        last["s2"] = time.time()
                        
                    
                
                

                vis = new_vis

            except Exception as e:
                self.log(f"⚠️ error: {e}"); time.sleep(0.5)

        self.log("🛑 หยุดแล้ว")

    def start(self): self._stop.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self):  self._stop.set()