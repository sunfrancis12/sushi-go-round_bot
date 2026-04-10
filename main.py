import pyautogui
import threading
from vision import check_all_orders

# 定義食材座標
INGREDIENTS = {
 "shirmp": (758, 1499),
 "rice": (995, 1504),
 "nori": (754, 1722),
 "fishegg": (981, 1730),
 "salmon": (752, 1960),
 "unagi": (981, 1960)
}

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
            threading.Timer(RESTOCK_DELAY, _apply_restock, args=(name, amount)).start()
            print(f"[補貨中] {name} 將在 {RESTOCK_DELAY} 秒後到貨")
    else:
        print(f"沒有找到 {name} 的補貨座標！")


if __name__ == "__main__":
    print_inventory()  # 顯示初始庫存
    #restock_ingredients("fishegg")  # 測試補貨米飯
    make_sushi("gunkan_maki")  # 測試製作飯糰
    # while True:
    #     check_plates()
    #     # 這裡可以加入更多邏輯來決定要做哪種壽司
    #     # 例如根據客人點的菜單來決定配方