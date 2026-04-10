import pyautogui
from pynput import keyboard
import os

print("=== 🍣 Sushi Go Round 開發輔助工具 ===")
print("操作說明：")
print("1. 將滑鼠移至遊戲中的目標（如食材、盤子、電話）")
print("2. 按下 'F1' 鍵紀錄座標與 RGB 顏色")
print("3. 按下 'Esc' 鍵結束程式並儲存紀錄")
print("-" * 30)

recorded_data = []

def on_press(key):
    if key == keyboard.Key.f1:
        # 獲取目前滑鼠座標
        x, y = pyautogui.position()
        # 獲取該點的 RGB 顏色
        color = pyautogui.pixel(x, y)
        
        info = f"座標: ({x}, {y}) | RGB 顏色: {color}"
        print(f"[已紀錄] {info}")
        recorded_data.append(info)

    if key == keyboard.Key.esc:
        print("\n正在停止程式...")
        return False

# 啟動監聽器
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

# 結束後將結果存檔，方便複製到你的主程式
if recorded_data:
    with open("game_coords.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(recorded_data))
    print(f"紀錄已存入 {os.path.abspath('game_coords.txt')}")