"""
WATCHDOG — Theo doi lenh tu may chu qua thu muc chia se
Kiem tra \\tsclient\D\AUTO\commands\ moi 30 giay
Bao cao trang thai ve \\tsclient\D\AUTO\status\

Lenh ho tro: run, stop, restart, update, kill
- run/stop/restart/update: watchdog VAN SONG, chi dieu khien dang.py
- kill: giet tat ca KE CA watchdog (khan cap)
"""
import os, sys, json, time, subprocess, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ═══════════════════════════════════════════
#  CAU HINH
# ═══════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNEL_DIR = os.path.dirname(BASE_DIR)

_cfg_path = os.path.join(BASE_DIR, "config.json")
CFG = {}
if os.path.isfile(_cfg_path):
    try:
        with open(_cfg_path, "r", encoding="utf-8") as f:
            CFG = json.load(f)
    except Exception:
        pass

CHANNEL_CODE = CFG.get("CHANNEL_CODE", os.path.basename(CHANNEL_DIR))
BROWSER_EXE = CFG.get("RUN_BROWSER_EXE", "")
if not BROWSER_EXE:
    BROWSER_EXE = os.path.join(CHANNEL_DIR, CHANNEL_CODE, f"{CHANNEL_CODE}.exe")

COMMANDS_DIR = r"\\tsclient\D\AUTO\commands"
STATUS_DIR = r"\\tsclient\D\AUTO\status"
CHECK_INTERVAL = 30
STATUS_INTERVAL = 60

PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")
DANG_PY = os.path.join(BASE_DIR, "dang.py")
UPDATE_BAT = os.path.join(BASE_DIR, "update.bat")

# Trang thai
start_time = time.time()
state = "idle"
last_error = ""

SUPPORTED_CMDS = ["run", "stop", "update"]

logging.info(f"Watchdog khoi dong: CHANNEL={CHANNEL_CODE}")
logging.info(f"Theo doi: {COMMANDS_DIR}")


# ═══════════════════════════════════════════
#  HAM HO TRO
# ═══════════════════════════════════════════

def is_dang_running():
    """Kiem tra dang.py co dang chay khong."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'WINDOWTITLE eq Dang Video', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10
        )
        return 'python' in result.stdout.lower()
    except Exception:
        return False


def kill_dang_and_browser():
    """Kill dang.py va browser. KHONG kill watchdog."""
    logging.info("Kill dang.py + browser...")

    # Kill dang.py
    subprocess.run(
        'taskkill /F /FI "WINDOWTITLE eq Dang Video" /T',
        shell=True, capture_output=True, timeout=15
    )
    time.sleep(2)

    # Kill browser
    exe_name = os.path.basename(BROWSER_EXE) if BROWSER_EXE else ""
    browsers = ['chrome.exe', 'msedge.exe', 'firefox.exe']
    if exe_name:
        browsers.append(exe_name)

    for b in browsers:
        subprocess.run(
            f'taskkill /F /IM "{b}" /T',
            shell=True, capture_output=True, timeout=10
        )
    time.sleep(1)
    logging.info("Da kill dang.py + browser.")


def start_dang():
    """Khoi dong dang.py trong cua so moi."""
    logging.info("Khoi dong dang.py...")
    subprocess.Popen(
        f'start "Dang Video" "{PYTHON_EXE}" "{DANG_PY}"',
        shell=True, cwd=BASE_DIR
    )


def start_all_scripts():
    """Khoi dong dang.py (va cmt.py khi can) truc tiep. KHONG qua run.bat."""
    logging.info("Khoi dong dang.py...")
    subprocess.Popen(
        f'start "Dang Video" "{PYTHON_EXE}" "{DANG_PY}"',
        shell=True, cwd=BASE_DIR
    )
    # Sau nay them cmt.py:
    # CMT_PY = os.path.join(BASE_DIR, "cmt.py")
    # if os.path.isfile(CMT_PY):
    #     subprocess.Popen(
    #         f'start "Tra loi binh luan" "{PYTHON_EXE}" "{CMT_PY}"',
    #         shell=True, cwd=BASE_DIR
    #     )


def detect_signal():
    """Kiem tra file lenh. Tra ve (command, filepath) hoac None."""
    try:
        if not os.path.isdir(COMMANDS_DIR):
            return None

        for prefix in [CHANNEL_CODE, "ALL"]:
            for cmd in SUPPORTED_CMDS:
                fpath = os.path.join(COMMANDS_DIR, f"{prefix}.{cmd}")
                if os.path.isfile(fpath):
                    logging.info(f"Phat hien lenh: {prefix}.{cmd}")
                    return (cmd, fpath)
    except Exception:
        pass
    return None


def delete_signal(fpath):
    """Xoa file lenh, retry 3 lan."""
    for _ in range(3):
        try:
            if os.path.isfile(fpath):
                os.remove(fpath)
            return True
        except Exception:
            time.sleep(1)
    return False


def write_status():
    """Ghi trang thai ra file JSON."""
    global state
    try:
        os.makedirs(STATUS_DIR, exist_ok=True)
        status_file = os.path.join(STATUS_DIR, f"{CHANNEL_CODE}.json")

        uptime = int((time.time() - start_time) / 60)
        dang_alive = is_dang_running()

        # Cap nhat state tu dong
        if dang_alive and state in ("idle", "stopped"):
            state = "running"
        elif not dang_alive and state == "running":
            state = "stopped"

        data = {
            "channel": CHANNEL_CODE,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "state": state,
            "dang_py": "running" if dang_alive else "stopped",
            "last_error": last_error,
            "uptime_minutes": uptime
        }

        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception:
        pass


# ═══════════════════════════════════════════
#  XU LY LENH (watchdog van song, tru kill)
# ═══════════════════════════════════════════

def do_run(signal_path):
    """Chay run.bat (khoi dong tat ca: dang.py, cmt.py...)."""
    global state
    delete_signal(signal_path)

    if is_dang_running():
        logging.info("dang.py da dang chay, bo qua lenh RUN.")
        return

    logging.info("=== RUN ===")
    state = "starting"
    write_status()
    kill_dang_and_browser()  # don sach truoc
    time.sleep(2)
    start_all_scripts()
    time.sleep(8)
    state = "running"
    write_status()
    logging.info("Da chay run.bat xong.")


def do_stop(signal_path):
    """Dung dang.py + browser. Watchdog van song."""
    global state
    logging.info("=== STOP ===")
    state = "stopping"
    write_status()
    kill_dang_and_browser()
    delete_signal(signal_path)
    state = "stopped"
    write_status()
    logging.info("Da stop. Watchdog van hoat dong, cho lenh tiep.")


def do_update(signal_path):
    """Kill dang.py → chay update.bat → khoi dong lai dang.py. Watchdog van song."""
    global state, last_error
    logging.info("=== UPDATE ===")
    state = "updating"
    write_status()
    kill_dang_and_browser()
    time.sleep(2)

    # Chay update.bat
    logging.info("Chay update.bat...")
    try:
        subprocess.run(
            f'cmd /c "{UPDATE_BAT}"',
            shell=True, timeout=600, cwd=BASE_DIR
        )
        logging.info("update.bat hoan tat.")
    except subprocess.TimeoutExpired:
        last_error = "update.bat timeout 10 phut"
        logging.error(last_error)
    except Exception as e:
        last_error = f"update.bat loi: {e}"
        logging.error(last_error)

    delete_signal(signal_path)
    time.sleep(3)
    start_all_scripts()
    time.sleep(8)
    state = "running"
    write_status()
    logging.info("Da update + run xong.")




# ═══════════════════════════════════════════
#  VONG LAP CHINH
# ═══════════════════════════════════════════

def main():
    global state
    last_status_write = 0

    # Kiem tra dang.py co dang chay khong khi watchdog bat dau
    if is_dang_running():
        state = "running"
    else:
        state = "idle"

    while True:
        try:
            # 1) Kiem tra lenh tu may chu
            sig = detect_signal()
            if sig:
                cmd, fpath = sig
                if cmd == "run":
                    do_run(fpath)
                elif cmd == "stop":
                    do_stop(fpath)
                elif cmd == "update":
                    do_update(fpath)

            # 2) Tu dong cap nhat state
            if state not in ("stopped", "killed", "stopping", "starting",
                             "restarting", "updating"):
                if is_dang_running():
                    state = "running"
                else:
                    state = "stopped"

            # 3) Ghi trang thai
            now = time.time()
            if now - last_status_write >= STATUS_INTERVAL:
                write_status()
                last_status_write = now

        except Exception as e:
            logging.error(f"Watchdog loi: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
