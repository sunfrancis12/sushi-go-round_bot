import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys

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

        # 每 500ms 更新一次庫存顯示
        self._update_inventory()

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

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = SushiGUI(root)
    root.mainloop()
    sys.stdout = sys.__stdout__
