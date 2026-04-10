import pyautogui
import os
import time

# --- 設定區 ---
# 格式: (中心X, 中心Y, 寬度, 高度)
ORDER_SIZE = {
    "height": 150,
    "width": 180
}

CUSTOMER_CONFIGS = {
    "customer1": (841, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
    "customer2": (1253, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
    "customer3": (1669, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
    "customer4": (2089, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
    "customer5": (2500, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
    "customer6": (2914, 414, ORDER_SIZE["width"], ORDER_SIZE["height"]),
}

# 圖片資料夾路徑
ORDERS_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "orders_image")

# 自動載入資料夾內所有 .png 作為訂單圖庫
# 檔名（不含副檔名）即為料理名稱，例如 gunkan_maki.png -> "gunkan_maki"
ORDER_IMAGES = {
    os.path.splitext(f)[0]: os.path.join(ORDERS_IMAGE_DIR, f)
    for f in os.listdir(ORDERS_IMAGE_DIR)
    if f.endswith(".png")
}

def get_region(cx, cy, w, h):
    """將中心點座標轉換為 pyautogui region 格式 (left, top, width, height)"""
    return (int(cx - w / 2), int(cy - h / 2), int(w), int(h))

def check_all_orders(confidence=0.8):
    """
    偵測所有顧客的訂單。
    回傳格式: {"customer1": "gunkan_maki", "customer2": None, ...}
    None 表示該座位無法辨識訂單。
    """
    total_start = time.perf_counter()
    results = {}
    for seat, (cx, cy, w, h) in CUSTOMER_CONFIGS.items():
        region = get_region(cx, cy, w, h)
        results[seat] = None
        seat_start = time.perf_counter()
        for recipe_name, img_path in ORDER_IMAGES.items():
            try:
                match = pyautogui.locateOnScreen(img_path, region=region, confidence=confidence)
                if match:
                    results[seat] = recipe_name
                    break
            except pyautogui.ImageNotFoundException:
                continue
        seat_elapsed = time.perf_counter() - seat_start
        print(f"  [{seat}] {results[seat] or '無訂單':>15}  ({seat_elapsed:.3f}s)")
    total_elapsed = time.perf_counter() - total_start
    print(f"  總計耗時: {total_elapsed:.3f}s")
    return results

if __name__ == "__main__":
    orders = check_all_orders()
    for seat, recipe in orders.items():
        if recipe:
            print(f"{seat}: {recipe}")
        else:
            print(f"{seat}: 無訂單 / 無法辨識")
