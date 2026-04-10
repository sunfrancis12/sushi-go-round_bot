import pyautogui

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
    "unagi_shushi": [INGREDIENTS["rice"], INGREDIENTS["nori"], INGREDIENTS["unagi"], INGREDIENTS["unagi"]] # 飯, 海苔, 海膽, 海膽
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

# 檢查盤子是否存在
def check_plates():
    for plate, coord in PLATES.items():
        # 使用 tolerance 容許些微的顏色偏移
        if not pyautogui.pixelMatchesColor(coord[0], coord[1], TABLE_COLOR, tolerance=10):
            print(f"發現盤子！點擊收盤 {plate}...")
            pyautogui.click(coord)

# 製作壽司
def make_sushi(name):
    for coord in RECIPES[name]:
        pyautogui.click(coord)
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作
    pyautogui.click(WORKSTATIONS) # 點擊工作臺開始製作

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
        
    else:
        print(f"沒有找到 {name} 的補貨座標！")


if __name__ == "__main__":
    #restock_ingredients("fishegg")  # 測試補貨米飯
    make_sushi("gunkan_maki")  # 測試製作飯糰
    # while True:
    #     check_plates()
    #     # 這裡可以加入更多邏輯來決定要做哪種壽司
    #     # 例如根據客人點的菜單來決定配方