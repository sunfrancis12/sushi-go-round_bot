import pyautogui
import threading
import time
from vision import check_all_orders, check_game_finished as _vision_check_game_finished, check_single_seat

# 定義食材座標
INGREDIENTS = {
 "shirmp": (758, 1499),
 "rice": (995, 1504),
 "nori": (754, 1722),
 "fishegg": (981, 1730),
 "salmon": (752, 1960),
 "unagi": (981, 1960)
}

# Button region
# (1930, 1680) Continue
# (1462, 617) (2376, 721) WIN
# (1297, 699) (2544, 816) Fail

# 定義工作臺座標
WORKSTATIONS = (1442, 1714)

#定義盤子座標
PLATES = {
    "plate1": (937, 992),
    "plate2": (1356, 989),
    "plate3": (1795, 990),
    "plate4": (2195, 992),
    "plate5": (2606, 991),
    "plate6": (3024, 987)
}

#定義客人餐點座標
CUSTOMERS = {
    "customer1": (841, 415),
    "customer2": (1253, 418),
    "customer3": (1669, 414),
    "customer4": (2089, 407),
    "customer5": (2500, 412),
    "customer6": (2914, 413)
}

#定義桌子顏色 (判定是否有盤子)
TABLE_COLOR = (238, 219, 169)  # 桌子顏色

# 定義配方座標
RECIPES = {
    "onigiri": [INGREDIENTS["rice"], INGREDIENTS["rice"], INGREDIENTS["nori"]], # 飯, 飯,海苔
    "california_roll": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["fishegg"]], # 飯, 海苔, 魚卵
    "gunkan_maki": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["fishegg"], INGREDIENTS["fishegg"]], # 飯, 海苔, 魚卵, 魚卵
    "salmon_shushi": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["salmon"], INGREDIENTS["salmon"]], # 飯, 海苔, 鮭魚, 鮭魚
    "shrimp_shushi": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["shirmp"], INGREDIENTS["shirmp"]], # 飯, 海苔, 蝦, 蝦
    "unagi_shushi": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["unagi"], INGREDIENTS["unagi"]] # 飯, 海苔, 鰻魚, 鰻魚
}

# 定義食材捕貨座標
RESTOCK_INGREDIENTS = {
 "shirmp": (2628, 1047),
 "rice": (2838, 1282),
 "nori": (2623, 1273),
 "fishegg": (2967, 1278),
 "salmon": (2628, 1502),
 "unagi": (2968, 1050)
}

RESTOCK_ITEMS = {
 "Telephone": (2997, 1603),
 "Topping": (2731, 1251),
 "Rice": (2772, 1337),
 "DELIVERY": (2616, 1339) # 只用免費的
}

# 初始食材數量
INITIAL_STOCK = {
    "shirmp":   5,
    "rice":    10,
    "nori":    10,
    "fishegg": 10,
    "salmon":   5,
    "unagi":    5,
}

# 每次補貨補充的數量（補貨後 6.5 秒才到貨）
RESTOCK_AMOUNTS = {
    "shirmp":   5,
    "rice":    10,
    "nori":    10,
    "fishegg": 10,
    "salmon":   5,
    "unagi":    5,
}

RESTOCK_DELAY = 6.5  # 補貨延遲秒數

# 目前庫存（執行時動態變化）
inventory = dict(INITIAL_STOCK)

# 目前偵測到的顧客訂單
current_orders = {}

# 每個顧客的訂單狀態（待處理 / 製作中 / 已送出 / 完成）
order_status = {}

# 自動遊玩旗標
_auto_play_running = False

# 正在補貨中的食材集合（避免重複補貨）
_restocking = set()

def detect_orders(confidence=0.8):
    """偵測所有顧客訂單並更新 current_orders"""
    global current_orders
    print("[訂單偵測] 掃描中...")
    current_orders = check_all_orders(confidence)
    return current_orders

# 每道壽司消耗的食材數量
RECIPE_INGREDIENTS = {
    "onigiri":         {"rice": 2, "nori": 1},
    "california_roll": {"rice": 1, "nori": 1, "fishegg": 1},
    "gunkan_maki":     {"rice": 1, "nori": 1, "fishegg": 2},
    "salmon_shushi":   {"rice": 1, "nori": 1, "salmon": 2},
    "shrimp_shushi":   {"rice": 1, "nori": 1, "shirmp": 2},
    "unagi_shushi":    {"rice": 1, "nori": 1, "unagi": 2},
}


def has_enough_ingredients(recipe_name):
    needed = RECIPE_INGREDIENTS.get(recipe_name, {})
    for ingredient, amount in needed.items():
        if inventory.get(ingredient, 0) < amount:
            print(f"食材不足：{ingredient}（需要 {amount}，剩餘 {inventory.get(ingredient, 0)}）")
            return False
    return True

# 回傳目前庫存能製作的料理清單
def get_makeable_recipes(order_list):
    """
    從傳入的 order_list 中篩選出目前庫存足夠製作的料理。
    order_list: list of recipe name strings，例如 ["gunkan_maki", "onigiri"]
    回傳: 可製作的料理名稱 list
    """
    return [name for name in order_list if has_enough_ingredients(name)]

# 製作壽司後扣除食材
def consume_ingredients(recipe_name):
    needed = RECIPE_INGREDIENTS.get(recipe_name, {})
    for ingredient, amount in needed.items():
        inventory[ingredient] -= amount
    print_inventory()

# 補貨到貨後更新庫存（由 Timer 呼叫）
def _apply_restock(name, amount):
    inventory[name] += amount
    _restocking.discard(name)
    print(f"[補貨到貨] {name} +{amount}，目前庫存：{inventory[name]}")

# 印出目前所有食材庫存
def print_inventory():
    print("=== 目前食材庫存 ===")
    for name, amount in inventory.items():
        print(f"  {name:>10}: {amount}")
    print("===================")

# 檢查盤子是否存在
def check_plates():
    for plate, coord in PLATES.items():
        #直接點擊
        pyautogui.click(coord)
        # # 使用 tolerance 容許些微的顏色偏移
        # if not pyautogui.pixelMatchesColor(coord[0], coord[1], TABLE_COLOR, tolerance=10):
        #     print(f"發現盤子！點擊收盤 {plate}...")
        #     pyautogui.click(coord)

# 製作壽司
def make_sushi(name):
    if not has_enough_ingredients(name):
        print(f"食材不足，無法製作 {name}")
        return False
    for coord in RECIPES[name]:
        pyautogui.click(coord)
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
    pyautogui.click(WORKSTATIONS) # 點擊工作臺開始製作
    consume_ingredients(name)
    pyautogui.sleep(1.0)  # 等待遊戲動畫完成
    return True

# 食材補貨
def restock_ingredients(name):
    if name in _restocking:
        print(f"[補貨] {name} 已在補貨中，略過...")
        return
    if name in RESTOCK_INGREDIENTS:
        print(f"正在補貨 {name}...")
        pyautogui.click(RESTOCK_ITEMS["Telephone"]) # 點擊電話
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
        
        if name == "rice": #單獨處理米飯
            pyautogui.click(RESTOCK_ITEMS["Rice"]) # 點擊米飯
        else:
            pyautogui.click(RESTOCK_ITEMS["Topping"]) # 點擊配料
        
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
        pyautogui.click(RESTOCK_INGREDIENTS[name]) #選取食材
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
        pyautogui.click(RESTOCK_ITEMS["DELIVERY"]) # 點擊送貨

        # 6.5 秒後自動更新庫存
        amount = RESTOCK_AMOUNTS.get(name, 0)
        if amount > 0:
            _restocking.add(name)
            threading.Timer(RESTOCK_DELAY, _apply_restock, args=(name, amount)).start()
            print(f"[補貨中] {name} 將在 {RESTOCK_DELAY} 秒後到貨")
    else:
        print(f"沒有找到 {name} 的補貨座標！")

def check_game_finished(confidence=0.8):
    """偵測關卡是否通關"""
    global game_result
    print("[關卡通過偵測] 掃描中...")
    game_result = _vision_check_game_finished(confidence)
    if game_result == 0:
        print("關卡尚未結束，繼續遊戲...")
    elif game_result == 1:
        print("恭喜！關卡已通過！")
        pyautogui.sleep(3) # 停頓
        pyautogui.click(1930, 1680)  # 點擊 Continue
        # pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
        # pyautogui.click(1930, 1680)  # 點擊 Continue
    elif game_result == 2:
        print("很遺憾，關卡失敗！")
        pyautogui.sleep(3) # 停頓
        pyautogui.click(1930, 1680)  # 點擊 Continue
        # pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
        # pyautogui.click(1930, 1680)  # 點擊 Continue
    return game_result

# 客人座位的順序（輸送帶方向）
SEAT_ORDER = ["customer1", "customer2", "customer3", "customer4", "customer5", "customer6"]


def rescan_earlier_seats(target_seat, recipe):
    """
    在為 target_seat 製作壽司前，補掃所有排在它之前且無待處理訂單的座位。
    若發現前面座位有相同訂單，立刻將其加入 order_status 並回傳 True（表示有插隊情況）。
    """
    target_idx = SEAT_ORDER.index(target_seat)
    found = False
    for seat in SEAT_ORDER[:target_idx]:
        status = order_status.get(seat, {}).get("status")
        if status in ("待處理", "製作中", "已送出"):
            continue  # 已有進行中訂單，跳過
        detected = check_single_seat(seat)
        if detected:
            print(f"[補掃] 發現 {seat} 有訂單：{detected}，加入處理佇列")
            order_status[seat] = {"order": detected, "status": "待處理"}
            if detected == recipe:
                found = True  # 前面有人要同樣的菜，需優先處理
    return found


def calc_required_ingredients(pending_orders):
    """計算所有待處理訂單合計需要的食材數量"""
    required = {}
    for recipe in pending_orders:
        for ingredient, amount in RECIPE_INGREDIENTS.get(recipe, {}).items():
            required[ingredient] = required.get(ingredient, 0) + amount
    return required


def restock_shortfall(required):
    """依合計需求與目前庫存之差，補足不夠的食材（每種只補一次）"""
    for ingredient, needed in required.items():
        shortage = needed - inventory.get(ingredient, 0)
        if shortage > 0:
            restock_ingredients(ingredient)
            time.sleep(0.3)


def auto_play_loop():
    global _auto_play_running, current_orders, order_status
    SCAN_INTERVAL = 10
    last_scan_time = 0
    print("[自動遊玩] 開始！")

    while _auto_play_running:
        now = time.time()

        # 每 10 秒：收盤子 + 掃描訂單 + 預先補貨
        if now - last_scan_time >= SCAN_INTERVAL:

            # 2. 掃描訂單
            print("[自動遊玩] 掃描訂單...")
            detect_orders()
            last_scan_time = time.time()

            # 更新訂單狀態
            for seat, order in current_orders.items():
                prev = order_status.get(seat, {})
                if order:
                    if prev.get("order") != order:
                        order_status[seat] = {"order": order, "status": "待處理"}
                else:
                    # 只有已送出壽司後掃不到訂單，才算真正完成
                    # 若狀態為「待處理」或「製作中」掃不到，視為辨識失敗，保留原狀態
                    if prev.get("status") == "已送出":
                        order_status[seat] = {"order": None, "status": "完成"}

            # 3. 統計所有待處理訂單需要的食材，不足則補貨
            pending = [info["order"] for info in order_status.values()
                       if info.get("status") == "待處理" and info.get("order")]
            if pending:
                required = calc_required_ingredients(pending)
                print(f"[自動遊玩] 待處理訂單需求：{required}")
                restock_shortfall(required)
            
            # 1. 收盤子
            print("[自動遊玩] 收盤子...")
            check_plates()
            
            # 5. 偵測關卡結果
            if check_game_finished() != 0:
                _auto_play_running = False
                break

        # 4. 製作壽司（依座位順序，食材足夠才做；製作前先補掃前方座位）
        for seat in SEAT_ORDER:
            if not _auto_play_running:
                break
            info = order_status.get(seat, {})
            if info.get("status") != "待處理":
                continue
            recipe = info["order"]
            if recipe not in RECIPES:
                continue
            # 補掃前方座位，若有人要同樣的菜則讓迴圈從頭來一次處理前面的人
            if rescan_earlier_seats(seat, recipe):
                print(f"[衝突] {seat} 前方有相同訂單，優先處理前方座位")
                break  # 下一輪迴圈會從 SEAT_ORDER 頭開始，先處理前面的座位
            if has_enough_ingredients(recipe):
                order_status[seat]["status"] = "製作中"
                print(f"[自動遊玩] 為 {seat} 製作 {recipe}...")
                make_sushi(recipe)
                order_status[seat]["status"] = "已送出"

        time.sleep(0.5)

    print("[自動遊玩] 結束！")


def start_auto_play():
    global _auto_play_running
    if not _auto_play_running:
        _auto_play_running = True
        threading.Thread(target=auto_play_loop, daemon=True).start()


def stop_auto_play():
    global _auto_play_running
    _auto_play_running = False


def reset_game():
    """重置所有遊戲狀態（庫存、訂單、補貨追蹤）"""
    global inventory, current_orders, order_status, _restocking
    stop_auto_play()
    inventory = dict(INITIAL_STOCK)
    current_orders = {}
    order_status = {}
    _restocking = set()
    print("[重置] 遊戲狀態已全部重置！")
    print_inventory()


if __name__ == "__main__":
    print_inventory()  # 顯示初始庫存
    #restock_ingredients("fishegg")  # 測試補貨米飯
    make_sushi("gunkan_maki")  # 測試製作飯糰
    # while True:
    #     check_plates()
    #     # 這裡可以加入更多邏輯來決定要做哪種壽司
    #     # 例如根據客人點的菜單來決定配方