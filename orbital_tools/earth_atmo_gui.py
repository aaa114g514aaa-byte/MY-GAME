"""
地球大气稠度计算器 (GUI)
========================
滑块实时调节海拔，即时显示温度、气压、密度、相对海平面比例。
大气模型: 1976 U.S. Standard Atmosphere (0 ~ 84.852 km)
"""

import tkinter as tk
from tkinter import ttk
from earth_calculations import (
    earth_temperature, earth_pressure, earth_density, RHO0
)


class AtmoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("地球大气稠度")
        self.root.geometry("540x440")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d1b2a")

        self._setup_styles()
        self._build_ui()

        # 卡片就绪后再触发初始更新
        self.root.after(50, lambda: self.slider.set(0))

    def _setup_styles(self):
        self.c = {
            "bg": "#0d1b2a",
            "fg": "#e0e0e0",
            "accent": "#4fc3f7",
            "card": "#1b2838",
            "border": "#2c3e50",
            "value": "#ffffff",
            "label": "#78909c",
            "highlight": "#ff5252",
        }

    def _build_ui(self):
        root = self.root

        # ── 标题 ──
        tk.Label(
            root,
            text="地球大气稠度计算器",
            font=("Segoe UI", 16, "bold"),
            bg=self.c["bg"],
            fg=self.c["accent"],
        ).pack(pady=(16, 4))
        tk.Label(
            root,
            text="1976 U.S. Standard Atmosphere · 0 ~ 84.852 km",
            font=("Segoe UI", 9),
            bg=self.c["bg"],
            fg=self.c["label"],
        ).pack(pady=(0, 12))

        # ── 滑块行 ──
        frame_slider = tk.Frame(root, bg=self.c["bg"])
        frame_slider.pack(fill="x", padx=30, pady=(0, 8))

        tk.Label(
            frame_slider, text="海拔 (km)",
            font=("Segoe UI", 10), bg=self.c["bg"], fg=self.c["fg"],
        ).pack(anchor="w")

        slider_row = tk.Frame(frame_slider, bg=self.c["bg"])
        slider_row.pack(fill="x")

        self.alt_label = tk.Label(
            slider_row, text="0.00 km",
            font=("Segoe UI", 20, "bold"),
            bg=self.c["bg"], fg=self.c["value"],
            width=10, anchor="e",
        )
        self.alt_label.pack(side="right", padx=(10, 0))

        self.slider = ttk.Scale(
            slider_row,
            from_=0,
            to=84.852,
            orient="horizontal",
            command=self._on_slider,
        )
        self.slider.pack(side="left", fill="x", expand=True)

        # ── 数据显示卡片 ──
        frame_data = tk.Frame(root, bg=self.c["bg"])
        frame_data.pack(fill="both", expand=True, padx=30, pady=(8, 16))

        self._make_card(frame_data, "温度", "0 K", 0, 0, "lbl_temp")
        self._make_card(frame_data, "大气压", "0 Pa", 0, 1, "lbl_press")
        self._make_card(frame_data, "大气密度", "0 kg/m³", 1, 0, "lbl_density")
        self._make_card(frame_data, "相对海平面", "0.00%", 1, 1, "lbl_ratio")

    def _make_card(self, parent, label, value, row, col, attr_name):
        card = tk.Frame(
            parent, bg=self.c["card"],
            highlightbackground=self.c["border"],
            highlightthickness=1,
            padx=14, pady=10,
        )
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(
            card, text=label,
            font=("Segoe UI", 9), bg=self.c["card"], fg=self.c["label"],
        ).pack(anchor="w")

        lbl = tk.Label(
            card, text=value,
            font=("Segoe UI", 14, "bold"),
            bg=self.c["card"], fg=self.c["value"],
            anchor="w",
        )
        lbl.pack(fill="x", pady=(4, 0))
        setattr(self, attr_name, lbl)

    def _on_slider(self, val):
        try:
            km = float(val)
        except ValueError:
            km = 0.0
        self._update(km)

    def _update(self, km: float):
        h = km * 1000.0
        T = earth_temperature(h)
        P = earth_pressure(h)
        rho = earth_density(h)
        ratio = (rho / RHO0 * 100) if rho > 0 else 0.0

        # 大气层分类
        if km >= 84.852:
            status = "已出大气层"
            status_color = self.c["highlight"]
        elif km < 11:
            status = "对流层"
            status_color = self.c["accent"]
        elif km < 20:
            status = "对流层顶 / 平流层底"
            status_color = "#81c784"
        elif km < 47:
            status = "平流层"
            status_color = "#f0c040"
        elif km < 51:
            status = "平流层顶"
            status_color = "#ffb74d"
        elif km < 71:
            status = "中间层"
            status_color = "#a080ff"
        else:
            status = "中间层顶 / 近真空"
            status_color = "#ce93d8"

        self.alt_label.config(text=f"{km:.2f} km")
        self.lbl_temp.config(text=f"{T:.2f} K ({T - 273.15:.1f} °C)" if T > 0 else "N/A")
        self.lbl_press.config(text=f"{P:.4f} Pa" if P > 0 else "0 Pa")
        self.lbl_density.config(text=f"{rho:.6e} kg/m³" if rho > 0 else "0 kg/m³")
        self.lbl_ratio.config(text=f"{ratio:.4f}%")

        # 状态显示
        self.lbl_status = getattr(self, "lbl_status", None)
        if self.lbl_status:
            self.lbl_status.config(text=status, fg=status_color)
        else:
            # 跨网格底部的状态条
            status_frame = tk.Frame(
                self.lbl_ratio.master.master, bg=self.c["card"],
                highlightbackground=self.c["border"], highlightthickness=1,
                padx=14, pady=8,
            )
            status_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=(6, 0))
            tk.Label(
                status_frame, text="大气层",
                font=("Segoe UI", 9), bg=self.c["card"], fg=self.c["label"],
            ).pack(anchor="w")
            self.lbl_status = tk.Label(
                status_frame, text=status,
                font=("Segoe UI", 14, "bold"),
                bg=self.c["card"], fg=status_color, anchor="w",
            )
            self.lbl_status.pack(fill="x", pady=(4, 0))

        # 让数据显示区域的父级多一行给状态栏
        frame_data = self.lbl_ratio.master.master
        frame_data.grid_rowconfigure(2, weight=0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AtmoGUI()
    app.run()
