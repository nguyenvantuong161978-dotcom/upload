"""
WATCHDOG — Theo doi lenh tu may chu qua thu muc chia se
Kiem tra \\tsclient\D\AUTO\commands\ moi 30 giay
Bao cao trang thai ve \\tsclient\D\AUTO\status\
"""
import os, sys, json, time, subprocess, logging, signal
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ═══════════════════════════════════════════
#  CAU HINH
# ═══════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNEL_DIR = os.path.dirname(BASE_DIR)

# Doc config.json
_cfg_path = os.path.join(BASE_DIR, "config.json")
CFG = {}
if os.path.isfile(_cfg_path):
    try:
        with open(_cfg_path, "r", encoding="utf-8") as f:
            CFG = json.load(f)
    except Exception:
        pass

# Auto-detect CHANNEL_CODE tu duong dan
CHANNEL_CODE = CFG.get("CHANNEL_CODE", os.path.basename(CHANNEL_DIR))
BROWSER_EXE = CFG.get("RUN_BROWSER_EXE", "")
if not BROWSER_EXE:
    BROWSER_EXE = os.path.join(CHANNEL_DIR, CHANNEL_CODE, f"{CHANNEL_CODE}.exe")

COMMANDS_DIR = r"\\tsclient\D\AUTO\commands"
STATUS_DIR = r"\\tsclient\D\AUTO\status"
CHECK_INTERVAL = 30     # giay
STATUS_INTERVAL = 60    # giay

PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")
RUN_BAT = os.path.join(BASE_DIR, "run.bat")
UPDATE_BAT = os.path.join(BASE_DIR, "update.bat")

# Trang thai
start_time = time.time()
state = "running"
current_code = ""
last_error = ""

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


def kill_all():
    """Kill tat ca: dang.py, browser, cmd."""
    logging.info("Kill tat ca process...")

    # Kill dang.py (theo window title)
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
    logging.info("Da kill tat ca.")


def detect_signal():
    """Kiem tra co file lenh trong COMMANDS_DIR khong.
    Tra ve (command, filepath) hoac None."""
    try:
        if not os.path.isdir(COMMANDS_DIR):
            return None

        # Uu tien lenh rieng cho channel truoc, roi ALL
        for prefix in [CHANNEL_CODE, "ALL"]:
            for cmd in ["kill", "update", "restart"]:
                fpath = os.path.join(COMMANDS_DIR, f"{prefix}.{cmd}")
                if os.path.isfile(fpath):
                    logging.info(f"Phat hien lenh: {prefix}.{cmd}")
                    return (cmd, fpath)
    except Exception as e:
        # \\tsclient khong san sang (RDP disconnect)
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
    """Ghi trang thai ra file JSON de may chu doc."""
    global state
    try:
        os.makedirs(STATUS_DIR, exist_ok=True)
        status_file = os.path.join(STATUS_DIR, f"{CHANNEL_CODE}.json")

        uptime = int((time.time() - start_time) / 60)
        dang_alive = is_dang_running()
        if not dang_alive and state == "running":
            state = "dang.py stopped"

        data = {
            "channel": CHANNEL_CODE,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "state": state,
            "dang_py": "running" if dang_alive else "stopped",
            "current_code": current_code,
            "last_error": last_error,
            "uptime_minutes": uptime
        }

        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception:
        # \\tsclient khong san sang
        pass


def start_run_bat():
    """Khoi dong run.bat trong process moi."""
    logging.info(f"Khoi dong run.bat...")
    subprocess.Popen(
        f'cmd /c start "" "{RUN_BAT}"',
        shell=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )


# ═══════════════════════════════════════════
#  XU LY LENH
# ═══════════════════════════════════════════

def do_restart(signal_path):
    """Kill all → xoa lenh → chay lai run.bat → thoat."""
    global state
    state = "restarting"
    write_status()
    logging.info("=== RESTART ===")
    kill_all()
    delete_signal(signal_path)
    time.sleep(3)
    start_run_bat()
    logging.info("Da restart. Thoat watchdog cu.")
    sys.exit(0)


def do_update(signal_path):
    """Kill all → chay update.bat → xoa lenh → chay lai run.bat → thoat."""
    global state
    state = "updating"
    write_status()
    logging.info("=== UPDATE ===")
    kill_all()
    time.sleep(2)

    # Chay update.bat (dong bo, cho xong)
    logging.info("Chay update.bat...")
    try:
        subprocess.run(
            f'cmd /c "{UPDATE_BAT}"',
            shell=True, timeout=600  # toi da 10 phut
        )
    except subprocess.TimeoutExpired:
        logging.error("update.bat timeout sau 10 phut.")
    except Exception as e:
        logging.error(f"update.bat loi: {e}")

    delete_signal(signal_path)
    time.sleep(3)
    start_run_bat()
    logging.info("Da update + restart. Thoat watchdog cu.")
    sys.exit(0)


def do_kill(signal_path):
    """Kill all → xoa lenh → thoat."""
    global state
    state = "killed"
    write_status()
    logging.info("=== KILL ===")
    kill_all()
    delete_signal(signal_path)
    logging.info("Da kill tat ca. Thoat watchdog.")
    sys.exit(0)


# ═══════════════════════════════════════════
#  VONG LAP CHINH
# ═══════════════════════════════════════════

def main():
    global state
    last_status_write = 0

    while True:
        try:
            # 1) Kiem tra lenh tu may chu
            sig = detect_signal()
            if sig:
                cmd, fpath = sig
                if cmd == "restart":
                    do_restart(fpath)
                elif cmd == "update":
                    do_update(fpath)
                elif cmd == "kill":
                    do_kill(fpath)

            # 2) Kiem tra dang.py con song khong
            if not is_dang_running():
                if state == "running":
                    state = "dang.py stopped"
                    logging.warning("dang.py da dung! Cho lenh restart tu may chu.")
            else:
                state = "running"

            # 3) Ghi trang thai moi 60 giay
            now = time.time()
            if now - last_status_write >= STATUS_INTERVAL:
                write_status()
                last_status_write = now

        except Exception as e:
            logging.error(f"Watchdog loi: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
