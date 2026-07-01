# main.py
import cv2, time, multiprocessing, threading, asyncio
import numpy as np
from ultralytics import YOLO
import config
from api_client import CampusAI

# ==========================================
# 語音進程 (拔除嗶嗶聲，專注於極速人聲)
# ==========================================
def voice_worker(q):
    import win32com.client, pythoncom
    pythoncom.CoInitialize()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Rate = 2 # 稍微加快語速
    
    while True:
        try:
            text = q.get()
            if text == "STOP": break
            
            # 清洗舊隊列，只唸最新的危險
            while q.qsize() > 0: 
                old_text = q.get()
            speaker.Speak(text, 0)
        except: pass

def api_task_for_signals(api, frame, n_zh, pos, dist, v_q):
    async def run():
        resp = await api.verify_object(frame, n_zh, pos, dist)
        print(f"🚥 號誌指引：{resp}")
        v_q.put(resp)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())

def run_vision_agent(v_q):
    print("系統啟動")
    model_coco = YOLO(config.MODEL_COCO)
    model_custom = YOLO(config.MODEL_CUSTOM)
    ai_client = CampusAI(config.API_KEY, config.BASE_URL)

    cap = cv2.VideoCapture(config.TEST_VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_MSEC, config.START_SECOND * 1000)
    end_ms = (config.START_SECOND + config.DURATION) * 1000
    
    real_start_time = time.time()
    last_seen = {}

    while cap.isOpened():
        curr_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        real_elap = time.time() - real_start_time
        if curr_ms >= end_ms or real_elap >= config.DURATION: break

        ret, frame = cap.read()
        if not ret: break

        video_sec = (curr_ms - config.START_SECOND * 1000) / 1000.0
        if video_sec > real_elap: time.sleep(video_sec - real_elap)

        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % config.DETECT_INTERVAL == 0:
            current_sec = curr_ms / 1000.0
            
            res_coco = model_coco(frame, verbose=False, conf=0.25, imgsz=config.IMG_SIZE)
            res_custom = model_custom(frame, verbose=False, conf=0.25, imgsz=config.IMG_SIZE)
            
            f_w = frame.shape[1]
            temp_hits = []
            
            for r in [res_custom[0], res_coco[0]]:
                is_c = (r == res_custom[0])
                for b in r.boxes:
                    n = (model_custom if is_c else model_coco).names[int(b.cls[0])]
                    conf = float(b.conf[0])
                    if conf < config.CONF_THRESHOLDS.get(n, 0.30): continue
                    if is_c or n in config.STREET_CLASSES:
                        temp_hits.append({'box': b, 'name': n, 'is_c': is_c, 'conf': conf})

            valid_targets = []
            for h in temp_hits:
                n_en = h['name']
                if n_en not in config.OBJECT_HEIGHTS: continue
                c = h['box'].xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, c)
                cx = (x1 + x2) / 2
                
                box_height = max(y2 - y1, 1)
                dist = round((config.FOCAL_LENGTH * config.OBJECT_HEIGHTS[n_en]) / box_height, 2)
                
                # 方位字眼縮短，讓語音更洗鍊 (例如：左前方 -> 左前)
                pos = "左前" if cx < f_w * config.CENTER_ZONE_LEFT else "右前" if cx > f_w * config.CENTER_ZONE_RIGHT else "正前"
                valid_targets.append({'name': n_en, 'zh': config.LABEL_MAP.get(n_en, n_en), 'pos': pos, 'dist': dist, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'is_c': h['is_c']})

            valid_targets.sort(key=lambda x: x['dist'])

            for target in valid_targets:
                n_en, n_zh, pos, dist = target['name'], target['zh'], target['pos'], target['dist']
                
                weight = max(0.1, config.THREAT_WEIGHTS.get(n_en, 1.0))
                danger_score = dist / weight
                
                if danger_score < 3.8:
                    cool_key = f"{pos}_{n_en}"
                    
                    if cool_key not in last_seen or (current_sec - last_seen[cool_key] > 5.0):
                        last_seen[cool_key] = current_sec
                        
                        if n_en == "traffic light":
                            threading.Thread(target=api_task_for_signals, args=(ai_client, frame.copy(), n_zh, pos, dist, v_q)).start()
                        
                        # 💡 靜態物品：改為極簡微語音
                        elif n_en in config.STATIC_CLASSES:
                            if dist < 1.2:
                                # 太近了，加兩個字提醒
                                warning_msg = f"小心{pos}{n_zh}" 
                            else:
                                # 正常距離，只報方位跟物品，4個字解決
                                warning_msg = f"{pos}{n_zh}" 
                                
                            print(f"[{current_sec:.1f}s] 🔊 靜態提示：{warning_msg} ({dist}m)")
                            v_q.put(warning_msg)
                        
                        # 💡 動態危險物：維持緊急避讓指令
                        elif n_en in config.DYNAMIC_CLASSES:
                            avoid_action = "靠右" if "左" in pos else "靠左"
                            if "正前" in pos: avoid_action = "繞開"
                            
                            if dist > 2.5:
                                warning_msg = f"{pos}有{n_zh}" 
                            elif dist > 1.2:
                                warning_msg = f"{pos}{n_zh}，請{avoid_action}" 
                            else:
                                warning_msg = f"危險！立即{avoid_action}！" 

                            print(f"[{current_sec:.1f}s] 🚨 動態預警：{warning_msg} ({dist}m)")
                            v_q.put(warning_msg) 

                color = (0, 0, 255) if target['is_c'] else (255, 0, 0)
                cv2.rectangle(frame, (target['x1'], target['y1']), (target['x2'], target['y2']), color, 2)
                cv2.putText(frame, f"{n_en} {dist}m", (target['x1'], target['y1'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            cv2.imshow("VisionAgent PRO", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
    v_q.put("STOP")

if __name__ == "__main__":
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=voice_worker, args=(q,))
    p.start()
    try: run_vision_agent(q)
    except KeyboardInterrupt: pass
    finally: p.terminate()