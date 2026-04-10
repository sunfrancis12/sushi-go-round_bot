import cv2
import numpy as np
import mss
import time
import easyocr

# --- 設定區 ---
# 格式: (中心X, 中心Y, 寬度, 高度)
RECEIPE_SIZE = {
    "height": 150,
    "width": 180
}

INGREDIENTS_SIZE = {
    "height": 180,
    "width": 180
}

MONITOR_CONFIGS = {
    "customer1": (841, 415, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "customer2": (1253, 418, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "customer3": (1669, 414, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "customer4": (2089, 407, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "customer5": (2500, 412, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "customer6": (2914, 413, RECEIPE_SIZE["width"], RECEIPE_SIZE["height"]),
    "shirmp": (758, 1499, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"]),
    "rice": (995, 1504, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"]),
    "nori": (754, 1722, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"]),
    "fishegg": (981, 1730, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"]),
    "salmon": (752, 1960, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"]),
    "unagi": (981, 1960, INGREDIENTS_SIZE["width"], INGREDIENTS_SIZE["height"])
}

INGREDIENT_NAMES = ["shirmp", "rice", "nori", "fishegg", "salmon", "unagi"]

# 初始化 EasyOCR（只載入一次，避免重複佔用記憶體）
ocr_reader = easyocr.Reader(['en'], gpu=False)

def get_mss_dict(cx, cy, w, h):
    """將中心點座標轉換為 mss 格式"""
    return {
        "left": int(cx - w / 2),
        "top": int(cy - h / 2),
        "width": int(w),
        "height": int(h)
    }

def get_ingredient_counts(sct):
    """
    使用 EasyOCR 讀取各食材的庫存數量。
    回傳格式: {"shirmp": 3, "rice": 5, ...}
    無法辨識時該食材數量為 -1。
    """
    counts = {}
    for name in INGREDIENT_NAMES:
        cx, cy, w, h = MONITOR_CONFIGS[name]
        region = get_mss_dict(cx, cy, w, h)
        img = np.array(sct.grab(region))
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 預處理：灰階 → 放大 3 倍 → Otsu 二值化（提升辨識率）
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        
        cv2.imwrite(f"debug_{name}.png", processed_bgr)  # 儲存預處理後的圖片以供調試
        results = ocr_reader.readtext(processed_bgr, allowlist='0123456789', detail=0, paragraph=False)
        text = ''.join(results).strip()
        try:
            counts[name] = int(text)
        except ValueError:
            counts[name] = -1  # 辨識失敗

    return counts

def start_visual_debug():
    with mss.mss() as sct:
        # 抓取第一個顯示器
        monitor = sct.monitors[1]
        
        # 建立視窗並命名，方便後續操作
        win_name = "Debug View (Press Q to Quit)"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL) 

        while True:
            # 截圖並轉換為 BGR
            img = np.array(sct.grab(monitor))
            display_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 讀取食材數量
            counts = get_ingredient_counts(sct)

            # 繪製紅框
            for name, (cx, cy, w, h) in MONITOR_CONFIGS.items():
                x1, y1 = int(cx - w/2), int(cy - h/2)
                x2, y2 = int(cx + w/2), int(cy + h/2)
                cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(display_img, name, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                # 若是食材區域，額外顯示辨識到的數量
                if name in counts:
                    count_text = str(counts[name]) if counts[name] != -1 else "?"
                    cv2.putText(display_img, count_text, (x1 + 5, y2 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

            # 顯示結果
            cv2.imshow(win_name, display_img)

            # 關鍵修改：等待 1 毫秒並抓取按鍵
            key = cv2.waitKey(1) & 0xFF
            
            # 1. 按下 Q 鍵退出
            # 2. 或者按下 Esc 鍵 (27)
            # 3. 或者點擊視窗右上角的 X (如果視窗屬性變為 -1)
            if key == ord('q') or key == 27 or cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # 徹底釋放資源
        cv2.destroyAllWindows()
        # 額外保險：在某些環境下需要多呼叫幾次 waitKey 來清空視窗隊列
        cv2.waitKey(1)

if __name__ == "__main__":
    start_visual_debug()