"""
DIEU KHIEN MAY AO — RUN / STOP / UPDATE + SETTING SMB
"""
import os, json, time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDS_DIR = os.path.join(BASE_DIR, "commands")
STATUS_DIR = os.path.join(BASE_DIR, "status")
SETTINGS_FILE = os.path.join(BASE_DIR, "control_settings.json")
os.makedirs(COMMANDS_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)

# SMB mac dinh
DEFAULT_SMB = {
    "SMB_USER": "smbuser",
    "SMB_PASS": "159753",
    "SMB_DRIVE": "Z:",
    "servers": []  # danh sach IP may chu: ["192.168.88.254", "192.168.88.100"]
}


def load_settings():
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_SMB)


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class App:
    def __init__(self):
        self.settings = load_settings()
        self.root = tk.Tk()
        self.root.title("DIEU KHIEN MAY AO")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # ═══ TOP: Title + Setting button ═══
        title_frame = tk.Frame(self.root, bg="#1e1e2e")
        title_frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(title_frame, text="DIEU KHIEN MAY AO", font=("Segoe UI", 14, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(side="left")
        tk.Button(title_frame, text="SETTING", bg="#585b70", fg="#cdd6f4",
                  font=("Segoe UI", 9, "bold"), width=8, relief="flat",
                  command=self.open_settings).pack(side="right")

        # ═══ ALL buttons ═══
        top = tk.Frame(self.root, bg="#1e1e2e")
        top.pack(fill="x", padx=10, pady=5)
        for txt, cmd, color in [("RUN ALL", "run", "#a6e3a1"),
                                 ("STOP ALL", "stop", "#f38ba8"),
                                 ("UPDATE ALL", "update", "#89b4fa")]:
            tk.Button(top, text=txt, bg=color, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                      width=12, relief="flat",
                      command=lambda c=cmd: self.send("ALL", c)).pack(side="left", padx=3)

        # ═══ VM list ═══
        self.container = tk.Frame(self.root, bg="#1e1e2e")
        self.container.pack(fill="both", expand=True, padx=10, pady=5)

        # ═══ Status bar ═══
        self.status_lbl = tk.Label(self.root, text="", font=("Consolas", 9),
                                    fg="#a6adc8", bg="#1e1e2e", anchor="w")
        self.status_lbl.pack(fill="x", padx=10, pady=(0, 5))

        self.refresh()
        self.root.mainloop()

    # ─── SMB SETTINGS WINDOW ───
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("SETTING - SMB MAY CHU")
        win.configure(bg="#1e1e2e")
        win.geometry("500x450")
        win.resizable(False, False)

        s = self.settings

        # SMB chung
        tk.Label(win, text="CAU HINH SMB CHUNG", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))

        common = tk.Frame(win, bg="#313244", padx=10, pady=8)
        common.pack(fill="x", padx=10, pady=5)

        for i, (label, key, default) in enumerate([
            ("User:", "SMB_USER", "smbuser"),
            ("Password:", "SMB_PASS", "159753"),
            ("Drive:", "SMB_DRIVE", "Z:")
        ]):
            tk.Label(common, text=label, font=("Consolas", 10), fg="#a6adc8",
                     bg="#313244", width=10, anchor="w").grid(row=i, column=0, pady=2)
            entry = tk.Entry(common, font=("Consolas", 10), width=25, bg="#45475a",
                             fg="#cdd6f4", insertbackground="#cdd6f4", relief="flat")
            entry.insert(0, s.get(key, default))
            entry.grid(row=i, column=1, pady=2, padx=5)
            setattr(self, f"entry_{key}", entry)

        # Danh sach may chu
        tk.Label(win, text="DANH SACH MAY CHU (IP)", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(15, 5))

        srv_frame = tk.Frame(win, bg="#1e1e2e")
        srv_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.server_listbox = tk.Listbox(srv_frame, font=("Consolas", 11), bg="#313244",
                                          fg="#a6e3a1", selectbackground="#585b70",
                                          relief="flat", height=6)
        self.server_listbox.pack(side="left", fill="both", expand=True)

        for ip in s.get("servers", []):
            self.server_listbox.insert("end", ip)

        # Buttons ben phai
        btn_frame = tk.Frame(srv_frame, bg="#1e1e2e")
        btn_frame.pack(side="right", padx=(5, 0))

        self.new_ip_entry = tk.Entry(btn_frame, font=("Consolas", 10), width=16,
                                      bg="#45475a", fg="#cdd6f4", insertbackground="#cdd6f4",
                                      relief="flat")
        self.new_ip_entry.pack(pady=2)
        self.new_ip_entry.insert(0, "192.168.88.")

        tk.Button(btn_frame, text="THEM", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), width=8, relief="flat",
                  command=self.add_server).pack(pady=2)
        tk.Button(btn_frame, text="XOA", bg="#f38ba8", fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), width=8, relief="flat",
                  command=self.remove_server).pack(pady=2)

        # Luu + Dong
        bottom = tk.Frame(win, bg="#1e1e2e")
        bottom.pack(fill="x", padx=10, pady=10)
        tk.Button(bottom, text="LUU & AP DUNG", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=15, relief="flat",
                  command=lambda: self.save_and_apply(win)).pack(side="left", padx=3)
        tk.Button(bottom, text="DONG", bg="#585b70", fg="#cdd6f4",
                  font=("Segoe UI", 10, "bold"), width=8, relief="flat",
                  command=win.destroy).pack(side="right", padx=3)

        # Huong dan
        tk.Label(win, text="Khi LUU, thong tin SMB se duoc gui toi tat ca may ao qua lenh 'smb_setup'",
                 font=("Segoe UI", 8), fg="#585b70", bg="#1e1e2e").pack(pady=(0, 5))

    def add_server(self):
        ip = self.new_ip_entry.get().strip()
        if ip and ip not in self.server_listbox.get(0, "end"):
            self.server_listbox.insert("end", ip)
            self.new_ip_entry.delete(0, "end")
            self.new_ip_entry.insert(0, "192.168.88.")

    def remove_server(self):
        sel = self.server_listbox.curselection()
        if sel:
            self.server_listbox.delete(sel[0])

    def save_and_apply(self, win):
        """Luu settings va tao file smb_setup cho tat ca VM."""
        self.settings["SMB_USER"] = self.entry_SMB_USER.get().strip()
        self.settings["SMB_PASS"] = self.entry_SMB_PASS.get().strip()
        self.settings["SMB_DRIVE"] = self.entry_SMB_DRIVE.get().strip()
        self.settings["servers"] = list(self.server_listbox.get(0, "end"))

        save_settings(self.settings)

        # Tao file smb_setup cho tat ca VM
        # Watchdog se doc file nay va cap nhat config.json tren VM
        smb_data = {
            "SMB_USER": self.settings["SMB_USER"],
            "SMB_PASS": self.settings["SMB_PASS"],
            "SMB_DRIVE": self.settings["SMB_DRIVE"],
            "servers": self.settings["servers"]
        }
        smb_file = os.path.join(COMMANDS_DIR, "ALL.smb_setup")
        try:
            with open(smb_file, "w", encoding="utf-8") as f:
                json.dump(smb_data, f, ensure_ascii=False, indent=2)
            self.log(f"Da luu setting + gui smb_setup toi tat ca VM")
        except Exception as e:
            self.log(f"LOI luu: {e}")

        win.destroy()

    # ─── CORE ───
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
        h = 150 + count * 45
        self.root.geometry(f"720x{min(h, 800)}")
        self.root.after(5000, self.refresh)

    def draw_vm(self, vm):
        ch = vm.get("channel", "?")
        st = vm.get("state", "?")
        dp = vm.get("dang_py", "?")
        up = vm.get("uptime_minutes", 0)
        color = self.get_color(st)

        row = tk.Frame(self.container, bg="#313244", pady=4, padx=8)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=ch, font=("Consolas", 11, "bold"), fg="#cdd6f4",
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=st, font=("Consolas", 10), fg=color,
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=f"dang.py={dp}", font=("Consolas", 9), fg="#a6adc8",
                 bg="#313244", width=16, anchor="w").pack(side="left")
        tk.Label(row, text=f"{up}p", font=("Consolas", 9), fg="#a6adc8",
                 bg="#313244", width=6).pack(side="left")

        for txt, cmd, clr in [("RUN", "run", "#a6e3a1"),
                                ("STOP", "stop", "#f38ba8"),
                                ("UPDATE", "update", "#89b4fa")]:
            tk.Button(row, text=txt, bg=clr, fg="#1e1e2e", font=("Segoe UI", 8, "bold"),
                      width=7, relief="flat",
                      command=lambda c=cmd, n=ch: self.send(n, c)).pack(side="left", padx=2)


if __name__ == "__main__":
    App()
