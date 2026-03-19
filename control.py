"""
DIEU KHIEN MAY AO — 3 nut: RUN / STOP / UPDATE
"""
import os, json, time
import tkinter as tk
from datetime import datetime

BASE_DIR = r"D:\AUTO"
COMMANDS_DIR = os.path.join(BASE_DIR, "commands")
STATUS_DIR = os.path.join(BASE_DIR, "status")
os.makedirs(COMMANDS_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DIEU KHIEN MAY AO")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # Title
        tk.Label(self.root, text="DIEU KHIEN MAY AO", font=("Segoe UI", 14, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))

        # ALL buttons
        top = tk.Frame(self.root, bg="#1e1e2e")
        top.pack(fill="x", padx=10, pady=5)
        for txt, cmd, color in [("RUN ALL", "run", "#a6e3a1"),
                                 ("STOP ALL", "stop", "#f38ba8"),
                                 ("UPDATE ALL", "update", "#89b4fa")]:
            tk.Button(top, text=txt, bg=color, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                      width=12, relief="flat",
                      command=lambda c=cmd: self.send("ALL", c)).pack(side="left", padx=3)

        # VM list
        self.container = tk.Frame(self.root, bg="#1e1e2e")
        self.container.pack(fill="both", expand=True, padx=10, pady=5)

        # Status bar
        self.status_lbl = tk.Label(self.root, text="", font=("Consolas", 9),
                                    fg="#a6adc8", bg="#1e1e2e", anchor="w")
        self.status_lbl.pack(fill="x", padx=10, pady=(0, 5))

        self.refresh()
        self.root.mainloop()

    def send(self, channel, cmd):
        fpath = os.path.join(COMMANDS_DIR, f"{channel}.{cmd}")
        try:
            with open(fpath, "w") as f:
                f.write(datetime.now().isoformat())
            self.log(f"Da gui: {cmd} -> {channel}")
        except Exception as e:
            self.log(f"LOI: {e}")

    def log(self, msg):
        self.status_lbl.config(text=f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def get_color(self, state):
        if state == "running":
            return "#a6e3a1"
        if state in ("stopped", "killed", "idle"):
            return "#f38ba8"
        if state in ("updating", "starting"):
            return "#89b4fa"
        return "#fab387"

    def refresh(self):
        vms = []
        try:
            for f in sorted(os.listdir(STATUS_DIR)):
                if not f.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(STATUS_DIR, f), "r", encoding="utf-8") as fh:
                        vms.append(json.load(fh))
                except Exception:
                    pass
        except Exception:
            pass

        for w in self.container.winfo_children():
            w.destroy()

        if not vms:
            tk.Label(self.container, text="Chua co may ao nao bao cao...",
                     font=("Segoe UI", 11), fg="#a6adc8", bg="#1e1e2e").pack(pady=20)
        else:
            for vm in vms:
                self.draw_vm(vm)

        count = max(len(vms), 1)
        h = 130 + count * 45
        self.root.geometry(f"680x{min(h, 800)}")
        self.root.after(5000, self.refresh)

    def draw_vm(self, vm):
        ch = vm.get("channel", "?")
        st = vm.get("state", "?")
        dp = vm.get("dang_py", "?")
        up = vm.get("uptime_minutes", 0)
        color = self.get_color(st)

        row = tk.Frame(self.container, bg="#313244", pady=4, padx=8)
        row.pack(fill="x", pady=2)

        # Info
        tk.Label(row, text=ch, font=("Consolas", 11, "bold"), fg="#cdd6f4",
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=st, font=("Consolas", 10), fg=color,
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=f"dang.py={dp}", font=("Consolas", 9), fg="#a6adc8",
                 bg="#313244", width=16, anchor="w").pack(side="left")
        tk.Label(row, text=f"{up}p", font=("Consolas", 9), fg="#a6adc8",
                 bg="#313244", width=6).pack(side="left")

        # 3 buttons
        for txt, cmd, clr in [("RUN", "run", "#a6e3a1"),
                                ("STOP", "stop", "#f38ba8"),
                                ("UPDATE", "update", "#89b4fa")]:
            tk.Button(row, text=txt, bg=clr, fg="#1e1e2e", font=("Segoe UI", 8, "bold"),
                      width=7, relief="flat",
                      command=lambda c=cmd, n=ch: self.send(n, c)).pack(side="left", padx=2)


if __name__ == "__main__":
    App()
