import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
from pynput import keyboard

import main as game

# 顯示名稱對照表
RECIPE_DISPLAY_NAMES = {
    "onigiri":         "飯糰",
    "california_roll": "加州捲",
    "gunkan_maki":     "軍艦卷",
    "salmon_shushi":   "鮭魚壽司",
    "shrimp_shushi":   "蝦壽司",
    "unagi_shushi":    "鰻魚壽司",
}

INGREDIENT_DISPLAY_NAMES = {
    "shirmp":  "蝦",
    "rice":    "米飯",
    "nori":    "海苔",
    "fishegg": "魚卵",
    "salmon":  "鮭魚",
    "unagi":   "鰻魚",
}


class TextRedirector:
    """將 print 輸出安全地導向至 tkinter Text widget"""
    def __init__(self, widget, root):
        self.widget = widget
        self.root = root

    def write(self, text):
        self.root.after(0, self._write, text)

    def _write(self, text):
        self.widget.configure(state="normal")
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
        self.widget.configure(state="disabled")

    def flush(self):
        pass


class SushiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("壽司製作控制台")
        self.root.resizable(True, True)

        self._build_ui()

        # 重導向 print 輸出到日誌視窗
        sys.stdout = TextRedirector(self.log_text, self.root)

        # 按下 X 鍵關閉視窗（視窗有焦點時）
        self.root.bind("<x>", lambda e: self._quit())
        self.root.bind("<X>", lambda e: self._quit())

        # 全域熱鍵 Ctrl+Q 關閉、Ctrl+S 停止自動遊玩、Ctrl+R 重置
        self._hotkey = keyboard.GlobalHotKeys({
            "<ctrl>+q": self._quit,
            "<ctrl>+s": self._hotkey_stop_play,
            "<ctrl>+r": self._hotkey_reset,
        })
        self._hotkey.start()

        # 每 500ms 更新一次庫存顯示
        self._update_inventory()

        # 自動遊玩狀態
        self._playing = False
        self._update_order_status()

        print("=== 控制台已啟動 ===")
        game.print_inventory()

    def _build_ui(self):
        # ── 頂部三欄框架 ──
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.BOTH)

        # ── 左欄：食材庫存 ──
        inv_frame = tk.LabelFrame(top_frame, text="食材庫存", padx=8, pady=8,
                                  font=("Arial", 11, "bold"))
        inv_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ns")

        self.inv_labels = {}
        for name, display in INGREDIENT_DISPLAY_NAMES.items():
            row = tk.Frame(inv_frame)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{display}：", width=6, anchor="w",
                     font=("Arial", 11)).pack(side=tk.LEFT)
            lbl = tk.Label(row, text="--", width=4, anchor="e",
                           font=("Arial", 12, "bold"))
            lbl.pack(side=tk.LEFT)
            self.inv_labels[name] = lbl

        # ── 中欄：製作壽司 ──
        sushi_frame = tk.LabelFrame(top_frame, text="製作壽司", padx=8, pady=8,
                                    font=("Arial", 11, "bold"))
        sushi_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

        for recipe, display in RECIPE_DISPLAY_NAMES.items():
            btn = tk.Button(
                sushi_frame, text=display, width=12, height=2,
                font=("Arial", 10, "bold"),
                bg="#4CAF50", fg="white", activebackground="#388E3C",
                command=lambda r=recipe: self._action_make_sushi(r)
            )
            btn.pack(pady=3)

        # ── 右欄：補貨 ──
        restock_frame = tk.LabelFrame(top_frame, text="補貨", padx=8, pady=8,
                                      font=("Arial", 11, "bold"))
        restock_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ns")

        for name, display in INGREDIENT_DISPLAY_NAMES.items():
            if name in game.RESTOCK_AMOUNTS:
                amount = game.RESTOCK_AMOUNTS[name]
                btn = tk.Button(
                    restock_frame,
                    text=f"{display}  (+{amount})",
                    width=12, height=2,
                    font=("Arial", 10),
                    bg="#2196F3", fg="white", activebackground="#1565C0",
                    command=lambda n=name: self._action_restock(n)
                )
                btn.pack(pady=3)

        # ── 最右欄：操作 ──
        action_frame = tk.LabelFrame(top_frame, text="操作", padx=8, pady=8,
                                     font=("Arial", 11, "bold"))
        action_frame.grid(row=0, column=3, padx=5, pady=5, sticky="ns")

        tk.Button(
            action_frame, text="收盤", width=12, height=2,
            font=("Arial", 10, "bold"),
            bg="#FF9800", fg="white", activebackground="#E65100",
            command=self._action_check_plates
        ).pack(pady=3)

        tk.Button(
            action_frame, text="偵測訂單", width=12, height=2,
            font=("Arial", 10, "bold"),
            bg="#9C27B0", fg="white", activebackground="#6A1B9A",
            command=self._action_detect_orders
        ).pack(pady=3)

        tk.Button(
            action_frame, text="偵測關卡結果", width=12, height=2,
            font=("Arial", 10, "bold"),
            bg="#F44336", fg="white", activebackground="#B71C1C",
            command=self._action_check_game_finished
        ).pack(pady=3)

        self._play_btn = tk.Button(
            action_frame, text="▶ 開始遊玩", width=12, height=2,
            font=("Arial", 10, "bold"),
            bg="#009688", fg="white", activebackground="#00695C",
            command=self._action_start_stop_play
        )
        self._play_btn.pack(pady=3)

        tk.Button(
            action_frame, text="🔄 重置遊戲", width=12, height=2,
            font=("Arial", 10, "bold"),
            bg="#607D8B", fg="white", activebackground="#37474F",
            command=self._action_reset
        ).pack(pady=3)

        # ── 訂單顯示區 ──
        orders_frame = tk.LabelFrame(self.root, text="顧客訂單", padx=8, pady=8,
                                     font=("Arial", 11, "bold"))
        orders_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.order_labels = {}
        self.order_status_labels = {}
        for i, seat in enumerate(["customer1", "customer2", "customer3",
                                   "customer4", "customer5", "customer6"]):
            col = tk.Frame(orders_frame)
            col.grid(row=0, column=i, padx=10, pady=4)
            tk.Label(col, text=f"客1座" if i == 0 else f"客{i+1}座",
                     font=("Arial", 9, "bold")).pack()
            lbl = tk.Label(col, text="--", font=("Arial", 9),
                           width=10, bg="#f0f0f0", relief="sunken", pady=3)
            lbl.pack()
            self.order_labels[seat] = lbl
            status_lbl = tk.Label(col, text="--", font=("Arial", 8),
                                  width=10, bg="#f0f0f0", relief="flat", pady=2)
            status_lbl.pack()
            self.order_status_labels[seat] = status_lbl

        # ── 底部：執行日誌 ──
        log_frame = tk.LabelFrame(self.root, text="執行日誌", padx=8, pady=5,
                                  font=("Arial", 11, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=12, state="disabled",
            font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        tk.Button(log_frame, text="清除日誌", command=self._clear_log,
                  font=("Arial", 9)).pack(anchor="e", pady=2)

    def _quit(self):
        self._hotkey.stop()
        self.root.after(0, self.root.destroy)

    def _update_inventory(self):
        for name, lbl in self.inv_labels.items():
            amount = game.inventory.get(name, 0)
            lbl.config(
                text=str(amount),
                fg="#e53935" if amount <= 1 else "#2e7d32"
            )
        self.root.after(500, self._update_inventory)

    def _action_make_sushi(self, recipe_name):
        display = RECIPE_DISPLAY_NAMES.get(recipe_name, recipe_name)
        print(f"[操作] 製作 {display}...")
        threading.Thread(
            target=game.make_sushi, args=(recipe_name,), daemon=True
        ).start()

    def _action_restock(self, name):
        display = INGREDIENT_DISPLAY_NAMES.get(name, name)
        print(f"[操作] 補貨 {display}...")
        threading.Thread(
            target=game.restock_ingredients, args=(name,), daemon=True
        ).start()

    def _action_check_plates(self):
        print("[操作] 檢查並收盤...")
        threading.Thread(target=game.check_plates, daemon=True).start()

    def _action_detect_orders(self):
        print("[操作] 偵測顧客訂單...")
        def _detect():
            game.detect_orders()
            self.root.after(0, self._refresh_order_labels)
        threading.Thread(target=_detect, daemon=True).start()

    def _hotkey_stop_play(self):
        if self._playing:
            self.root.after(0, self._stop_play_ui)

    def _hotkey_reset(self):
        self.root.after(0, self._action_reset)

    def _stop_play_ui(self):
        game.stop_auto_play()
        self._playing = False
        self._play_btn.config(text="▶ 開始遊玩", bg="#009688")
        print("[熱鍵] Ctrl+S 停止自動遊玩")

    def _action_reset(self):
        game.reset_game()
        self._playing = False
        self._play_btn.config(text="▶ 開始遊玩", bg="#009688")
        print("[重置] 已重置所有狀態")

    def _action_start_stop_play(self):
        if not self._playing:
            self._playing = True
            self._play_btn.config(text="■ 停止遊玩", bg="#e53935")
            print("[操作] 自動遊玩啟動...")
            threading.Thread(target=game.start_auto_play, daemon=True).start()
        else:
            game.stop_auto_play()
            self._playing = False
            self._play_btn.config(text="▶ 開始遊玩", bg="#009688")
            print("[操作] 自動遊玩停止...")

    def _update_order_status(self):
        STATUS_COLORS = {
            "待處理": "#FFF9C4",
            "製作中": "#FFE0B2",
            "已送出": "#BBDEFB",
            "完成":   "#C8E6C9",
        }
        # 如果自動遊玩已由內部停止（關卡結束）則更新按鈕
        if self._playing and not game._auto_play_running:
            self._playing = False
            self._play_btn.config(text="▶ 開始遊玩", bg="#009688")

        for seat in self.order_status_labels:
            info = game.order_status.get(seat, {})
            order = info.get("order")
            status = info.get("status", "--")
            color = STATUS_COLORS.get(status, "#f0f0f0")

            # 訂單名稱
            display = RECIPE_DISPLAY_NAMES.get(order, "無訂單") if order else "無訂單"
            order_bg = "#c8e6c9" if order else "#f0f0f0"
            self.order_labels[seat].config(text=display, bg=order_bg)

            # 狀態
            self.order_status_labels[seat].config(text=status, bg=color)

        self.root.after(500, self._update_order_status)

    def _action_check_game_finished(self):
        print("[操作] 偵測關卡結果...")
        threading.Thread(target=game.check_game_finished, daemon=True).start()

    def _refresh_order_labels(self):
        for seat, lbl in self.order_labels.items():
            recipe = game.current_orders.get(seat)
            display = RECIPE_DISPLAY_NAMES.get(recipe, "無訂單") if recipe else "無訂單"
            lbl.config(
                text=display,
                bg="#c8e6c9" if recipe else "#f0f0f0"
            )
    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = SushiGUI(root)
    root.mainloop()
    sys.stdout = sys.__stdout__
