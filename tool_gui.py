# -*- coding: utf-8 -*-
"""
TOOL GUI — Bang dieu khien tong: chay an dang.py + cmt.py, theo doi log, quan ly all.

Mo GUI  -> don sach cai cu (kill dang/cmt + browser) -> chay dang.py + cmt.py AN console.
Dong GUI (X) -> tat het (dang + cmt + browser).
Chay bang pythonw.exe -> GUI khong co console den.

Nut: [Chay] [Restart Dang] [Restart Cmt] [Lay Token/Key] [Dung]
Hien: trang thai dang/cmt + uptime, so kenh/token/key, log 2 script.
"""
import os
import sys
import time
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:        # python nhung khong tu them dir script -> them de import stats
    sys.path.insert(0, BASE_DIR)

# Tcl/Tk duoc cay vao python nhung (python/tcl/...). Chi cho Tkinter biet duong dan
# truoc khi import (python embeddable khong tu set TCL_LIBRARY/TK_LIBRARY).
_tcl = os.path.join(BASE_DIR, "python", "tcl")
if os.path.isdir(_tcl):
    for _sub in os.listdir(_tcl):
        _p = os.path.join(_tcl, _sub)
        if _sub.startswith("tcl8") and os.path.isdir(_p):
            os.environ.setdefault("TCL_LIBRARY", _p)
        elif _sub.startswith("tk8") and os.path.isdir(_p):
            os.environ.setdefault("TK_LIBRARY", _p)

import tkinter as tk
PARENT = os.path.dirname(BASE_DIR)
PY = os.path.join(BASE_DIR, "python", "python.exe")
DANG = os.path.join(BASE_DIR, "dang.py")
CMT = os.path.join(BASE_DIR, "cmt.py")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
DANG_LOG = os.path.join(LOG_DIR, "dang.log")
CMT_LOG = os.path.join(LOG_DIR, "cmt.log")

CREATE_NO_WINDOW = 0x08000000
LOG_TAIL_BYTES = 60 * 1024
LOG_MAX_BYTES = 5 * 1024 * 1024


def discover_channel_exes():
    """Ten .exe browser cua cac kenh (folder <name>/<name>.exe) de kill khi dung."""
    exes = set()
    try:
        for name in os.listdir(PARENT):
            d = os.path.join(PARENT, name)
            if os.path.isdir(d) and name.lower() != "upload":
                if os.path.isfile(os.path.join(d, f"{name}.exe")):
                    exes.add(f"{name}.exe")
    except Exception:
        pass
    return exes


def kill_pid(p):
    """Kill 1 tien trinh + cay con cua no (theo PID)."""
    if p is None:
        return
    try:
        subprocess.run(f'taskkill /F /T /PID {p.pid}', shell=True, capture_output=True)
    except Exception:
        pass


def _channel_proc_names():
    """Ten tien trinh browser kenh (vd TL1-T1.exe -> 'TL1-T1')."""
    return [os.path.splitext(e)[0] for e in discover_channel_exes()]


def kill_browsers(graceful_wait=6):
    """Dong browser NHE NHANG (CloseMainWindow ~ bam X) de KHONG hong profile antidetect.
    Cho luu xong roi MOI force-kill nhung cai con ket (treo, hoi 'Save?') de relaunch duoc."""
    names = ["chrome", "msedge", "firefox"] + _channel_proc_names()
    quoted = ",".join("'" + n.replace("'", "") + "'" for n in names)
    ps = (
        f"$names=@({quoted});"
        "Get-Process -ErrorAction SilentlyContinue | "
        "Where-Object { $names -contains $_.ProcessName } | "
        "ForEach-Object { if($_.MainWindowHandle -ne 0){ $null=$_.CloseMainWindow() } }"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass
    time.sleep(graceful_wait)   # cho browser luu profile + dong sach
    # Chi force nhung cai van con song (de relaunch khong bi khoa profile)
    for b in ["chrome.exe", "msedge.exe", "firefox.exe"]:
        subprocess.run(f'taskkill /F /IM "{b}" /T', shell=True, capture_output=True)
    for exe in discover_channel_exes():
        subprocess.run(f'taskkill /F /IM "{exe}" /T', shell=True, capture_output=True)


def kill_all_scripts():
    """Kill TAT CA python.exe (dang/cmt). GUI chay pythonw.exe nen khong bi anh huong."""
    subprocess.run('taskkill /F /IM python.exe /T', shell=True, capture_output=True)


def kill_other_python():
    """Kill cac python.exe KHAC (dang/cmt) TRU chinh tien trinh hien tai.
    Dung cho updater (chay bang python.exe) de khong tu giet minh."""
    me = os.getpid()
    try:
        out = subprocess.run('tasklist /fi "imagename eq python.exe" /fo csv /nh',
                             shell=True, capture_output=True, text=True, errors="replace").stdout
        for line in out.splitlines():
            parts = [p.strip(' "') for p in line.split('","')]
            if len(parts) >= 2 and parts[1].isdigit() and int(parts[1]) != me:
                subprocess.run(f'taskkill /F /PID {parts[1]} /T', shell=True, capture_output=True)
    except Exception:
        pass


def force_kill_browsers():
    """Force-kill (cung) tat ca browser - dung khi can chac chan chet (vd truoc khi bat IPv4)."""
    for b in ["chrome.exe", "msedge.exe", "firefox.exe"]:
        subprocess.run(f'taskkill /F /IM "{b}" /T', shell=True, capture_output=True)
    for exe in discover_channel_exes():
        subprocess.run(f'taskkill /F /IM "{exe}" /T', shell=True, capture_output=True)


def browsers_alive():
    """Dem tien trinh browser con song (chrome/msedge/firefox + browser kenh)."""
    names = [b.lower() for b in ["chrome.exe", "msedge.exe", "firefox.exe"]]
    names += [e.lower() for e in discover_channel_exes()]
    try:
        out = subprocess.run('tasklist /fo csv /nh', shell=True, capture_output=True,
                             text=True, errors="replace").stdout.lower()
        return sum(out.count(n) for n in names)
    except Exception:
        return 0


def launch_hidden(script, log_path):
    """Chay 1 script AN console, log do ra file. Tra ve Popen."""
    try:
        open(log_path, "w", encoding="utf-8").close()
    except Exception:
        pass
    lf = open(log_path, "a", encoding="utf-8", errors="replace")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.Popen(
        [PY, "-u", "-X", "utf8", script],
        cwd=BASE_DIR, stdout=lf, stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW, env=env,
    )


CREATE_NEW_CONSOLE = 0x00000010

def launch_setup_console():
    """Mo 'cmt.py setup' trong 1 console RIENG (hien) de user tu chon tk + tao key.
    Tra ve Popen de GUI theo doi: setup xong -> tu chay lai dang/cmt."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.Popen(
        [PY, "-X", "utf8", "cmt.py", "setup"],
        cwd=BASE_DIR, creationflags=CREATE_NEW_CONSOLE, env=env,
    )


def trim_log(path):
    try:
        if os.path.isfile(path) and os.path.getsize(path) > LOG_MAX_BYTES:
            with open(path, "rb") as f:
                f.seek(-LOG_MAX_BYTES // 2, os.SEEK_END)
                tail = f.read()
            with open(path, "wb") as f:
                f.write(b"...(da cat bot log cu)...\n" + tail)
    except Exception:
        pass


def read_tail(path, nbytes=LOG_TAIL_BYTES):
    try:
        if not os.path.isfile(path):
            return "(chua co log)"
        with open(path, "rb") as f:
            if os.path.getsize(path) > nbytes:
                f.seek(-nbytes, os.SEEK_END)
            data = f.read()
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"(loi doc log: {e})"


def count_status():
    """(so kenh, so token, so key Gemini)."""
    nch = ntok = nkey = 0
    try:
        nch = sum(1 for n in os.listdir(PARENT)
                  if os.path.isdir(os.path.join(PARENT, n)) and n.lower() != "upload"
                  and os.path.isfile(os.path.join(PARENT, n, f"{n}.exe")))
    except Exception:
        pass
    try:
        ntok = sum(1 for f in os.listdir(os.path.join(BASE_DIR, "tokens")) if f.endswith(".json"))
    except Exception:
        pass
    try:
        cfg = json.load(open(os.path.join(BASE_DIR, "config.json"), encoding="utf-8"))
        keys = list(cfg.get("GEMINI_API_KEYS", []) or [])
        if cfg.get("GEMINI_API_KEY"):
            keys.append(cfg["GEMINI_API_KEY"])
        nkey = len(set(k for k in keys if k))
    except Exception:
        pass
    return nch, ntok, nkey


import re as _re

LANG_MAP = {1: "Spanish", 2: "Vietnamese", 3: "English", 4: "French", 5: "German",
            6: "Portuguese", 7: "Japanese", 8: "Korean", 9: "Italian", 10: "Turkish"}


def channel_lang(name):
    m = _re.search(r"-T(\d+)", name)
    return LANG_MAP.get(int(m.group(1)), "?") if m else "?"


def discover_channels():
    out = []
    try:
        for n in sorted(os.listdir(PARENT)):
            d = os.path.join(PARENT, n)
            if os.path.isdir(d) and n.lower() != "upload" and os.path.isfile(os.path.join(d, n + ".exe")):
                out.append(n)
    except Exception:
        pass
    return out


def has_token(name):
    return os.path.isfile(os.path.join(BASE_DIR, "tokens", name + ".json"))


def replied_count(name):
    try:
        with open(os.path.join(BASE_DIR, "replied", name + ".txt"), encoding="utf-8", errors="ignore") as f:
            return sum(1 for ln in f if ln.strip())
    except Exception:
        return 0


CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def _dedupe(keys):
    seen, out = set(), []
    for k in keys:
        k = (k or "").strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_gemini_keys():
    """Tat ca key Gemini hien co (gop GEMINI_API_KEYS + GEMINI_API_KEY)."""
    try:
        cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
        keys = list(cfg.get("GEMINI_API_KEYS", []) or [])
        if cfg.get("GEMINI_API_KEY"):
            keys.append(cfg["GEMINI_API_KEY"])
        return _dedupe(keys)
    except Exception:
        return []


def save_gemini_keys(keys):
    """Ghi danh sach key vao config.json (gop het vao GEMINI_API_KEYS)."""
    try:
        cfg = json.load(open(CONFIG_PATH, encoding="utf-8")) if os.path.isfile(CONFIG_PATH) else {}
    except Exception:
        cfg = {}
    out = _dedupe(keys)
    cfg["GEMINI_API_KEYS"] = out
    cfg["GEMINI_API_KEY"] = ""   # gop het vao list cho gon
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return len(out)


def read_version():
    """Doc so version tu file VERSION (tu dong cap nhat khi code len ban moi)."""
    try:
        with open(os.path.join(BASE_DIR, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "?"


# ---- Khoa chi 1 instance GUI chay cung luc ----
_SINGLE_INSTANCE_MUTEX = None


def acquire_single_instance():
    """Giu mutex Windows. True = OK (giu khoa); False = da co GUI khac dang chay."""
    global _SINGLE_INSTANCE_MUTEX
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.CreateMutexW(None, False, "TL_TOOL_GUI_SINGLETON")
        if k.GetLastError() == 183:        # ERROR_ALREADY_EXISTS
            if h:
                k.CloseHandle(h)
            return False
        _SINGLE_INSTANCE_MUTEX = h
        return True
    except Exception:
        return True                        # loi -> van cho chay, khong chan oan


def release_single_instance():
    """Nha khoa (truoc khi Update tu mo lai GUI moi)."""
    global _SINGLE_INSTANCE_MUTEX
    try:
        if _SINGLE_INSTANCE_MUTEX:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(_SINGLE_INSTANCE_MUTEX)
            _SINGLE_INSTANCE_MUTEX = None
    except Exception:
        pass


# ---- Update tu GitHub ----
GITHUB_ZIP = "https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
UPDATE_FILES = ["cmt.py", "dang.py", "tool_gui.py", "stats.py", "run.bat", "update.bat",
                "setup.bat", "lay_token.bat", "VERSION", "tkinter-embed-py311.zip"]


def _ps(cmd):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass


def _set_ipv4(enable):
    verb = "Enable" if enable else "Disable"
    _ps(f"Get-NetAdapter | ForEach-Object {{ {verb}-NetAdapterBinding -Name $_.Name "
        f"-ComponentID ms_tcpip -ErrorAction SilentlyContinue }}")
    if enable:
        _ps("Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object { "
            "Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex "
            "-ServerAddresses 8.8.8.8 -ErrorAction SilentlyContinue }")


def run_updater():
    """Chay o TIEN TRINH RIENG (console hien, GUI da dong) -> tai code moi -> mo lai GUI.
    Tach khoi GUI de GUI KHONG bi 'not responding' luc cap nhat."""
    import urllib.request, zipfile, tempfile, shutil

    def say(m):
        print("[UPDATE] " + m, flush=True)

    def open_gui():
        # Detach bang 'start' -> GUI moi KHONG la con cua updater, tranh bi kill_all_scripts /T giet theo
        try:
            pyw = os.path.join(BASE_DIR, "python", "pythonw.exe")
            subprocess.Popen(f'start "" "{pyw}" tool_gui.py', shell=True, cwd=BASE_DIR)
        except Exception as e:
            say("Mo lai GUI loi: " + repr(e)[:80])

    try:
        say("Cho GUI cu dong...")
        time.sleep(3)
        say("Dung dang/cmt + dong het browser...")
        kill_other_python()          # KHONG dung kill_all_scripts (se tu giet updater)
        for _ in range(8):
            force_kill_browsers()
            if browsers_alive() == 0:
                break
            time.sleep(1)
        say("Bat IPv4 de tai...")
        _set_ipv4(True)
        time.sleep(7)
        say("Tai code moi tu GitHub...")
        tmp = tempfile.gettempdir()
        zp = os.path.join(tmp, "tl_update.zip")
        ex = os.path.join(tmp, "tl_update_ex")
        urllib.request.urlretrieve(GITHUB_ZIP, zp)
        if os.path.isdir(ex):
            shutil.rmtree(ex, ignore_errors=True)
        with zipfile.ZipFile(zp) as z:
            z.extractall(ex)
        subdirs = [os.path.join(ex, d) for d in os.listdir(ex) if os.path.isdir(os.path.join(ex, d))]
        if not subdirs:
            raise Exception("ZIP rong")
        src = subdirs[0]
        say("Copy file moi...")
        for f in UPDATE_FILES:
            sp = os.path.join(src, f)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(BASE_DIR, f))
        si = os.path.join(src, "icon")
        if os.path.isdir(si):
            shutil.copytree(si, os.path.join(BASE_DIR, "icon"), dirs_exist_ok=True)
        if not os.path.isfile(os.path.join(BASE_DIR, "python", "tkinter", "__init__.py")):
            zt = os.path.join(BASE_DIR, "tkinter-embed-py311.zip")
            if os.path.isfile(zt):
                with zipfile.ZipFile(zt) as z:
                    z.extractall(os.path.join(BASE_DIR, "python"))
        say("Tat IPv4...")
        _set_ipv4(False)
        time.sleep(2)
        say("XONG. Mo lai GUI ban moi...")
        open_gui()
        time.sleep(2)
    except Exception as e:
        say("LOI cap nhat: " + repr(e)[:140])
        try:
            _set_ipv4(False)
        except Exception:
            pass
        say("Mo lai GUI...")
        open_gui()
        time.sleep(6)   # giu console de doc loi


BG = "#1e1e2e"
PANEL = "#11111b"
FG = "#cdd6f4"
GREEN = "#a6e3a1"
RED = "#f38ba8"
BLUE = "#89b4fa"
YELLOW = "#f9e2af"


class App:
    def __init__(self):
        self.proc_dang = None
        self.proc_cmt = None
        self.t_dang = 0
        self.t_cmt = 0
        self.running = False          # True khi dang o che do chay (de watchdog tu restart)
        self.n_rl_dang = 0            # so lan tu dong restart dang
        self.n_rl_cmt = 0            # so lan tu dong restart cmt
        self.last_rl_dang = 0
        self.last_rl_cmt = 0
        self.proc_setup = None        # tien trinh 'cmt.py setup' (Lay Token/Key) dang mo
        self.last_temp_clean = time.time()
        self._tick = 0
        self._ram_txt = ""
        self._updating = False
        self._update_msg = ""

        self.root = tk.Tk()
        self.root.title(f"TOOL DIEU KHIEN — Dang + Cmt   v{read_version()}")
        self.root.configure(bg=BG)
        self.root.geometry("1040x620")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=10, pady=(8, 2))
        self.lbl_dang = tk.Label(top, text="● Dang: ...", font=("Consolas", 11, "bold"), fg=GREEN, bg=BG)
        self.lbl_dang.pack(side="left", padx=(2, 18))
        self.lbl_cmt = tk.Label(top, text="● Cmt: ...", font=("Consolas", 11, "bold"), fg=GREEN, bg=BG)
        self.lbl_cmt.pack(side="left")

        btns = tk.Frame(self.root, bg=BG)
        btns.pack(fill="x", padx=10, pady=(0, 6))
        for txt, cmd, clr in [
            ("↻ Restart Dang", self.restart_dang, BLUE),
            ("↻ Restart Cmt", self.restart_cmt, BLUE),
            ("🔑 Lay Token/Key", self.do_setup, YELLOW),
            ("✎ Key Gemini", self.do_keys, GREEN),
            ("⬇ Update", self.do_update, "#fab387"),
        ]:
            tk.Button(btns, text=txt, command=cmd, bg=clr, fg=BG,
                      font=("Segoe UI", 9, "bold"), relief="flat", padx=8).pack(side="left", padx=3)
        self.lbl_sum = tk.Label(btns, text="", font=("Consolas", 9), fg=YELLOW, bg=BG)
        self.lbl_sum.pack(side="right", padx=6)

        # ----- BANG TONG QUAN (nhin phat hieu) -----
        ovf = tk.Frame(self.root, bg=BG)
        ovf.pack(fill="x", padx=10, pady=(0, 6))
        tk.Label(ovf, text="TONG QUAN CAC KENH  (VIDEO + REPLY = so lieu HOM NAY)",
                 font=("Segoe UI", 9, "bold"), fg=YELLOW, bg=BG).pack(anchor="w")
        _oh = max(4, min(14, len(discover_channels()) + 3))
        self.txt_over = tk.Text(ovf, bg=PANEL, fg=FG, font=("Consolas", 10),
                                relief="flat", height=_oh, wrap="none")
        self.txt_over.pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)
        tk.Label(body, text="DANG (dang video)", font=("Segoe UI", 9, "bold"), fg=FG, bg=BG).grid(row=0, column=0, sticky="w")
        tk.Label(body, text="CMT (tra loi binh luan)", font=("Segoe UI", 9, "bold"), fg=FG, bg=BG).grid(row=0, column=1, sticky="w")
        self.txt_dang = tk.Text(body, bg=PANEL, fg=FG, font=("Consolas", 8), relief="flat", wrap="none")
        self.txt_dang.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.txt_cmt = tk.Text(body, bg=PANEL, fg=FG, font=("Consolas", 8), relief="flat", wrap="none")
        self.txt_cmt.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        self.start_all()
        self.refresh()
        self.root.mainloop()

    # ---- dieu khien ----
    def start_all(self):
        kill_all_scripts()
        kill_browsers()
        time.sleep(1.2)
        self.proc_dang = launch_hidden(DANG, DANG_LOG)
        self.t_dang = time.time()
        self.proc_cmt = launch_hidden(CMT, CMT_LOG)
        self.t_cmt = time.time()
        self.running = True

    def stop_all(self):
        self.running = False
        kill_pid(self.proc_dang)
        kill_pid(self.proc_cmt)
        kill_all_scripts()
        kill_browsers()
        self.proc_dang = None
        self.proc_cmt = None
        self.t_dang = self.t_cmt = 0

    def restart_dang(self):
        kill_pid(self.proc_dang)
        kill_browsers()
        time.sleep(1)
        self.proc_dang = launch_hidden(DANG, DANG_LOG)
        self.t_dang = time.time()
        self.running = True

    def restart_cmt(self):
        kill_pid(self.proc_cmt)
        time.sleep(0.5)
        self.proc_cmt = launch_hidden(CMT, CMT_LOG)
        self.t_cmt = time.time()
        self.running = True

    def do_setup(self):
        # Tam dung dang/cmt (tranh tranh browser) -> mo setup HIEN. Setup xong se TU CHAY LAI.
        self.stop_all()
        time.sleep(1)
        self.proc_setup = launch_setup_console()

    def clean_temp(self):
        # Don rac %temp% (file dang dung bi khoa se tu dong bo qua)
        try:
            subprocess.run('cmd /c del /q /f /s "%temp%\\*.*"', shell=True, capture_output=True)
        except Exception:
            pass
        self.last_temp_clean = time.time()

    def do_keys(self):
        # Hop thoai nhap/sua/xoa key Gemini -> luu config.json -> restart cmt de ap dung
        win = tk.Toplevel(self.root)
        win.title("Quan ly Key Gemini")
        win.configure(bg=BG)
        win.geometry("580x430")
        tk.Label(win, text="Moi key 1 dong. Them key moi / xoa key chet / sua roi bam LUU.\n"
                           "Luu xong cmt se tu restart de dung key moi.",
                 font=("Segoe UI", 9), fg=FG, bg=BG, justify="left").pack(anchor="w", padx=10, pady=8)
        box = tk.Text(win, bg=PANEL, fg=FG, font=("Consolas", 9), relief="flat", wrap="none")
        box.pack(fill="both", expand=True, padx=10)
        box.insert("1.0", "\n".join(load_gemini_keys()))
        bar = tk.Frame(win, bg=BG)
        bar.pack(fill="x", padx=10, pady=8)
        info = tk.Label(bar, text="", fg=GREEN, bg=BG, font=("Segoe UI", 9))
        info.pack(side="left")

        def do_save():
            n = save_gemini_keys(box.get("1.0", "end").splitlines())
            info.config(text=f"Da luu {n} key. Restart cmt...")
            self.restart_cmt()
            win.after(900, win.destroy)

        tk.Button(bar, text="LUU", command=do_save, bg=GREEN, fg=BG,
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=12).pack(side="right", padx=3)
        tk.Button(bar, text="Dong", command=win.destroy, bg=RED, fg=BG,
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=12).pack(side="right", padx=3)
        win.transient(self.root)
        win.grab_set()

    def do_update(self):
        # Dong GUI -> chay update.bat (cmd rieng). update.bat tu: kill tool + tai code
        # moi + mo lai run.bat (GUI). cmd la tien trinh rieng nen GUI khong bi 'not responding'.
        if self._updating:
            return
        self._updating = True
        try:
            subprocess.Popen(f'start "" "{os.path.join(BASE_DIR, "update.bat")}"',
                             shell=True, cwd=BASE_DIR)
        except Exception:
            pass
        time.sleep(0.6)
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    # ---- hien thi ----
    def _alive(self, p):
        return p is not None and p.poll() is None

    def _uptime(self, t):
        if not t:
            return ""
        s = int(time.time() - t)
        h, s = divmod(s, 3600)
        m, _ = divmod(s, 60)
        return f"{h}h{m:02d}m"

    def _ram_mb(self):
        """Tong RAM cua cac python.exe (dang+cmt) -> de thay 'nang' hay khong."""
        try:
            out = subprocess.run('tasklist /fi "imagename eq python.exe" /fo csv /nh',
                                 shell=True, capture_output=True, text=True).stdout
            kb = 0
            for line in out.splitlines():
                line = line.strip()
                if not line:
                    continue
                last = line.split('","')[-1].strip(' "')
                digits = ''.join(c for c in last if c.isdigit())
                if digits:
                    kb += int(digits)
            mb = kb // 1024
            return f"{mb}MB" if mb else "..."
        except Exception:
            return "..."

    def _overview_text(self):
        chs = discover_channels()
        if not chs:
            return "(chua phat hien kenh nao)"
        try:
            import stats
        except Exception:
            stats = None
        out = [f"{'KENH':<11}{'NGON NGU':<12}{'TOKEN':<7}{'VIDEO':<8}REPLY"]
        out.append("-" * 44)
        for c in chs:
            tok = "✓" if has_token(c) else "✗"
            v, r = stats.today_counts(c) if stats else (0, 0)
            out.append(f"{c:<11}{channel_lang(c):<12}{tok:<7}{v:<8}{r}")
        return "\n".join(out)

    def refresh(self):
        try:
            self._tick += 1
            now = time.time()

            # Dang cap nhat -> hien tien trinh, khong lam gi khac
            if self._updating:
                self.lbl_dang.config(text="⬇ DANG CAP NHAT: " + self._update_msg, fg=YELLOW)
                self.lbl_cmt.config(text="(dung khong dong cua so)", fg=YELLOW)
                self.root.after(700, self.refresh)
                return

            # 1) Setup xong (cua so setup da dong) -> tu chay lai dang/cmt
            if self.proc_setup is not None and self.proc_setup.poll() is not None:
                self.proc_setup = None
                self.start_all()

            da = self._alive(self.proc_dang)
            ca = self._alive(self.proc_cmt)

            # 2) Watchdog: dang chay ma tien trinh chet cung -> tu khoi dong lai (cho 20s tranh loop)
            if self.running and self.proc_setup is None:
                if not da and now - self.last_rl_dang > 20:
                    self.proc_dang = launch_hidden(DANG, DANG_LOG)
                    self.t_dang = now
                    self.last_rl_dang = now
                    self.n_rl_dang += 1
                    da = True
                if not ca and now - self.last_rl_cmt > 20:
                    self.proc_cmt = launch_hidden(CMT, CMT_LOG)
                    self.t_cmt = now
                    self.last_rl_cmt = now
                    self.n_rl_cmt += 1
                    ca = True

            # 3) Don rac %temp% dinh ky (6 tieng/lan) cho khoi nang
            if now - self.last_temp_clean > 6 * 3600:
                self.clean_temp()

            # 4) RAM (cap nhat ~12s/lan vi tasklist hoi nang)
            if self._tick % 5 == 1:
                self._ram_txt = self._ram_mb()

            if self.proc_setup is not None:
                self.lbl_dang.config(text="● Dang: TAM DUNG (dang lay token/key)", fg=YELLOW)
                self.lbl_cmt.config(text="● Cmt: TAM DUNG (dang lay token/key)", fg=YELLOW)
            else:
                rl_d = f"  [tu restart {self.n_rl_dang}]" if self.n_rl_dang else ""
                rl_c = f"  [tu restart {self.n_rl_cmt}]" if self.n_rl_cmt else ""
                self.lbl_dang.config(text=f"● Dang: {'CHAY ' + self._uptime(self.t_dang) if da else 'DUNG'}{rl_d}",
                                     fg=GREEN if da else RED)
                self.lbl_cmt.config(text=f"● Cmt: {'CHAY ' + self._uptime(self.t_cmt) if ca else 'DUNG'}{rl_c}",
                                    fg=GREEN if ca else RED)

            nch, ntok, nkey = count_status()
            self.lbl_sum.config(text=f"v{read_version()} | {nch} kenh | {ntok} token | {nkey} key | RAM {self._ram_txt}")

            # Bang tong quan cac kenh
            self.txt_over.config(state="normal")
            self.txt_over.delete("1.0", "end")
            self.txt_over.insert("1.0", self._overview_text())
            self.txt_over.config(state="disabled")

            trim_log(DANG_LOG)
            trim_log(CMT_LOG)
            self._set_text(self.txt_dang, read_tail(DANG_LOG))
            self._set_text(self.txt_cmt, read_tail(CMT_LOG))
        except Exception:
            pass
        finally:
            self.root.after(2500, self.refresh)

    def _set_text(self, widget, content):
        at_end = True
        try:
            at_end = widget.yview()[1] > 0.93
        except Exception:
            pass
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content[-20000:])
        if at_end:
            widget.see("end")
        widget.config(state="disabled")

    def on_close(self):
        self.stop_all()
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)


if __name__ == "__main__":
    if not acquire_single_instance():
        try:
            import tkinter.messagebox as _mb
            _r = tk.Tk()
            _r.withdraw()
            _mb.showinfo("Tool dang chay", "Tool da chay roi (chi 1 phien ban). Khong mo them.")
            _r.destroy()
        except Exception:
            pass
        os._exit(0)
    App()
