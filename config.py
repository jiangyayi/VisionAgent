# config.py
MODEL_COCO = "yolo11n.pt"
MODEL_CUSTOM = "best.pt"
DEVICE = "cpu"
IMG_SIZE = 416

API_KEY = "sk-dh9TO-SnswgOV8HZSlXOAQ"
BASE_URL = "https://api.ithu.tw/v1"

# --- 影片設定 ---
TEST_VIDEO_PATH = "assets/video/campus_test.mp4" 
START_SECOND = 30   
DURATION = 45
DETECT_INTERVAL = 4  # 啟用追蹤後，偵測頻率稍微加快

# --- 畫面區域判定 ---
CENTER_ZONE_LEFT = 0.42
CENTER_ZONE_RIGHT = 0.58

# --- 💡 智慧混合測距：相機參數與防低頭設定 ---
CAMERA_HEIGHT = 1.35      # 假設鏡頭佩戴在胸口高度 (公尺)
CAMERA_TILT_OFFSET = 60   # 若鏡頭微朝下，給予正數補償 (可依實際情況微調 30~80)
HORIZON_Y = (IMG_SIZE / 2) - CAMERA_TILT_OFFSET  # 校正後的地平線位置
FOCAL_LENGTH = 500

# --- 嚴格信心門檻防誤判 ---
CONF_THRESHOLDS = {
    "truck": 0.70,     
    "bus": 0.60,
    "upstair": 0.60,
    "Stairs": 0.60,
    "pothole": 0.40,
    "fire hydrant": 0.75  # 防消防栓幻覺
}

# --- 動靜態分類 ---
DYNAMIC_CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck", "dog", "cat"] 
STATIC_CLASSES = ["pothole", "upstair", "Stairs", "bollard", "bollard_abnormal", "traffic-cone", "bench", "potted plant", "fire hydrant", "chair", "suitcase"] 
STREET_CLASSES = DYNAMIC_CLASSES + STATIC_CLASSES + ["traffic light", "stop sign"]

LABEL_MAP = {
    "person": "行人", "bicycle": "腳踏車", "car": "汽車", "motorcycle": "機車",
    "bus": "公車", "truck": "貨車", "dog": "小狗", "cat": "小貓",
    "traffic light": "紅綠燈", "stop sign": "停車標誌", "fire hydrant": "消防栓",
    "bench": "長椅", "potted plant": "盆栽", "suitcase": "行李箱",
    "chair": "椅子", "couch": "沙發", "dining table": "桌子",
    "toilet": "馬桶", "sink": "洗手槽", "pothole": "坑洞",
    "upstair": "階梯", "Stairs": "階梯", "bollard_abnormal": "路樁",
    "bollard": "路樁", "traffic-cone": "三角錐", "tactile pavement": "導盲磚"
}

THREAT_WEIGHTS = { "truck": 1.5, "bus": 1.5, "motorcycle": 1.4, "car": 1.3, "pothole": 1.8, "upstair": 1.6, "Stairs": 1.6, "traffic light": 0.0 }
OBJECT_HEIGHTS = { "person": 1.7, "bicycle": 1.0, "car": 1.5, "motorcycle": 1.2, "bus": 3.0, "truck": 3.5, "dog": 0.5, "cat": 0.3, "potted plant": 0.6, "traffic light": 0.8, "stop sign": 2.5, "fire hydrant": 0.7, "bench": 0.5, "suitcase": 0.6, "chair": 0.9, "couch": 0.8, "dining table": 0.75, "toilet": 0.5, "sink": 0.8, "pothole": 0.25, "upstair": 1.2, "Stairs": 1.2, "bollard_abnormal": 0.8, "bollard": 0.8, "traffic-cone": 0.7, "tactile pavement": 0.1 }