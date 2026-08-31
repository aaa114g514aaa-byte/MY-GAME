"""
KSP1 大气稠度计算器 (GUI)
=========================
滑块实时调节海拔，即时显示大气压、密度、相对海平面比例。
"""

import tkinter as tk
from tkinter import ttk
from ksp1_calculations import kerbin_pressure, kerbin_density, RHO0_KERBIN, ATM_TOP


class AtmoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kerbin 大气稠度")
        self.root.geometry("520x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self._setup_styles()
        self._build_ui()

        # 卡片就绪后再触发初始更新
        self.root.after(50, lambda: self.slider.set(0))

    def _setup_styles(self):
        self.c = {
            "bg": "#1a1a2e",
            "fg": "#e0e0e0",
            "accent": "#00d4ff",
            "card": "#16213e",
            "border": "#0f3460",
            "value": "#ffffff",
            "label": "#8899aa",
            "highlight": "#e94560",
        }

    def _build_ui(self):
        root = self.root

        # ── 标题 ──
        tk.Label(
            root,
            text="Kerbin 大气稠度计算器",
            font=("Segoe UI", 16, "bold"),
            bg=self.c["bg"],
            fg=self.c["accent"],
        ).pack(pady=(16, 4))
        tk.Label(
            root,
            text="KSP1 指数大气模型 · 标高 5.6 km · 大气顶 69.078 km",
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

        # 高度显示 + 滑块
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
            to=ATM_TOP / 1000.0,
            orient="horizontal",
            command=self._on_slider,
        )
        self.slider.pack(side="left", fill="x", expand=True)

        # ── 数据显示卡片 ──
        frame_data = tk.Frame(root, bg=self.c["bg"])
        frame_data.pack(fill="both", expand=True, padx=30, pady=(8, 16))

        self._make_card(frame_data, "大气压", "0 Pa", 0, 0, "lbl_press")
        self._make_card(frame_data, "大气密度", "0 kg/m³", 0, 1, "lbl_density")
        self._make_card(frame_data, "相对海平面", "0.00%", 1, 0, "lbl_ratio")
        self._make_card(frame_data, "大气层状态", "海平面", 1, 1, "lbl_status")

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
        P = kerbin_pressure(h)
        rho = kerbin_density(h)
        ratio = (rho / RHO0_KERBIN * 100) if rho > 0 else 0.0

        # 大气层状态
        if h >= ATM_TOP:
            status = "已出大气层"
            status_color = self.c["highlight"]
        elif h < 18000:
            status = "低层大气"
            status_color = self.c["accent"]
        elif h < 40000:
            status = "中层大气"
            status_color = "#f0c040"
        else:
            status = "高层大气 / 近真空"
            status_color = "#a080ff"

        # 更新显示
        self.alt_label.config(text=f"{km:.2f} km")
        self.lbl_press.config(text=f"{P:.2f} Pa" if P > 0 else "0 Pa")
        self.lbl_density.config(text=f"{rho:.6e} kg/m³" if rho > 0 else "0 kg/m³")
        self.lbl_ratio.config(text=f"{ratio:.4f}%")
        self.lbl_status.config(text=status, fg=status_color)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AtmoGUI()
    app.run()
