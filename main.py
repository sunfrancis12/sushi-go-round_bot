import pyautogui

# 在你的主迴圈中
def check_plates():
    # 使用 tolerance 容許些微的顏色偏移
    if pyautogui.pixelMatchesColor(500, 600, (255, 255, 255), tolerance=10):
        print("發現盤子！點擊收盤...")
        pyautogui.click(500, 600)

# 定義配方座標
RECIPES = {
    "salmon_roll": [(400, 300), (450, 300), (500, 300)] # 飯, 海苔, 魚
}

def make_sushi(name):
    for coord in RECIPES[name]:
        pyautogui.click(coord)
        pyautogui.sleep(0.1) # 稍微停頓模擬真人操作