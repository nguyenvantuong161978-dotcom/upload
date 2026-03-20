"""
DIEU KHIEN MAY AO — RUN / STOP / UPDATE + SETTING SMB (IPv4 + IPv6)
"""
import os, json, time, subprocess
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDS_DIR = os.path.join(BASE_DIR, "commands")
STATUS_DIR = os.path.join(BASE_DIR, "status")
SETTINGS_FILE = os.path.join(BASE_DIR, "control_settings.json")
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

DEFAULT_SETTINGS = {
    "SMB_USER": "smbuser",
    "SMB_PASS": "159753",
    "SMB_DRIVE": "Z:",
    "SHARE_PATH": "D:\\",
    "SHARE_NAME": "D",
    "host_ipv4": "192.168.88.254",
    "host_ipv6": "",
    "vm_protocol": {}  # {"KA1-T3": "ipv4", "TA2-T1": "ipv6", ...}
}


def load_settings():
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def setup_smb_on_host(user, password, share_name, share_path):
    errors = []
    result = subprocess.run(f'net user {user} {password} /add',
                            shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        errors.append(f"[OK] Tao user: {user}")
    elif "already exists" in (result.stderr + result.stdout).lower():
        subprocess.run(f'net user {user} {password}', shell=True, capture_output=True, timeout=10)
        errors.append(f"[OK] User da ton tai, cap nhat password")
    else:
        errors.append(f"[!] Tao user: {result.stdout.strip()} {result.stderr.strip()}")

    subprocess.run(f'net share {share_name} /delete /y', shell=True, capture_output=True, timeout=10)
    result = subprocess.run(f'net share {share_name}="{share_path}" /grant:{user},FULL',
                            shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        errors.append(f"[OK] Share: {share_name} -> {share_path}")
    else:
        errors.append(f"[!] Share: {result.stdout.strip()} {result.stderr.strip()}")

    subprocess.run('netsh advfirewall firewall add rule name="SMB-In" dir=in action=allow protocol=tcp localport=445',
                   shell=True, capture_output=True, timeout=10)
    errors.append("[OK] Firewall: port 445 da mo")
    return errors


def ipv6_to_literal(ipv6):
    """2001:ee0:b004:3001::2 -> 2001-ee0-b004-3001--2.ipv6-literal.net"""
    return ipv6.replace(":", "-").replace("---", "--") + ".ipv6-literal.net"


class App:
    def __init__(self):
        self.settings = load_settings()
        self.root = tk.Tk()
        self.root.title(f"DIEU KHIEN MAY AO  v{CURRENT_VERSION}")
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

    # ─── SETTINGS ───
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("SETTING - SMB MAY CHU")
        win.configure(bg="#1e1e2e")
        win.geometry("550x500")
        win.resizable(False, False)
        s = self.settings

        # SMB chung
        tk.Label(win, text="THONG TIN SMB", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))
        common = tk.Frame(win, bg="#313244", padx=10, pady=8)
        common.pack(fill="x", padx=10, pady=5)

        for i, (label, key, default) in enumerate([
            ("User:", "SMB_USER", "smbuser"),
            ("Password:", "SMB_PASS", "159753"),
            ("Drive:", "SMB_DRIVE", "Z:"),
            ("Share name:", "SHARE_NAME", "D"),
            ("Share path:", "SHARE_PATH", "D:\\"),
        ]):
            tk.Label(common, text=label, font=("Consolas", 10), fg="#a6adc8",
                     bg="#313244", width=12, anchor="w").grid(row=i, column=0, pady=2)
            entry = tk.Entry(common, font=("Consolas", 10), width=25, bg="#45475a",
                             fg="#cdd6f4", insertbackground="#cdd6f4", relief="flat")
            entry.insert(0, s.get(key, default))
            entry.grid(row=i, column=1, pady=2, padx=5)
            setattr(self, f"entry_{key}", entry)

        # IP may chu
        tk.Label(win, text="IP MAY CHU", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#1e1e2e").pack(pady=(10, 5))
        ip_frame = tk.Frame(win, bg="#313244", padx=10, pady=8)
        ip_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(ip_frame, text="IPv4:", font=("Consolas", 10), fg="#a6adc8",
                 bg="#313244", width=8, anchor="w").grid(row=0, column=0, pady=2)
        self.entry_ipv4 = tk.Entry(ip_frame, font=("Consolas", 10), width=18, bg="#45475a",
                                    fg="#a6e3a1", insertbackground="#cdd6f4", relief="flat")
        self.entry_ipv4.insert(0, s.get("host_ipv4", "192.168.88.254"))
        self.entry_ipv4.grid(row=0, column=1, pady=2, padx=5)

        tk.Label(ip_frame, text="IPv6:", font=("Consolas", 10), fg="#a6adc8",
                 bg="#313244", width=8, anchor="w").grid(row=1, column=0, pady=2)
        self.entry_ipv6 = tk.Entry(ip_frame, font=("Consolas", 10), width=30, bg="#45475a",
                                    fg="#89b4fa", insertbackground="#cdd6f4", relief="flat")
        self.entry_ipv6.insert(0, s.get("host_ipv6", ""))
        self.entry_ipv6.grid(row=1, column=1, pady=2, padx=5)

        # Buttons
        btn_frame = tk.Frame(win, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=10, pady=8)
        tk.Button(btn_frame, text="TAO SMB", bg="#fab387", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=12, relief="flat",
                  command=lambda: self.create_smb(win)).pack(side="left", padx=3)
        tk.Button(btn_frame, text="GUI CONFIG", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=12, relief="flat",
                  command=lambda: self.send_smb_to_vms(win)).pack(side="left", padx=3)
        tk.Button(btn_frame, text="CAI FFPROBE", bg="#cba6f7", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), width=12, relief="flat",
                  command=lambda: self.install_ffprobe_all(win)).pack(side="left", padx=3)
        tk.Button(btn_frame, text="DONG", bg="#585b70", fg="#cdd6f4",
                  font=("Segoe UI", 10, "bold"), width=8, relief="flat",
                  command=win.destroy).pack(side="right", padx=3)

        # Log
        self.setting_log = tk.Text(win, font=("Consolas", 9), bg="#313244", fg="#cdd6f4",
                                    height=4, relief="flat", state="disabled")
        self.setting_log.pack(fill="x", padx=10, pady=(0, 10))

    def setting_log_msg(self, msg):
        self.setting_log.config(state="normal")
        self.setting_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.setting_log.see("end")
        self.setting_log.config(state="disabled")

    def _read_entries(self):
        self.settings["SMB_USER"] = self.entry_SMB_USER.get().strip()
        self.settings["SMB_PASS"] = self.entry_SMB_PASS.get().strip()
        self.settings["SMB_DRIVE"] = self.entry_SMB_DRIVE.get().strip()
        self.settings["SHARE_NAME"] = self.entry_SHARE_NAME.get().strip()
        self.settings["SHARE_PATH"] = self.entry_SHARE_PATH.get().strip()
        self.settings["host_ipv4"] = self.entry_ipv4.get().strip()
        self.settings["host_ipv6"] = self.entry_ipv6.get().strip()
        save_settings(self.settings)

    def create_smb(self, win):
        self._read_entries()
        s = self.settings
        self.setting_log_msg("Dang tao SMB share...")
        results = setup_smb_on_host(s["SMB_USER"], s["SMB_PASS"], s["SHARE_NAME"], s["SHARE_PATH"])
        for r in results:
            self.setting_log_msg(r)
        self.setting_log_msg("HOAN TAT!")

    def install_ffprobe_all(self, win):
        """Gui lenh install_ffprobe toi tat ca VM."""
        self.send("ALL", "install_ffprobe")
        self.setting_log_msg("Da gui lenh cai ffprobe toi tat ca VM.")
        self.setting_log_msg("VM se copy ffprobe.exe tu \\\\tsclient\\D\\upload\\ffmpeg\\bin\\")

    def send_smb_to_vms(self, win):
        """Gui config SMB rieng cho tung VM theo protocol da chon."""
        self._read_entries()
        s = self.settings
        ipv4 = s.get("host_ipv4", "")
        ipv6 = s.get("host_ipv6", "")
        vm_proto = s.get("vm_protocol", {})

        if not ipv4 and not ipv6:
            messagebox.showwarning("Thieu IP", "Can co it nhat IPv4 hoac IPv6!")
            return

        channels = self._get_all_channels()
        if not channels:
            self.setting_log_msg("Khong co VM nao!")
            return

        count_v4 = 0
        count_v6 = 0
        for ch in channels:
            proto = vm_proto.get(ch, "ipv4")  # mac dinh ipv4
            if proto == "ipv6" and ipv6:
                ip_literal = ipv6_to_literal(ipv6)
                smb_server = f"\\\\{ip_literal}\\{s['SHARE_NAME']}"
                need_ipv4_toggle = False
                count_v6 += 1
            else:
                smb_server = f"\\\\{ipv4}\\{s['SHARE_NAME']}"
                need_ipv4_toggle = True
                count_v4 += 1

            smb_data = {
                "SMB_SERVER": smb_server,
                "SMB_USER": s["SMB_USER"],
                "SMB_PASS": s["SMB_PASS"],
                "SMB_DRIVE": s["SMB_DRIVE"],
                "SHARE_NAME": s["SHARE_NAME"],
                "NEED_IPV4_TOGGLE": need_ipv4_toggle,
                "servers": [ipv4 if proto != "ipv6" else ipv6]
            }
            fpath = os.path.join(COMMANDS_DIR, f"{ch}.smb_setup")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(smb_data, f, ensure_ascii=False, indent=2)

        self.setting_log_msg(f"Da gui: {count_v4} VM dung IPv4, {count_v6} VM dung IPv6")
        self.log(f"SMB config: {count_v4} IPv4 + {count_v6} IPv6")

    # ─── CORE ───
    def _get_all_channels(self):
        channels = []
        try:
            for f in os.listdir(STATUS_DIR):
                if f.endswith(".json"):
                    channels.append(f.replace(".json", ""))
        except Exception:
            pass
        return channels

    def send(self, channel, cmd, data=None):
        if channel == "ALL":
            channels = self._get_all_channels()
            if not channels:
                self.log("Khong co VM nao!")
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
        if state == "running": return "#a6e3a1"
        if state in ("stopped", "killed", "idle"): return "#f38ba8"
        if state in ("updating", "starting"): return "#89b4fa"
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
        self.root.geometry(f"780x{min(h, 800)}")
        self.root.after(5000, self.refresh)

    def toggle_protocol(self, channel):
        """Chuyen doi IPv4 <-> IPv6 cho 1 VM."""
        vm_proto = self.settings.get("vm_protocol", {})
        current = vm_proto.get(channel, "ipv4")
        new_proto = "ipv6" if current == "ipv4" else "ipv4"
        vm_proto[channel] = new_proto
        self.settings["vm_protocol"] = vm_proto
        save_settings(self.settings)
        self.log(f"{channel}: {current} -> {new_proto}")

    def draw_vm(self, vm):
        ch = vm.get("channel", "?")
        st = vm.get("state", "?")
        dp = vm.get("dang_py", "?")
        up = vm.get("uptime_minutes", 0)
        ver = vm.get("version", "?")
        color = self.get_color(st)
        is_outdated = ver != CURRENT_VERSION and ver != "?"
        ver_color = "#f38ba8" if is_outdated else "#a6e3a1"

        # Protocol hien tai
        proto = self.settings.get("vm_protocol", {}).get(ch, "ipv4")
        proto_color = "#a6e3a1" if proto == "ipv4" else "#89b4fa"

        row = tk.Frame(self.container, bg="#313244", pady=4, padx=8)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=ch, font=("Consolas", 10, "bold"), fg="#cdd6f4",
                 bg="#313244", width=10, anchor="w").pack(side="left")
        tk.Label(row, text=st, font=("Consolas", 9), fg=color,
                 bg="#313244", width=9, anchor="w").pack(side="left")
        tk.Label(row, text=f"v{ver}", font=("Consolas", 8), fg=ver_color,
                 bg="#313244", width=6).pack(side="left")

        # Nút chọn IPv4/IPv6
        tk.Button(row, text=proto.upper(), bg=proto_color, fg="#1e1e2e",
                  font=("Consolas", 8, "bold"), width=5, relief="flat",
                  command=lambda c=ch: self.toggle_protocol(c)).pack(side="left", padx=2)

        # Nút điều khiển
        for txt, cmd, clr in [("RUN", "run", "#a6e3a1"),
                                ("STOP", "stop", "#f38ba8"),
                                ("UPDATE", "update", "#89b4fa")]:
            tk.Button(row, text=txt, bg=clr, fg="#1e1e2e", font=("Segoe UI", 8, "bold"),
                      width=6, relief="flat",
                      command=lambda c=cmd, n=ch: self.send(n, c)).pack(side="left", padx=1)


if __name__ == "__main__":
    App()
