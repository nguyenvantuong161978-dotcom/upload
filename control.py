"""
DIEU KHIEN MAY AO — RUN / STOP / UPDATE + SETTING SMB
"""
import os, json, time, subprocess, socket
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDS_DIR = os.path.join(BASE_DIR, "commands")
STATUS_DIR = os.path.join(BASE_DIR, "status")
SETTINGS_FILE = os.path.join(BASE_DIR, "control_settings.json")

# Doc version hien tai (tren may chu)
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
CURRENT_VERSION = "?"
if os.path.isfile(VERSION_FILE):
    try:
        with open(VERSION_FILE, "r") as f:
            CURRENT_VERSION = f.read().strip()
    except Exception:
        pass
os.makedirs(COMMANDS_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)

DEFAULT_SMB = {
    "SMB_USER": "smbuser",
    "SMB_PASS": "159753",
    "SMB_DRIVE": "Z:",
    "SHARE_PATH": "D:\\",
    "SHARE_NAME": "D",
    "servers": []
}


def load_settings():
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # merge defaults
                for k, v in DEFAULT_SMB.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return dict(DEFAULT_SMB)


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def setup_smb_on_host(user, password, share_name, share_path):
    """Tao user SMB + share thu muc tren may chu nay."""
    errors = []

    # 1. Tao user (neu chua co)
    result = subprocess.run(f'net user {user} {password} /add',
                            shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        errors.append(f"[OK] Tao user: {user}")
    elif "already exists" in result.stderr.lower() or "already exists" in result.stdout.lower():
        # Update password
        subprocess.run(f'net user {user} {password}',
                       shell=True, capture_output=True, timeout=10)
        errors.append(f"[OK] User da ton tai, cap nhat password: {user}")
    else:
        errors.append(f"[!] Tao user: {result.stdout.strip()} {result.stderr.strip()}")

    # 2. Xoa share cu (neu co)
    subprocess.run(f'net share {share_name} /delete /y',
                   shell=True, capture_output=True, timeout=10)

    # 3. Tao share moi
    result = subprocess.run(
        f'net share {share_name}="{share_path}" /grant:{user},FULL',
        shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        errors.append(f"[OK] Share: {share_name} -> {share_path}")
    else:
        errors.append(f"[!] Share: {result.stdout.strip()} {result.stderr.strip()}")

    # 4. Cho phep SMB qua firewall
    subprocess.run(
        'netsh advfirewall firewall add rule name="SMB-In" dir=in action=allow protocol=tcp localport=445',
        shell=True, capture_output=True, timeout=10)
    errors.append("[OK] Firewall: port 445 da mo")

    return errors


class App:
    def __init__(self):
        self.settings = load_settings()
        self.root = tk.Tk()
        self.root.title("DIEU KHIEN MAY AO")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # Title + Setting
        title_frame = tk.Frame(self.root, bg="#1e1e2e")
        title_frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(title_frame, text=f"DIEU KHIEN MAY AO  v{CURRENT_VERSION}",
                 font=("Segoe UI", 14, "bold"), fg="#cdd6f4", bg="#1e1e2e").pack(side="left")
        tk.Button(title_frame, text="SETTING", bg="#585b70", fg="#cdd6f4",
                  font=("Segoe UI", 9, "bold"), width=8, relief="flat",
                  command=self.open_settings).pack(side="right")

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

    # ─── SETTINGS WINDOW ───
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("SETTING - SMB MAY CHU")
        win.configure(bg="#1e1e2e")
        win.geometry("550x550")
        win.resizable(False, False)
        s = self.settings

        # === SECTION 1: Thong tin SMB ===
        tk.Label(win, text="THONG TIN SMB", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))

        common = tk.Frame(win, bg="#313244", padx=10, pady=8)
        common.pack(fill="x", padx=10, pady=5)

        fields = [
            ("User:", "SMB_USER", "smbuser"),
            ("Password:", "SMB_PASS", "159753"),
            ("Drive:", "SMB_DRIVE", "Z:"),
            ("Share name:", "SHARE_NAME", "D"),
            ("Share path:", "SHARE_PATH", "D:\\"),
        ]
        for i, (label, key, default) in enumerate(fields):
            tk.Label(common, text=label, font=("Consolas", 10), fg="#a6adc8",
                     bg="#313244", width=12, anchor="w").grid(row=i, column=0, pady=2)
            entry = tk.Entry(common, font=("Consolas", 10), width=25, bg="#45475a",
                             fg="#cdd6f4", insertbackground="#cdd6f4", relief="flat")
            entry.insert(0, s.get(key, default))
            entry.grid(row=i, column=1, pady=2, padx=5)
            setattr(self, f"entry_{key}", entry)

        # === SECTION 2: IP may chu ===
        tk.Label(win, text="IP MAY CHU (IPv4)", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))

        ip_frame = tk.Frame(win, bg="#313244", padx=10, pady=8)
        ip_frame.pack(fill="x", padx=10, pady=5)

        self.ip_var = tk.StringVar(value=s.get("host_ip", "192.168.88.254"))
        tk.Label(ip_frame, text="IPv4:", font=("Consolas", 10), fg="#a6adc8",
                 bg="#313244", width=12, anchor="w").pack(side="left")
        self.ip_entry = tk.Entry(ip_frame, font=("Consolas", 10), width=20,
                                  bg="#45475a", fg="#a6e3a1", insertbackground="#cdd6f4",
                                  relief="flat", textvariable=self.ip_var)
        self.ip_entry.pack(side="left", padx=5)
        tk.Button(ip_frame, text="TU DONG", bg="#89b4fa", fg="#1e1e2e",
                  font=("Segoe UI", 8, "bold"), relief="flat",
                  command=self.auto_detect_ip).pack(side="left", padx=3)

        # === SECTION 3: Buttons ===
        btn_frame = tk.Frame(win, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(btn_frame, text="TAO SMB TREN MAY CHU", bg="#fab387", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=25, relief="flat",
                  command=lambda: self.create_smb(win)).pack(pady=3)
        tk.Button(btn_frame, text="GUI CAU HINH TOI TAT CA VM", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=25, relief="flat",
                  command=lambda: self.send_smb_to_vms(win)).pack(pady=3)
        tk.Button(btn_frame, text="DONG", bg="#585b70", fg="#cdd6f4",
                  font=("Segoe UI", 10, "bold"), width=10, relief="flat",
                  command=win.destroy).pack(pady=3)

        # Log area
        self.setting_log = tk.Text(win, font=("Consolas", 9), bg="#313244", fg="#cdd6f4",
                                    height=5, relief="flat", state="disabled")
        self.setting_log.pack(fill="x", padx=10, pady=(0, 10))

    def auto_detect_ip(self):
        try:
            result = subprocess.run(
                'powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike \'127.*\' -and $_.IPAddress -notlike \'169.*\' } | Select-Object -First 1).IPAddress"',
                shell=True, capture_output=True, text=True, timeout=10)
            ip = result.stdout.strip()
            if ip:
                self.ip_var.set(ip)
                self.setting_log_msg(f"IPv4 phat hien: {ip}")
            else:
                self.setting_log_msg("Khong tim thay IPv4.")
        except Exception:
            self.setting_log_msg("Loi khi phat hien IPv4.")

    def setting_log_msg(self, msg):
        self.setting_log.config(state="normal")
        self.setting_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.setting_log.see("end")
        self.setting_log.config(state="disabled")

    def _read_entries(self):
        """Doc gia tri tu cac entry."""
        self.settings["SMB_USER"] = self.entry_SMB_USER.get().strip()
        self.settings["SMB_PASS"] = self.entry_SMB_PASS.get().strip()
        self.settings["SMB_DRIVE"] = self.entry_SMB_DRIVE.get().strip()
        self.settings["SHARE_NAME"] = self.entry_SHARE_NAME.get().strip()
        self.settings["SHARE_PATH"] = self.entry_SHARE_PATH.get().strip()
        self.settings["host_ip"] = self.ip_var.get().strip()
        save_settings(self.settings)

    def create_smb(self, win):
        """Tao user + share SMB tren may chu nay."""
        self._read_entries()
        s = self.settings

        if not s["SMB_USER"] or not s["SMB_PASS"]:
            messagebox.showwarning("Thieu thong tin", "Can co User va Password!")
            return

        self.setting_log_msg("Dang tao SMB share...")
        results = setup_smb_on_host(s["SMB_USER"], s["SMB_PASS"],
                                     s["SHARE_NAME"], s["SHARE_PATH"])
        for r in results:
            self.setting_log_msg(r)

        # Luu IP neu chua co
        if not s.get("host_ip"):
            self.auto_detect_ip()
            self.settings["host_ip"] = self.ip_var.get().strip()
            save_settings(self.settings)

        self.setting_log_msg("HOAN TAT! Gio hay an 'GUI CAU HINH TOI TAT CA VM'.")

    def send_smb_to_vms(self, win):
        """Gui thong tin SMB toi tat ca VM qua commands/."""
        self._read_entries()
        s = self.settings

        ip = s.get("host_ip", "")
        if not ip:
            messagebox.showwarning("Thieu IP",
                                   "Can co IPv4 may chu! An 'TU DONG' de phat hien.")
            return

        smb_data = {
            "SMB_USER": s["SMB_USER"],
            "SMB_PASS": s["SMB_PASS"],
            "SMB_DRIVE": s["SMB_DRIVE"],
            "SHARE_NAME": s["SHARE_NAME"],
            "servers": [ip]
        }

        data_str = json.dumps(smb_data, ensure_ascii=False, indent=2)
        self.send("ALL", "smb_setup", data=data_str)
        try:
            self.setting_log_msg(f"Da gui smb_setup toi tung VM:")
            self.setting_log_msg(f"  SMB: \\\\{ip}\\{s['SHARE_NAME']}")
            self.setting_log_msg(f"  Drive: {s['SMB_DRIVE']}")
            self.log(f"SMB config da gui toi tat ca VM")
        except Exception as e:
            self.setting_log_msg(f"LOI: {e}")

    # ─── CORE ───
    def _get_all_channels(self):
        """Lay danh sach channel tu status files."""
        channels = []
        try:
            for f in os.listdir(STATUS_DIR):
                if f.endswith(".json"):
                    channels.append(f.replace(".json", ""))
        except Exception:
            pass
        return channels

    def send(self, channel, cmd, data=None):
        """Gui lenh. Neu channel=ALL, tao file rieng cho TUNG VM."""
        if channel == "ALL":
            channels = self._get_all_channels()
            if not channels:
                self.log("Khong co VM nao de gui lenh!")
                return
            count = 0
            for ch in channels:
                fpath = os.path.join(COMMANDS_DIR, f"{ch}.{cmd}")
                try:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(data if data else datetime.now().isoformat())
                    count += 1
                except Exception:
                    pass
            self.log(f"Da gui: {cmd} -> {count}/{len(channels)} VM")
        else:
            fpath = os.path.join(COMMANDS_DIR, f"{channel}.{cmd}")
            try:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(data if data else datetime.now().isoformat())
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
        ver = vm.get("version", "?")
        color = self.get_color(st)
        is_outdated = ver != CURRENT_VERSION and ver != "?"
        ver_color = "#f38ba8" if is_outdated else "#a6e3a1"

        row = tk.Frame(self.container, bg="#313244", pady=4, padx=8)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=ch, font=("Consolas", 11, "bold"), fg="#cdd6f4",
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=st, font=("Consolas", 10), fg=color,
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=f"v{ver}", font=("Consolas", 9), fg=ver_color,
                 bg="#313244", width=7, anchor="w").pack(side="left")
        tk.Label(row, text=f"{up}p", font=("Consolas", 9), fg="#a6adc8",
                 bg="#313244", width=5).pack(side="left")

        for txt, cmd, clr in [("RUN", "run", "#a6e3a1"),
                                ("STOP", "stop", "#f38ba8"),
                                ("UPDATE", "update", "#89b4fa")]:
            tk.Button(row, text=txt, bg=clr, fg="#1e1e2e", font=("Segoe UI", 8, "bold"),
                      width=7, relief="flat",
                      command=lambda c=cmd, n=ch: self.send(n, c)).pack(side="left", padx=2)


if __name__ == "__main__":
    App()
