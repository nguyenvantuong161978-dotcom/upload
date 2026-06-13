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
import time
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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


def kill_browsers():
    for b in ["chrome.exe", "msedge.exe", "firefox.exe"]:
        subprocess.run(f'taskkill /F /IM "{b}" /T', shell=True, capture_output=True)
    for exe in discover_channel_exes():
        subprocess.run(f'taskkill /F /IM "{exe}" /T', shell=True, capture_output=True)


def kill_all_scripts():
    """Kill TAT CA python.exe (dang/cmt). GUI chay pythonw.exe nen khong bi anh huong."""
    subprocess.run('taskkill /F /IM python.exe /T', shell=True, capture_output=True)


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


def launch_setup_visible():
    """Chay 'cmt.py setup' trong console HIEN de user tu chon tk + tao key Gemini."""
    subprocess.Popen(f'start "Lay Token + Key Gemini" "{PY}" cmt.py setup',
                     cwd=BASE_DIR, shell=True)


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

        self.root = tk.Tk()
        self.root.title("TOOL DIEU KHIEN — Dang + Cmt")
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
            ("▶ Chay", self.start_all, GREEN),
            ("↻ Restart Dang", self.restart_dang, BLUE),
            ("↻ Restart Cmt", self.restart_cmt, BLUE),
            ("🔑 Lay Token/Key", self.do_setup, YELLOW),
            ("■ Dung", self.stop_all, RED),
        ]:
            tk.Button(btns, text=txt, command=cmd, bg=clr, fg=BG,
                      font=("Segoe UI", 9, "bold"), relief="flat", padx=8).pack(side="left", padx=3)
        self.lbl_sum = tk.Label(btns, text="", font=("Consolas", 9), fg=YELLOW, bg=BG)
        self.lbl_sum.pack(side="right", padx=6)

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

    def stop_all(self):
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

    def restart_cmt(self):
        kill_pid(self.proc_cmt)
        time.sleep(0.5)
        self.proc_cmt = launch_hidden(CMT, CMT_LOG)
        self.t_cmt = time.time()

    def do_setup(self):
        # Dung dang/cmt de tranh tranh browser, roi mo setup HIEN cho user tu thao tac
        self.stop_all()
        time.sleep(1)
        launch_setup_visible()

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

    def refresh(self):
        da = self._alive(self.proc_dang)
        ca = self._alive(self.proc_cmt)
        self.lbl_dang.config(text=f"● Dang: {'CHAY ' + self._uptime(self.t_dang) if da else 'DUNG'}",
                             fg=GREEN if da else RED)
        self.lbl_cmt.config(text=f"● Cmt: {'CHAY ' + self._uptime(self.t_cmt) if ca else 'DUNG'}",
                            fg=GREEN if ca else RED)
        nch, ntok, nkey = count_status()
        self.lbl_sum.config(text=f"{nch} kenh | {ntok} token | {nkey} key Gemini")

        trim_log(DANG_LOG)
        trim_log(CMT_LOG)
        self._set_text(self.txt_dang, read_tail(DANG_LOG))
        self._set_text(self.txt_cmt, read_tail(CMT_LOG))
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
    App()
