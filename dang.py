
import os,logging, time,random
from types import SimpleNamespace
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pyautogui
import pyperclip
from datetime import datetime, timedelta  # ⬅️ thêm timedelta
import ctypes
import shutil

# Bật DPI-aware để PyAutoGUI/Windows dùng cùng hệ quy chiếu
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

def _get_scale():
    """Tính tỉ lệ (screenshot px) / (logical px) theo 2 trục."""
    sw, sh = pyautogui.size()
    iw, ih = pyautogui.screenshot().size
    sx = iw / (sw or 1)
    sy = ih / (sh or 1)
    return sx, sy

def _to_logical(x, y):
    """Đổi toạ độ từ ảnh chụp (kết quả locateCenterOnScreen) sang logical px để moveTo/click."""
    sx, sy = _get_scale()
    return int(x / sx), int(y / sy)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
pyautogui.FAILSAFE = False  # tránh dừng khẩn cấp khi chuột ra góc

# ================== CẤU HÌNH TRỰC TIẾP ==================
CHANNEL_CODE       = "KA2-T2"    # cột AI
RUN_BROWSER_EXE   = r"C:\Users\Administrator\Documents\KA2-T2\KA2-T2\KA2-T2.exe"
# Thư mục video local (trên máy ảo)
LOCAL_DONE_ROOT   = r"C:\Users\Administrator\Desktop\done"
# Thư mục video trên máy chủ (qua RDP)
SERVER_DONE_ROOT  = r"Z:\AUTO\done"



SPREADSHEET_NAME   = "KA"
INPUT_SHEET        = "INPUT"
SOURCE_SHEET = "NGUON"  # sheet nguồn để cập nhật trạng thái
CREDENTIAL_PATH    = "creds.json"
STATUS_OK          = "EDIT XONG" # cột AV
STATUS_COL = 48  # AV = cột 48















# CỘT: BB=53, BC=54 (zero-based) — thêm:
IDX_DATE_BI = 60  # BI
IDX_TIME_BJ = 61  # BJ
IDX_LINK_BD = 55  # BD
IDX_LINK_BE = 56  # BE
IDX_LINK_BF = 57  # BF
IDX_LINK_BG = 58  # BG

# ================== CẤU HÌNH ĐƯỜNG DẪN ==================
UPLOAD_URL        = "https://www.youtube.com/upload"
# Mẫu đường dẫn thư mục video theo mã
FOLDER_PATTERN    = os.path.join(LOCAL_DONE_ROOT, "{code}")



# Thư mục icon (nằm cạnh file py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "icon")
TEMPLATE_SELECT_BTN = os.path.join(ICON_DIR, "chonfile.png")
TEMPLATE_DANHSACHPHAT = os.path.join(ICON_DIR, "danhsachphat.png")
TEMPLATE_DANGKY = os.path.join(ICON_DIR, "dangky.png")
TEMPLATE_NEXT_BTN   = os.path.join(ICON_DIR, "tiep.png")  # ảnh “Tiếp” trên trang metadata
TEMPLATE_OPEN_READY = os.path.join(ICON_DIR, "open.png")  # ảnh báo trang browser đã sẵn sàng
TEMPLATE_BUOC2 = os.path.join(ICON_DIR, "buoc2.png")  # anchor hiển thị rõ đã vào màn Bước 2
TEMPLATE_CHON_ENDSCREEN = os.path.join(ICON_DIR, "chonmanhinhketthuc.png")  # nút/ô chọn màn hình kết thúc trong editor
TEMPLATE_STEP2_THEM = os.path.join(ICON_DIR, "them.png")  # xác nhận đã sang bước 2
TEMPLATE_DONE       = os.path.join(ICON_DIR, "xong.png")  # nút/ảnh “xong”
TEMPLATE_SAVE       = os.path.join(ICON_DIR, "luu.png")   # nút “lưu”
TEMPLATE_ENDSCREEN  = os.path.join(ICON_DIR, "manhinhketthuc.png")  # xác nhận đã về màn “Màn hình kết thúc”
TEMPLATE_CHONVIDEO_CUTHE = os.path.join(ICON_DIR, "chonmotvideocuthe.png")  # UI “Chọn một video cụ thể”
TEMPLATE_THE1      = os.path.join(ICON_DIR, "the1.png")
TEMPLATE_HENLICH = os.path.join(ICON_DIR, "henlich.png")  # Ảnh nút hẹn lịch
TEMPLATE_SCHEDULE_PUBLISH = os.path.join(ICON_DIR, "lenlich.png")  # nút Lên lịch
TEMPLATE_DA_LEN_LICH = os.path.join(ICON_DIR, "dalenlichchovideo.png")  # ✅ ảnh xác nhận đã lên lịch cho video
TEMPLATE_FILENAME = os.path.join(ICON_DIR, "filename.png")
TEMPLATE_TAITEPLEN = os.path.join(ICON_DIR, "taiteplen.png")  # nút/ô tải tệp lên phụ đề
TEMPLATE_KETTHUC_OK = os.path.join(ICON_DIR, "ketthucok.png")  # xác nhận đã về màn 'Màn hình kết thúc'
TEMPLATE_THE        = os.path.join(ICON_DIR, "the.png")        # nút 'Thẻ' (Cards)
TEMPLATE_TAGVIDEO   = os.path.join(ICON_DIR, "tagvideo.png")   # ảnh gợi ý video khi dán link
TEMPLATE_TIME = os.path.join(ICON_DIR, "time.png")
TEMPLATE_TIEPTUC   = os.path.join(ICON_DIR, "tieptuc.png")  # nút/ô 'Tiếp tục' để mở hộp thoại Open SRT
TEMPLATE_CHEDO_HIEN_THI = os.path.join(ICON_DIR, "chedohienthi.png")


# ================== THAM SỐ NGẪU NHIÊN (dễ chỉnh) ==================
RANDOM = SimpleNamespace(
    # thời gian nghỉ nhỏ
    tiny=(0.5, 0.9),
    small=(1.2, 2.0),
    medium=(2.5, 4.0),
    long=(5.0, 8.0),

    # di chuyển chuột
    mouse_move=(0.25, 0.45),

    # khoảng nghỉ khi retry dò hình ảnh
    retry_screen_interval=(1.2, 2.0),

    # RDP / Browser


    browser_launch_wait_sec=(12, 20),


    # nhận diện ảnh
    click_timeout_sec=(120, 180),        # chờ ảnh hiển thị tới 2–3 phút
    click_confidence=(0.85, 0.95),       # bớt khó tính khi hình hơi mờ

    # Bước 2 (subtitles, end screen) thường load lâu
    step2_load_timeout_sec=(150, 240),   # 2.5–4 phút
)


def r(a, b):  # random float trong [a, b]
    return random.uniform(a, b)

def cleanup_posted_codes():
    """Xóa thư mục local của các mã đã có trạng thái 'ĐÃ ĐĂNG' trong Sheet."""
    logging.info("🧹 Dọn các mã đã đăng...")
    client = gs_client()
    ws = client.open(SPREADSHEET_NAME).worksheet(INPUT_SHEET)
    rows = ws.get_all_values()

    for row in rows[1:]:
        code = row[0].strip() if len(row) > 0 else ""
        status = row[STATUS_COL-1].strip() if len(row) >= STATUS_COL else ""
        if code and status.upper() == "ĐÃ ĐĂNG":
            folder_path = os.path.join(LOCAL_DONE_ROOT, code)
            if os.path.isdir(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    logging.info(f"🗑️ Đã xóa: {folder_path}")
                except Exception as e:
                    logging.warning(f"Không xóa được {folder_path}: {e}")



def click_once(x, y):
    lx, ly = _to_logical(x, y)
    pyautogui.moveTo(lx, ly, duration=r(*RANDOM.mouse_move))
    pyautogui.click(lx, ly)

def _parse_date(s):
    for f in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), f).date()
        except: pass
    return None

def _parse_time(s):
    for f in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s.strip(), f).time()
        except: pass
    return None



def close_browsers_gently_in_rdp():
    # Clear temp directory first
    logging.info("Xóa các file trong thư mục %temp%...")
    open_run_and_execute('cmd /c del /q /f /s "%temp%\\*.*" >nul 2>&1')
    rsleep("small")
    
    exebase = os.path.splitext(os.path.basename(RUN_BROWSER_EXE))[0]
    # 🟡 Lần 1: đóng nhẹ bằng CloseMainWindow() cho chrome, msedge, firefox, exebase
    ps_close = (
        "$names=@('chrome','msedge','firefox','{ex}');"
        "$procs=Get-Process -ErrorAction SilentlyContinue | ?{{ $names -contains $_.ProcessName }};"
        "foreach($p in $procs){{ if($p.MainWindowHandle -ne 0){{ $null=$p.CloseMainWindow() }} }}"
    ).format(ex=exebase)
    open_run_and_execute(f'powershell -NoProfile -WindowStyle Hidden -Command "{ps_close}"')
    rsleep("small")


    # 🟡 Lần 2: Stop-Process -Force (PowerShell) — bao gồm cả tiến trình bắt đầu bằng 'firefox' (nếu có)
    ps_kill = (
        "$names=@('chrome','msedge','firefox','{ex}');"
        # kill exact names first
        "foreach($n in $names){{ $p=Get-Process -Name $n -ErrorAction SilentlyContinue; if($p){{ $p | Stop-Process -Force }}}};"
        # thêm một lớp nữa để bắt các tiến trình có tiền tố firefox* (nếu có tiến trình con tên hơi khác)
        "$pf=Get-Process -ErrorAction SilentlyContinue | Where-Object {{ $_.ProcessName -like 'firefox*' }}; if($pf){{ $pf | Stop-Process -Force }};"
    ).format(ex=exebase)
    open_run_and_execute(f'powershell -NoProfile -WindowStyle Hidden -Command "{ps_kill}"')
    rsleep("small")

    # 🟡 Lần 3: taskkill kiểu “skill” mạnh (chắc chắn kill tất cả các tiến trình có liên quan)
    exename = os.path.basename(RUN_BROWSER_EXE)
    skill = (
        'cmd /c '
        'taskkill /F /IM chrome.exe /T 2>nul & '
        'taskkill /F /IM msedge.exe /T 2>nul & '
        'taskkill /F /IM firefox.exe /T 2>nul & '
        'taskkill /F /IM "{ex}" /T 2>nul'
    ).format(ex=exename)
    open_run_and_execute(skill)
    rsleep("small")



def rsleep(bucket="small"):
    lo, hi = getattr(RANDOM, bucket)
    time.sleep(r(lo, hi))

def paste_text(text: str):
    if text is None:
        return
    pyperclip.copy(text)
    rsleep("tiny")
    pyautogui.hotkey('ctrl', 'v')
    rsleep("tiny")

def move_click(x, y):
    # giữ tên cũ cho toàn bộ code bên dưới
    click_once(x, y)


# ================== GOOGLE SHEETS ==================

def gs_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIAL_PATH, scope)
    return gspread.authorize(creds)

def get_rows(client, sheet_name):
    return client.open(SPREADSHEET_NAME).worksheet(sheet_name).get_all_values()

def norm(s):
    return s.strip() if isinstance(s, str) else None






def find_row_by_code(rows, code):
    for r in rows[1:]:
        if r and len(r) > 0 and norm(r[0]) == code:
            return r
    return None



def update_source_status(client, code, status="ĐÃ ĐĂNG"):
    """
    Tìm dòng trong sheet NGUON có cột G == code, rồi ghi 'ĐÃ ĐĂNG' vào cột M.
    - Cột G (0-based index 6), cột M (0-based index 12).
    - update_cell dùng index 1-based, nên cộng +1 và +2 tương ứng với header.
    """
    try:
        ws = client.open(SPREADSHEET_NAME).worksheet(SOURCE_SHEET)
        rows = ws.get_all_values()
        for i, r in enumerate(rows[1:], start=2):  # bỏ header -> bắt đầu từ dòng 2
            if len(r) > 12 and norm(r[6]) == code:
                ws.update_cell(i, 13, status)  # cột M là 13 (1-based)
                logging.info("Đã cập nhật trạng thái '%s' cho mã %s ở dòng %d (sheet NGUON).", status, code, i)
                return True
        logging.warning("Không tìm thấy mã %s trong sheet NGUON (cột G).", code)
        return False
    except Exception as e:
        logging.error("Lỗi khi cập nhật trạng thái sheet NGUON: %s", e)
        return False


# ================== HỖ TRỢ RDP & WINDOW ==================


# ================== AUTOMATION TRÌNH DUYỆT ==================
def open_run_and_execute(command_line):
    pyautogui.hotkey('win', 'r'); rsleep("small")

    # Thử paste bằng clipboard
    try:
        pyperclip.copy(command_line)
        rsleep("tiny")
        pyautogui.hotkey('ctrl', 'v')
        rsleep("tiny")
    except Exception as e:
        logging.warning("Paste vào Run bị lỗi: %s -> fallback typewrite", e)
        pyautogui.typewrite(command_line, interval=0.02)

    pyautogui.press('enter'); rsleep("medium")



def wait_and_click_image(img_path, timeout_sec=30, confidence=0.85):
    """Chờ ảnh và click với cơ chế tự động giảm dần độ trùng khớp."""
    logging.info("Chờ ảnh (click): %s ...", img_path)
    end = time.time() + timeout_sec
    
    # Giảm dần độ trùng khớp qua nhiều mức
    confidence_levels = [confidence, 0.8, 0.75, 0.7, 0.65, 0.6]
    
    while time.time() < end:
        for conf_level in confidence_levels:
            try:
                pos = pyautogui.locateCenterOnScreen(img_path, confidence=conf_level)
                if pos:
                    click_once(pos.x, pos.y)
                    logging.info("Đã click ảnh: %s tại (%d, %d) với độ trùng khớp %.2f", img_path, pos.x, pos.y, conf_level)
                    return True
            except Exception:
                pass
        time.sleep(r(*RANDOM.retry_screen_interval))
    
    logging.error("Không tìm thấy ảnh trong ~%ss: %s (sau khi thử tất cả các mức độ trùng khớp)", timeout_sec, img_path)
    return False
def wait_image(img_path, timeout_sec=30, confidence=0.85):
    """Chờ ảnh xuất hiện (KHÔNG click). Trả về tọa độ tâm nếu thấy, None nếu hết hạn."""
    logging.info("Chờ ảnh (không click): %s ...", img_path)
    end = time.time() + timeout_sec
    last_err = None
    while time.time() < end:
        try:
            pos = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if pos:
                logging.info("Đã thấy ảnh: %s tại (%d, %d)", img_path, pos.x, pos.y)
                return pos
        except Exception as e:
            last_err = e
        time.sleep(r(*RANDOM.retry_screen_interval))
    if last_err:
        logging.debug("wait_image last error: %s", last_err)
    logging.error("Hết thời gian chờ ảnh: %s", img_path)
    return None

# ================== HỘP THOẠI OPEN ==================
def file_dialog_select_first_mp4(target_folder):
    rsleep("long")

    # Thêm: Tìm và click vào filename.png trước
    logging.info("Tìm và click vào 'filename.png' trước khi nhập đường dẫn...")
    
    # Thêm đường dẫn của filename.png vào khai báo ở đầu file
    # TEMPLATE_FILENAME = os.path.join(ICON_DIR, "filename.png")
    
    if not wait_and_click_image(TEMPLATE_FILENAME, timeout_sec=int(r(*RANDOM.click_timeout_sec)), 
                                confidence=r(*RANDOM.click_confidence)):
        logging.warning("Không tìm thấy 'filename.png', tiếp tục với Ctrl+L")
    
    rsleep("medium")  # Đợi sau khi click

    # 1) Ctrl+L -> dán path -> Enter (đi thẳng tới thư mục mã)
    pyautogui.hotkey('ctrl', 'l'); rsleep("tiny")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(target_folder)
    pyautogui.press('enter'); rsleep("medium")   # chờ thư mục load xong

    # 2) Alt+N -> dán '*.mp4' -> Enter (lọc file mp4)
    pyautogui.keyDown('alt')
    pyautogui.press('n')
    pyautogui.keyUp('alt')
    rsleep("tiny")

    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text('*.mp4')
    pyautogui.press('enter'); rsleep("long")


    # 3) Chọn file đầu và mở
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")

    # Thay vì nhấn Down, dùng Ctrl+A để chọn toàn bộ file (đảm bảo chọn file đầu)
    pyautogui.press('space'); rsleep("tiny")

    for _ in range(2):
        pyautogui.press('tab'); rsleep("small")
    pyautogui.press('enter'); rsleep("long")



def file_dialog_select_thumbnail():
    """
    Hộp thoại Open (chọn thumbnail) đã mở.
    Theo yêu cầu:
    - Shift+Tab x2
    - ArrowDown (chọn ảnh thumb)
    - Tab x4
    - Enter (Open)
    """
    rsleep("medium")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.press('space'); rsleep("small")   # chọn file thumbnail đầu tiên
    for _ in range(4):
        pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('enter'); rsleep("long")   # nhấn Open


# ================== FLOW NHẬP METADATA ==================
# CỘT: BB=53, BC=54 (zero-based)
IDX_TITLE_BB = 53
IDX_DESC_BC  = 54

def handle_metadata_flow(active_row):
    """
    Khi đã thấy trang metadata (có ảnh tiep.png),
    con trỏ đang ở ô TIÊU ĐỀ:
    - PASTE TIÊU ĐỀ (BB)
    - Tab×2 -> PASTE MÔ TẢ (BC)
    - Tab×2 -> NHẤN END -> Enter (mở hộp thoại chọn thumbnail)
    - Chọn thumbnail theo phím
    - Tab×2 -> Enter -> Tab -> Space -> Tab×2 -> Enter (chọn playlist)
    - Click tiep.png để sang bước 2
    """
    title = norm(active_row[IDX_TITLE_BB]) if len(active_row) > IDX_TITLE_BB else ""
    desc  = norm(active_row[IDX_DESC_BC])  if len(active_row) > IDX_DESC_BC  else ""
    
    logging.info("Dán TIÊU ĐỀ (BB): %s", (title or "(rỗng)"))
    # Nghỉ thêm cho chắc (đợi UI load xong)
    rsleep("long")   # hoặc "long" nếu RDP lag nhiều
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")   # quét sạch nội dung cũ
    paste_text(title or "")
    
    # Tab×2 -> vào MÔ TẢ
    pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('tab'); rsleep("tiny")
    rsleep("small")
    
    logging.info("Dán MÔ TẢ (BC).")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")   # quét sạch nội dung cũ
    paste_text(desc or "")
    
    # (NEW) Enter trước để thoát/commit ô mô tả
    pyautogui.press('enter'); rsleep("tiny")
    # Tab×2 -> khung chọn THUMBNAIL
    pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('tab'); rsleep("tiny")
    rsleep("small")
    
    # === THAY ĐỔI: NHẤN END TRƯỚC KHI ENTER ĐỂ MỞ HỘP THOẠI CHỌN THUMBNAIL ===
    logging.info("Nhấn END để cuộn xuống cuối trang trước khi chọn thumbnail...")
    pyautogui.press('end'); rsleep("small")
    # Nhấn thêm lần nữa để đảm bảo
    pyautogui.press('end'); rsleep("medium")  # Nghỉ lâu hơn để đảm bảo trang đã cuộn xong
    
    # Enter -> mở Open
    pyautogui.press('enter'); rsleep("small")
    
    # Chờ hộp thoại Open hiện (open.png) rồi mới thao tác chọn thumbnail
    pos_thumb_open = wait_image(TEMPLATE_OPEN_READY, timeout_sec=int(r(*RANDOM.click_timeout_sec)),
                                confidence=r(*RANDOM.click_confidence))
    if pos_thumb_open:
        file_dialog_select_thumbnail()
    else:
        logging.error("Không thấy hộp thoại Open (open.png) khi chọn thumbnail.")
        return
    
    # === SAU KHI CHỌN THUMBNAIL: CHỌN DANH SÁCH PHÁT THEO ANCHOR ẢNH ===
    logging.info("Chờ anchor 'danhsachphat.png' (khu chọn danh sách phát)...")
    pos_dsp = wait_image(TEMPLATE_DANHSACHPHAT,
                         timeout_sec=int(r(*RANDOM.click_timeout_sec)),
                         confidence=r(*RANDOM.click_confidence))
    if not pos_dsp:
        logging.error("Không tìm thấy 'danhsachphat.png' ⇒ bỏ qua bước chọn danh sách phát.")
    else:
        # Đảm bảo focus đúng vùng danh sách phát
        move_click(pos_dsp.x, pos_dsp.y); rsleep("small")
        
        # B1) Tab 1 lần → Enter (mở danh sách phát)
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('enter'); rsleep("small")
        
        # B2) Tab 2 lần → Enter (chốt/áp dụng danh sách phát)
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('enter'); rsleep("small")
    
    # === Cuối cùng: Click 'Tiếp' để sang bước 2 ===
    logging.info("Tìm và click nút 'Tiếp' để qua Bước 2...")
    pos = wait_image(TEMPLATE_NEXT_BTN,
                     timeout_sec=int(r(*RANDOM.click_timeout_sec)),
                     confidence=r(*RANDOM.click_confidence))
    if pos:
        click_once(pos.x, pos.y)
    else:
        logging.warning("Không tìm thấy nút 'Tiếp' sau khi nhập metadata.")
def file_dialog_select_srt():
    """
    Hộp thoại Open (chọn SRT) đã mở.
    Thêm bước click filename.png trước khi dán đường dẫn SRT.
    """
    # Thêm bước: Tìm và click vào filename.png trước khi nhập
    logging.info("Tìm và click vào 'filename.png' trước khi nhập tìm kiếm SRT...")
    if not wait_and_click_image(TEMPLATE_FILENAME, timeout_sec=int(r(*RANDOM.click_timeout_sec)), 
                              confidence=r(*RANDOM.click_confidence)):
        logging.warning("Không tìm thấy 'filename.png', tiếp tục với nhập trực tiếp")
    
    rsleep("small")  # Đợi sau khi click
    
    # Tiếp tục với phần nhập tìm kiếm SRT như trước
    paste_text('*.srt'); rsleep("tiny")
    pyautogui.press('enter'); rsleep("small")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.press('space'); rsleep("medium")   # chọn file đầu (đợi lâu hơn chút)
    for _ in range(4):
        pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('enter'); rsleep("long")


def handle_step2_flow(active_row):
    CLICK_TIMEOUT_SEC = int(r(*RANDOM.click_timeout_sec))
    CLICK_CONFIDENCE  = r(*RANDOM.click_confidence)
    STEP2_TIMEOUT_SEC = int(r(*RANDOM.step2_load_timeout_sec))

    def press(key, n=1, bucket="tiny"):
        for _ in range(n):
            pyautogui.press(key); rsleep(bucket)

    # 0) Vào Bước 2 (ưu tiên buoc2.png, fallback them.png)
    logging.info("Vào Bước 2 (anchor buoc2.png, fallback them.png)...")
    pos_buoc2 = wait_image(TEMPLATE_BUOC2, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_buoc2:
        logging.info("Không thấy buoc2.png → thử them.png")
        pos_them = wait_image(TEMPLATE_STEP2_THEM, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_them:
            logging.error("Không thấy buoc2.png / them.png ⇒ chưa vào Bước 2.")
            return
        pos_buoc2 = pos_them  # dùng tạm làm anchor click

    # 1) Lặp: click buoc2.png → nghỉ → click lại → Tab×4 → Enter
    #    Nếu KHÔNG thấy 'taiteplen.png' thì lặp lại chu trình trên.
    MAX_TRIES = 5
    for attempt in range(1, MAX_TRIES + 1):
        logging.info(f"[B2 focus try {attempt}/{MAX_TRIES}] click buoc2.png → nghỉ → click lại → Tab×4 → Enter")
        move_click(pos_buoc2.x, pos_buoc2.y); rsleep("small")   # click 1


        press('tab', 4, "tiny")
        pyautogui.press('enter'); rsleep("small")

        # Kiểm tra taiteplen.png đã hiện chưa
        logging.info("Kiểm tra 'taiteplen.png' sau Enter...")
        pos_tlp = wait_image(TEMPLATE_TAITEPLEN, timeout_sec=10, confidence=CLICK_CONFIDENCE)
        if pos_tlp:
            logging.info("ĐÃ thấy 'taiteplen.png' → tiếp tục các bước tiếp theo.")
            break
        else:
            logging.warning("Chưa thấy 'taiteplen.png' → lặp lại click buoc2.png → Tab×4 → Enter.")
            # tìm lại anchor (phòng bị trôi UI)
            pos_buoc2 = wait_image(TEMPLATE_BUOC2, timeout_sec=15, confidence=CLICK_CONFIDENCE) or \
                        wait_image(TEMPLATE_STEP2_THEM, timeout_sec=5, confidence=CLICK_CONFIDENCE)
            if not pos_buoc2:
                logging.error("Mất anchor buoc2.png/them.png → dừng Bước 2.")
                return
    else:
        logging.error(f"Sau {MAX_TRIES} lần vẫn không thấy 'taiteplen.png' → dừng Bước 2.")
        return

    # B) (NEW) Chờ thấy vùng/nút 'Tải tệp lên' của phụ đề (taiteplen.png)
    logging.info("Chờ 'taiteplen.png' (vùng Tải tệp lên phụ đề)...")
    if not wait_image(TEMPLATE_TAITEPLEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Không thấy 'taiteplen.png' ⇒ không thể mở khu tải phụ đề.")
        return

    # C) (NEW) Sau khi thấy 'taiteplen.png', chờ 1 nhịp cho UI ổn định
    rsleep("long")

    # D) (NEW) Click trực tiếp 'taiteplen.png' → đợi load → (đổi: click 'tieptuc.png' thay vì Tab×3→Enter)
    pos_tlp = wait_image(TEMPLATE_TAITEPLEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_tlp:
        logging.error("Không thấy 'taiteplen.png' ⇒ không thể mở khu tải phụ đề.")
        return

    move_click(pos_tlp.x, pos_tlp.y)
    rsleep("long")  # đợi UI ổn định

    # === THAY ĐỔI Ở ĐÂY: tìm và click 'tieptuc.png' để mở hộp thoại Open ===
    logging.info("Tìm và click 'tieptuc.png' để mở hộp thoại Open (SRT)...")
    if not wait_and_click_image(TEMPLATE_TIEPTUC, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.warning("Không thấy 'tieptuc.png' → fallback Tab×3 rồi Enter.")
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('enter'); rsleep("long")
    else:
        rsleep("long")  # cho UI mở hộp thoại xong


    # E) Hộp thoại Open: phải thấy open.png rồi mới gõ *.srt
    pos_open = wait_image(TEMPLATE_OPEN_READY, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_open:
        logging.error("Không thấy open.png khi thêm SRT.")
        return
    file_dialog_select_srt()

    # F) Xử lý upload SRT: đợi 'xong.png' rồi click
    logging.info("Chờ 'xong.png' sau khi upload SRT...")
    pos_done = wait_image(TEMPLATE_DONE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_done:
        logging.error("Không thấy xong.png sau khi thêm SRT.")
        return
    # nghỉ thêm cho chắc trước khi click
    rsleep("medium")
    move_click(pos_done.x, pos_done.y); rsleep("medium")

    # G) Sau khi ấn 'xong', PHẢI thấy trở về màn 'Màn hình kết thúc' (manhinhketthuc.png) rồi mới Tab
    logging.info("Chờ 'manhinhketthuc.png' (đã về trang mục Màn hình kết thúc)...")
    if not wait_image(TEMPLATE_ENDSCREEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Không thấy manhinhketthuc.png sau khi thêm SRT.")
        return

    # H) MỞ EDITOR END SCREEN (giữ nguyên)
    pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('tab'); rsleep("tiny")
    pyautogui.press('enter'); rsleep("medium")   # mở editor màn hình kết thúc

    # ====== BẮT ĐẦU CHUỖI THAO TÁC MỚI BÊN TRONG EDITOR ======

    # Helper nhỏ cho gọn
    def press(key, n=1, bucket="tiny"):
        for _ in range(n):
            pyautogui.press(key); rsleep(bucket)

    # (MỚI) Nghỉ 1 nhịp cho editor load ổn định
    rsleep("medium")

    # (MỚI) Click vào nút/ô 'chọn màn hình kết thúc' trong editor, rồi Tab × 3 để đưa focus tới slot đầu
    if not wait_and_click_image(TEMPLATE_CHON_ENDSCREEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Không thấy 'chonmanhinhketthuc.png' trong editor End screen.")
        return
    press('tab', 3, "tiny")


    # 2) Enter 2 lần để chọn Video 1
    press('enter', 2, "small")

    # 3) Enter 2 lần nữa để chọn Video 2
    press('enter', 2, "small")

    # 4) Enter 1 lần → gõ 'd' (jump to "Danh sách phát") → Enter → Tab ×3 → Enter
    press('enter', 1, "small")     # mở menu lựa chọn
    rsleep("tiny")
    pyautogui.press('d')           # gõ ký tự 'd' để nhảy đến "Danh sách phát"
    rsleep("tiny")
    press('enter', 1, "small")     # chọn "Danh sách phát"
    press('tab', 3, "tiny")        # di chuyển tới nút xác nhận/áp dụng
    press('enter', 1, "small")     # xác nhận


    # 5) Enter 1 lần → click trực tiếp vào ảnh 'dangky.png' → Enter
    press('enter', 1, "small")

    pos_dangky = wait_image(TEMPLATE_DANGKY, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if pos_dangky:
        move_click(pos_dangky.x, pos_dangky.y)
        rsleep("small")
    else:
        logging.error("Không thấy 'dangky.png' ⇒ bỏ qua bước chọn Đăng ký.")


    # ====== KẾT THÚC CHUỖI THAO TÁC MỚI ======

    # J) Đợi 'luu.png' rồi click Lưu (chờ lâu hơn vì render)
    logging.info("Chờ 'luu.png' để lưu màn hình kết thúc...")
    pos_save = wait_image(TEMPLATE_SAVE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_save:
        logging.error("Không thấy luu.png để lưu màn hình kết thúc.")
        return
    move_click(pos_save.x, pos_save.y); rsleep("medium")



    # ====== BẮT ĐẦU: THÊM THẺ (CARDS) SAU KHI LƯU END SCREEN ======

    # 0) Chờ 'ketthucok.png' xuất hiện để chắc chắn đang ở màn hình kết thúc
    logging.info("Chờ 'ketthucok.png' xác nhận đã ở màn 'Màn hình kết thúc'...")
    if not wait_image(TEMPLATE_KETTHUC_OK, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Không thấy 'ketthucok.png' sau khi Lưu End Screen.")
        return
    rsleep("small")

    # 1) Tab 1 lần → Enter để vào thêm thẻ
    press('tab', 1, "tiny")
    pyautogui.press('enter'); rsleep("small")  # mở giao diện 'Thêm thẻ' (Cards)
    rsleep("small")  # chờ UI hiện ra

    # Helper: tìm & click ảnh 'the.png'
    def click_the_button(step_tag="the_button"):
        """
        Tìm và click chính xác vào TEMPLATE_THE (the.png).
        - Chỉ click 1 lần.
        - Chuyển tọa độ physical->logical bằng _to_logical.
        - Không kéo chuột ra xa (loại bỏ moveRel gây lệch).
        - Ghi log physical & logical để debug nếu click sai.
        """
        logging.info("Tìm và click 'the.png' (nút Thẻ)...")

        # Park chuột ra xa trước khi dò ảnh để tránh overlay che template (nhưng rất nhanh)
        try:
            pyautogui.moveTo(10, 10, duration=min(0.2, r(*RANDOM.mouse_move)))
            rsleep("tiny")
        except Exception:
            pass

        pos_the = wait_image(TEMPLATE_THE, timeout_sec=int(r(*RANDOM.step2_load_timeout_sec)),
                            confidence=r(*RANDOM.click_confidence))
        if not pos_the:
            logging.error(f"Không thấy 'the.png' tại bước {step_tag}.")
            return False

        # Convert physical -> logical coords để click chính xác trong môi trường có scaling/RDP
        try:
            lx, ly = _to_logical(pos_the.x, pos_the.y)
        except Exception as e:
            logging.warning("Lỗi khi chuyển physical->logical coords: %s — sẽ dùng trực tiếp coords.", e)
            lx, ly = pos_the.x, pos_the.y

        logging.info("Click 'the.png' physical=(%d,%d) -> logical=(%d,%d)", pos_the.x, pos_the.y, lx, ly)

        # Click đúng 1 lần vào tọa độ đã chuyển
        try:
            pyautogui.moveTo(lx, ly, duration=min(0.15, r(*RANDOM.mouse_move)))
            pyautogui.click()
        except Exception as e:
            logging.error("Click vào 'the.png' thất bại: %s", e)
            return False

        rsleep("small")
        return True



    # (MỚI) Helper: thêm đúng 1 playlist card
    def add_single_playlist_card():
        """
        - Click 'Thẻ'
        - Tab ×4 → Enter (mở menu loại thẻ)
        - Đợi 1 nhịp
        - Tab ×3 → Enter (Thêm danh sách phát)
        """
        if not click_the_button(step_tag="playlist_open"):
            return False
        press('tab', 4, "tiny")
        pyautogui.press('enter'); rsleep("small")     # mở menu loại thẻ
        rsleep("small")                               # nghỉ 1 chút cho menu bung hẳn
        press('tab', 3, "tiny")
        pyautogui.press('enter'); rsleep("medium")    # chọn 'Thêm danh sách phát'
        rsleep("small")
        return True

    def click_the1_button(step_tag="the1_button"):
        """
        An toàn hơn: chờ the1.png, click exactly 1 lần (convert DPI), rồi đợi UI ổn định.
        Trả về True nếu click được, False nếu không thấy the1.png.
        """
        logging.info("Tìm và click 'the1.png' (the1)...")
        pos = wait_image(TEMPLATE_THE1, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos:
            logging.error(f"Không thấy 'the1.png' tại bước {step_tag}.")
            return False

        # click 1 lần chính xác
        try:
            click_once(pos.x, pos.y)
        except Exception as e:
            logging.error("Click the1.png thất bại: %s", e)
            return False

        # đợi UI ổn định trước khi tiếp tục (rất quan trọng)
        rsleep("tiny")

        # (Tùy chọn) nếu có template/menu xác nhận xuất hiện sau khi click the1, chờ nó:
        # EX: nếu bạn có TEMPLATE_THE_MENU (hình menu bật ra), uncomment dòng dưới
        # if not wait_image(TEMPLATE_THE_MENU, timeout_sec=5, confidence=CLICK_CONFIDENCE):
        #     logging.warning("Menu sau khi click the1 không xuất hiện (vẫn tiếp tục với Tab)...")

        return True



    # (MỚI) Helper: thêm 1 video card theo link ở 1 cột (BD/BE/BF/BG)
    def add_single_video_card_from_column(active_row, idx_col, col_name=""):
        """
        - Click 'Thẻ'
        - Tab ×4 → Enter ×2 (vào 'Thêm video')
        - Nghỉ 1 chút → tìm 'chonmotvideocuthe.png' → click
        - Tab ×3 → dán link (BD/BE/BF/BG)
        - Chờ 'tagvideo.png' → click
        """
        link = norm(active_row[idx_col]) if len(active_row) > idx_col else ""
        if not link:
            logging.warning("Cột %s rỗng, bỏ qua thẻ video.", col_name or f"idx {idx_col}")
            return False

        # Click trực tiếp the1.png rồi Tab → Enter
        if not click_the1_button(step_tag=f"video_{col_name or idx_col}__open_the1"):
            return False

        rsleep("tiny")                 # đợi UI nhận click
        press('tab', 1, "tiny")
        pyautogui.press('enter'); rsleep("medium")


        # Đợi nhẹ + tìm 'Chọn một video cụ thể'
        rsleep("small")
        pos_choose = wait_image(TEMPLATE_CHONVIDEO_CUTHE, timeout_sec=int(r(*RANDOM.step2_load_timeout_sec)),
                                confidence=r(*RANDOM.click_confidence))
        if not pos_choose:
            logging.error("Không thấy 'chonmotvideocuthe.png' → bỏ qua thẻ video %s.", col_name or idx_col)
            return False
        click_once(pos_choose.x, pos_choose.y)

        # Tab ×3 → ô link → paste
        press('tab', 3, "tiny")
        paste_text(link); rsleep("small")

        # Chờ gợi ý video và click
        logging.info("Chờ 'tagvideo.png' để chọn video gợi ý...")
        pos_tag = wait_image(TEMPLATE_TAGVIDEO, timeout_sec=int(r(*RANDOM.step2_load_timeout_sec)),
                            confidence=r(*RANDOM.click_confidence))
        if not pos_tag:
            logging.error("Không thấy 'tagvideo.png' sau khi dán link video %s.", col_name or idx_col)
            return False
        click_once(pos_tag.x, pos_tag.y)
        rsleep("medium")
        return True

    # ——— THEO YÊU CẦU MỚI: 1 PLAYLIST + 4 VIDEO ———

    # 1. Thêm 1 playlist
    if not add_single_playlist_card():
        logging.warning("Thêm playlist card thất bại — vẫn tiếp tục với video cards.")

    # 2. Thêm 4 video card theo BD, BE, BF, BG
    add_single_video_card_from_column(active_row, IDX_LINK_BD, col_name="BD")
    add_single_video_card_from_column(active_row, IDX_LINK_BE, col_name="BE")
    add_single_video_card_from_column(active_row, IDX_LINK_BF, col_name="BF")
    add_single_video_card_from_column(active_row, IDX_LINK_BG, col_name="BG")

    # 3) Thêm các mốc thời gian (timestamp) cho thẻ:
    # Yêu cầu: mỗi lần click 'the.png' → Tab 5 lần → nhập thời điểm → Tab (xác nhận)
    def add_timestamp_hhmmss(ts_value: str, step_label: str):
        if not click_the_button(step_tag=f"timestamp_{step_label}"):
            return False
        press('tab', 5, "tiny")
        paste_text(ts_value); rsleep("tiny")
        pyautogui.press('tab'); rsleep("small")
        return True

    # Lần lượt: 30:00:00, 10:00:00, 15:00:00, 20:00:00, 25:00:00
    add_timestamp_hhmmss("30:00:00", "30h")
    add_timestamp_hhmmss("10:00:00", "10m")
    add_timestamp_hhmmss("15:00:00", "15m")
    add_timestamp_hhmmss("20:00:00", "20m")
    add_timestamp_hhmmss("25:00:00", "25m")

    # 4) Chờ một chút rồi lưu (thao tác Lưu của phần Thẻ cũng dùng lại luu.png)
    rsleep("small")
    logging.info("Chờ 'luu.png' để lưu các thẻ (Cards)...")
    pos_save_cards = wait_image(TEMPLATE_SAVE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_save_cards:
        logging.error("Không thấy luu.png để lưu các thẻ.")
        return
    move_click(pos_save_cards.x, pos_save_cards.y); rsleep("medium")

    # ====== KẾT THÚC: THÊM THẺ (CARDS) ======




    # ====== BỎ LUỒNG ẤN "TIẾP" - NHẢY THẲNG SANG BƯỚC HẸN LỊCH ======
    logging.info("Click 'Chế độ hiển thị' để sang thẳng bước hẹn lịch (bỏ qua Step 3)...")
    pos_cdhien = wait_image(TEMPLATE_CHEDO_HIEN_THI, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_cdhien:
        logging.error("Không thấy 'chedohienthi.png' ⇒ không thể sang màn hẹn lịch.")
        return False
    move_click(pos_cdhien.x, pos_cdhien.y)
    rsleep("long")
    return True   # báo là đã sang màn hẹn lịch luôn


def handle_step3_4_flow(active_row, client, code):
    """
    Bước 3: Tìm và click trực tiếp vào henlich.png để vào màn hẹn lịch
    Sau đó: Sử dụng Tab để điều hướng đến ô ngày/giờ như trước
    """
    CLICK_TIMEOUT_SEC = int(r(*RANDOM.click_timeout_sec))
    
    logging.info("Tìm và click trực tiếp vào 'henlich.png' để vào màn hẹn lịch...")
    
    # Thêm đường dẫn tới ảnh henlich.png - bạn cần thêm ảnh này vào thư mục icon
    TEMPLATE_HENLICH = os.path.join(ICON_DIR, "henlich.png")
    
    # Tìm và click vào henlich.png
    if not wait_and_click_image(TEMPLATE_HENLICH, timeout_sec=CLICK_TIMEOUT_SEC):
        logging.error("Không tìm thấy 'henlich.png' ⇒ không thể vào màn hẹn lịch.")
        return False
    
    logging.info("Đã vào màn hẹn lịch, đợi UI ổn định...")
    rsleep("medium")  # Đợi UI ổn định
    
    # Sau khi click vào henlich.png, dùng Tab để điều hướng đến ô ngày như trước
    for _ in range(8):
        pyautogui.press('tab'); rsleep("tiny")

    pyautogui.press('enter'); rsleep("small")  # giờ con trỏ ở ô Ngày
    
    # Dán ngày từ cột BI
    date_val = norm(active_row[IDX_DATE_BI]) if len(active_row) > IDX_DATE_BI else ""
    logging.info("Dán NGÀY (BI): %s", date_val or "(rỗng)")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(date_val or "")
    pyautogui.press('enter'); rsleep("small")

    # Dán giờ từ cột BJ bằng cách click ảnh time.png → Ctrl+A → paste
    time_val = norm(active_row[IDX_TIME_BJ]) if len(active_row) > IDX_TIME_BJ else ""
    logging.info("Dán GIỜ (BJ): %s", time_val or "(rỗng)")

    pos_time = wait_image(TEMPLATE_TIME, timeout_sec=CLICK_TIMEOUT_SEC)
    if not pos_time:
        logging.error("Không thấy 'time.png' (ô Giờ).")
        return False

    # click thẳng vào chính giữa ô giờ (không lệch nữa)
    move_click(pos_time.x, pos_time.y)
    rsleep("small")

    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(time_val or "")
    pyautogui.press('enter'); rsleep("small")

    # Click nút Lên lịch
    logging.info("Tìm và click 'lenlich.png' để xác nhận hẹn lịch...")
    pos_publish = wait_image(TEMPLATE_SCHEDULE_PUBLISH, timeout_sec=CLICK_TIMEOUT_SEC)
    if not pos_publish:
        logging.error("Không thấy lenlich.png (nút Lên lịch).")
        return False

    move_click(pos_publish.x, pos_publish.y)
    rsleep("medium")

    # ✅ CẬP NHẬT TRẠNG THÁI NGAY KHI BẤM 'LÊN LỊCH'
    try:
        update_source_status(client, code, "ĐÃ ĐĂNG")
        logging.info("Đã cập nhật trạng thái 'ĐÃ ĐĂNG' cho mã %s ngay sau khi bấm Lên lịch.", code)
    except Exception as e:
        logging.warning("Cập nhật trạng thái ngay sau khi bấm Lên lịch bị lỗi: %s", e)

    # ⏳ Vẫn chờ 10 phút rồi mới xử lý mã tiếp theo
    logging.info("Chờ 10 phút để YouTube xử lý trước khi chuyển sang mã kế.")
    time.sleep(10 * 60)

    return True




# --- Helpers kiểm tra file & ổn định thư mục ---
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def has_required_files(dir_path: str) -> bool:
    """Trong dir_path phải có ≥1 .mp4, ≥1 .srt, ≥1 ảnh (jpg/jpeg/png/webp)."""
    if not os.path.isdir(dir_path):
        return False
    names = os.listdir(dir_path)
    has_mp4 = any(n.lower().endswith(".mp4") for n in names)
    has_srt = any(n.lower().endswith(".srt") for n in names)
    has_img = any(os.path.splitext(n)[1].lower() in IMG_EXTS for n in names)
    return has_mp4 and has_srt and has_img



# --- helper tính thống kê bộ bắt buộc (mp4 + srt + ảnh) ---
def get_required_stats(dir_path: str):
    """
    Trả về (count, total_bytes) của các file thuộc 'bộ bắt buộc':
    - .mp4, .srt và ảnh (IMG_EXTS).
    Dùng để so sánh nhanh server ↔ local.
    """
    if not os.path.isdir(dir_path):
        return (0, 0)
    total = 0
    count = 0
    for root, _, files in os.walk(dir_path):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext == ".mp4" or ext == ".srt" or ext in IMG_EXTS:
                fp = os.path.join(root, name)
                try:
                    total += os.path.getsize(fp)
                    count += 1
                except Exception:
                    pass
    return (count, total)
# --- ensure_local_folder có thêm kiểm tra dung lượng ---
def ensure_local_folder(code, delete_server=True):
    """
    Đảm bảo LOCAL_DONE_ROOT\\{code} có đủ mp4+srt+ảnh.
    Thêm: nếu local 'đủ bộ' nhưng (count, bytes) KHÁC server → copy lại.
    """
    local_folder  = os.path.join(LOCAL_DONE_ROOT, code)
    server_folder = os.path.join(SERVER_DONE_ROOT, code)

    local_enough  = os.path.isdir(local_folder) and has_required_files(local_folder)
    server_enough = has_required_files(server_folder)

    # Nếu local đã đủ bộ:
    if local_enough:
        # Nếu server cũng đủ bộ thì so thống kê; khác là copy lại
        if server_enough:
            lc = get_required_stats(local_folder)
            sc = get_required_stats(server_folder)
            if lc != sc:
                logging.info(f"♻️ Local khác dung lượng/bộ so với server ({lc} != {sc}) → refresh từ server.")
            else:
                logging.info(f"✅ Local đã đủ bộ và khớp server: {local_folder}")
                return True
        else:
            # Server thiếu hoặc không có → coi như local dùng được
            logging.info(f"✅ Local đã đủ bộ; server không sẵn. Giữ nguyên: {local_folder}")
            return True

    # Đến đây: hoặc local thiếu, hoặc local đủ nhưng stats khác server → cần copy từ server
    if not server_enough:
        logging.error(f"❌ Server thiếu bộ hoặc không có thư mục: {server_folder}")
        return False

    # Copy thẳng: xoá local cũ (nếu có), rồi copytree
    try:
        if os.path.exists(local_folder):
            shutil.rmtree(local_folder, ignore_errors=True)
        shutil.copytree(server_folder, local_folder)
        logging.info(f"📥 Đã copy {server_folder} → {local_folder}")
    except Exception as e:
        logging.error(f"❌ Lỗi copy {server_folder} → {local_folder}: {e}")
        return False

    # Xác nhận local đủ bộ sau copy
    if not has_required_files(local_folder):
        logging.error(f"❌ Sau copy, local vẫn thiếu bộ: {local_folder}")
        return False

    # (Tuỳ chọn) xoá server để dọn
    if delete_server:
        try:
            shutil.rmtree(server_folder)
            logging.info(f"🗑️ Đã xoá thư mục server: {server_folder}")
        except Exception as e:
            logging.warning(f"⚠️ Không xoá được server {server_folder}: {e}")

    return True

def get_all_ready_codes(rows):
    """Lấy tất cả code cùng kênh, trạng thái OK, lịch hôm nay và giờ còn > hiện tại."""
    now = datetime.now()
    out = []
    for r in rows[1:]:
        if len(r) > 61 and norm(r[34]) == CHANNEL_CODE and norm(r[47]) == STATUS_OK:
            d = _parse_date(norm(r[60]) or "")  # BI
            t = _parse_time(norm(r[61]) or "")  # BJ
            if not d or not t:
                continue
            target_dt = datetime.combine(d, t)
            if d == now.date() and target_dt > now:
                code = norm(r[0])
                if code:
                    out.append(code)
    return out


def get_tomorrow_codes(rows):
    """Lấy tất cả code (đúng CHANNEL_CODE, STATUS_OK) có lịch đúng NGÀY MAI (BI)."""
    tomorrow = datetime.now().date() + timedelta(days=1)
    out = []
    for r in rows[1:]:
        if len(r) > 61 and norm(r[34]) == CHANNEL_CODE and norm(r[47]) == STATUS_OK:
            d = _parse_date(norm(r[60]) or "")  # BI
            if d and d == tomorrow:
                code = norm(r[0])
                if code:
                    out.append(code)
    return out



# ================== MAIN ==================
def main():
    random.seed()
    cleanup_posted_codes()

    BROWSER_LAUNCH_WAIT_SEC = int(r(*RANDOM.browser_launch_wait_sec))
    CLICK_TIMEOUT_SEC       = int(r(*RANDOM.click_timeout_sec))
    CLICK_CONFIDENCE        = r(*RANDOM.click_confidence)

    client     = gs_client()
    input_rows = get_rows(client, INPUT_SHEET)

    # ========= XÁC ĐỊNH TRƯỚC TẤT CẢ MÃ CẦN ĐĂNG TRONG PHIÊN NÀY =========
    ready_codes = get_all_ready_codes(input_rows)
    if not ready_codes:
        logging.info(f"Không có mã thoả ({CHANNEL_CODE}, {STATUS_OK}) cho hôm nay. Pre-stage NGÀY MAI rồi thoát.")
        try:
            tomorrow_codes = get_tomorrow_codes(input_rows)
            if tomorrow_codes:
                logging.info(f"Pre-stage NGÀY MAI: {len(tomorrow_codes)} mã: {tomorrow_codes}")
                for c in tomorrow_codes:
                    try:
                        ensure_local_folder(c)  # đã có .mp4 ở local thì hàm tự bỏ qua
                    except Exception as e:
                        logging.warning(f"Pre-stage NGÀY MAI lỗi {c}: {e}")
            else:
                logging.info("Không có mã ngày mai để pre-stage.")
        except Exception as e:
            logging.warning(f"Lỗi khi pre-stage ngày mai: {e}")
        return

    # Lọc theo thư mục gốc server: thiếu bộ là loại
    server_or_local_ok = []
    for c in ready_codes:
        lf = os.path.join(LOCAL_DONE_ROOT, c)
        sf = os.path.join(SERVER_DONE_ROOT, c)
        if has_required_files(lf) or has_required_files(sf):
            server_or_local_ok.append(c)
        else:
            logging.warning("⛔ Bỏ mã %s: thiếu bộ ở cả local & server.", c)
    ready_codes = server_or_local_ok

    if not ready_codes:
        logging.info("Không còn mã hợp lệ sau khi kiểm tra thư mục server. Pre-stage NGÀY MAI rồi thoát.")
        # Pre-stage ngày mai nhưng cũng lọc theo server
        try:
            tomorrow_codes = get_tomorrow_codes(input_rows)
            if tomorrow_codes:
                tmr_ok = [c for c in tomorrow_codes if has_required_files(os.path.join(SERVER_DONE_ROOT, c))]
                if tmr_ok:
                    logging.info(f"Pre-stage NGÀY MAI (đã lọc đủ bộ): {tmr_ok}")
                    for c in tmr_ok:
                        try:
                            ensure_local_folder(c)
                        except Exception as e:
                            logging.warning(f"Pre-stage NGÀY MAI lỗi {c}: {e}")
                else:
                    logging.info("Không có mã ngày mai đủ bộ để pre-stage.")
            else:
                logging.info("Không có mã ngày mai để pre-stage.")
        except Exception as e:
            logging.warning(f"Lỗi khi pre-stage ngày mai: {e}")
        return   
    logging.info(f"Phiên này sẽ chỉ đăng {len(ready_codes)} mã: {ready_codes}")
    
    # Pre-stage (copy) tất cả mã đã lên lịch đăng
    for c in ready_codes:
        try:
            ensure_local_folder(c)  # sẽ không copy lại nếu local đã có .mp4
        except Exception as e:
            logging.warning(f"Prestage lỗi {c}: {e}")

    # 1) Đóng trình duyệt đang chạy (local)
    close_browsers_gently_in_rdp()
    rsleep("small")

    # 2) Mở trình duyệt LOCAL
    logging.info("Mở trình duyệt: %s", RUN_BROWSER_EXE)
    open_run_and_execute(RUN_BROWSER_EXE)
    time.sleep(BROWSER_LAUNCH_WAIT_SEC)

    # ========= VÒNG LẶP ĐĂNG TỪNG MÃ TRONG DANH SÁCH ĐÃ XÁC ĐỊNH =========
    first_time = True
    processed_codes = set()
    round_idx = 0

    # Thay đổi chính: vòng lặp qua danh sách mã đã xác định trước
    for code in ready_codes:
        # Kiểm tra lại nếu mã đã xử lý trong phiên này
        if code in processed_codes:
            logging.info("Mã %s đã xử lý trong phiên này. Bỏ qua.", code)
            continue
            
        round_idx += 1
        logging.info("=== Vòng đăng #%d | CODE: %s ===", round_idx, code)
        
        # Lấy toàn bộ hàng để đọc BB/BC
        active_row = find_row_by_code(input_rows, code)
        if not active_row:
            logging.error("Không tìm thấy dòng dữ liệu tương ứng với mã: %s", code)
            continue

        target_folder = FOLDER_PATTERN.format(code=code)
        logging.info("Thư mục mã: %s", target_folder)
        
        # Đảm bảo thư mục video tồn tại
        if not ensure_local_folder(code):
            logging.error(f"Không thể chuẩn bị thư mục video cho mã {code} ⇒ bỏ qua.")
            continue

        # Điều hướng tới trang upload
        if not first_time:
            pyautogui.hotkey('ctrl', 't'); rsleep("small")
        
        logging.info("Đi tới: %s", UPLOAD_URL)
        pyautogui.hotkey('ctrl', 'l'); rsleep("tiny")
        paste_text(UPLOAD_URL)
        pyautogui.press('enter'); rsleep("medium")
        
        # ===== THÊM ĐOẠN PHÓNG TO TRÌNH DUYỆT SAU KHI MỞ LINK UPLOAD =====
        logging.info("Phóng to cửa sổ trình duyệt...")
           
        try:
            # Cách 2: Alt+Space rồi X
            pyautogui.keyDown('alt'); pyautogui.press('space'); pyautogui.keyUp('alt'); rsleep("tiny")
            pyautogui.press('x'); rsleep("small")
        except Exception:
            logging.warning("Phóng to bằng Alt+Space -> X thất bại, thử cách khác...")
        
        try:
            # Cách 3: Windows+Up
            pyautogui.keyDown('win'); pyautogui.press('up'); pyautogui.keyUp('win'); rsleep("small")
        except Exception:
            logging.warning("Phóng to bằng Win+Up thất bại.")
        pyautogui.press('f5'); rsleep("medium")
        # 7) Chờ nút Select files rồi click
        logging.info("Chờ nút Select files (chonfile.png)...")

        if not wait_and_click_image(TEMPLATE_SELECT_BTN,
                                    timeout_sec=CLICK_TIMEOUT_SEC,
                                    confidence=CLICK_CONFIDENCE):
            logging.warning("Hết hạn chưa thấy chonfile.png → F5 rồi thử lại 1 lần.")
            try:
                pyautogui.press('f5')
            except Exception:
                pass
            rsleep("medium")  # đợi trang refresh

            # thử lại một lần, thời gian ngắn hơn
            if not wait_and_click_image(TEMPLATE_SELECT_BTN,
                                        timeout_sec=max(20, CLICK_TIMEOUT_SEC // 2),
                                        confidence=CLICK_CONFIDENCE):
                logging.error("Không click được nút Select files (sau khi F5). Bỏ qua mã %s.", code)
                continue

        


        # 8) Chờ hộp thoại Open sẵn sàng
        logging.info("Chờ hộp thoại Open (open.png)...")
        pos_open = wait_image(TEMPLATE_OPEN_READY, timeout_sec=CLICK_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_open:
            logging.error("Không thấy open.png (hộp thoại Open chưa load). Bỏ qua mã %s.", code)
            first_time = False
            continue

        # 9) Chọn .mp4 đầu tiên
        logging.info("Chọn .mp4 đầu tiên trong thư mục: %s", target_folder)
        file_dialog_select_first_mp4(target_folder)
        logging.info("Đã chọn video — YouTube bắt đầu upload.")

        # 10) Chờ trang metadata sẵn sàng
        pos_next = wait_image(TEMPLATE_NEXT_BTN, timeout_sec=CLICK_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_next:
            logging.error("Không thấy giao diện metadata (tiep.png) với mã %s. Bỏ qua.", code)
            first_time = False
            continue

        # 11) Nhập metadata + Step 2 + Step 4 (lên lịch)
        handle_metadata_flow(active_row)
        handle_step2_flow(active_row)
        ok = handle_step3_4_flow(active_row, client, code)

        if not ok:
            logging.error("Đăng/lên lịch không xác nhận được bằng ảnh → bỏ qua Ctrl+T cho vòng sau.")
            continue

        # Thêm mã đã xử lý vào danh sách đã xử lý
        processed_codes.add(code)
        first_time = False
        
    logging.info("Đã hoàn thành tất cả %d/%d mã trong danh sách.", len(processed_codes), len(ready_codes))

    # ⬇️ Copy sẵn video của NGÀY MAI (pre-stage)
    try:
        tomorrow_codes = get_tomorrow_codes(input_rows)
        if tomorrow_codes:
            logging.info(f"Pre-stage NGÀY MAI: {len(tomorrow_codes)} mã: {tomorrow_codes}")
            for c in tomorrow_codes:
                try:
                    ensure_local_folder(c)  # sẽ không copy lại nếu local đã có .mp4
                except Exception as e:
                    logging.warning(f"Pre-stage lỗi {c}: {e}")
        else:
            logging.info("Không có mã ngày mai để pre-stage.")
    except Exception as e:
        logging.warning(f"Lỗi khi pre-stage ngày mai: {e}")


if __name__ == "__main__":
    while True:
        try:
            # ❌ Bỏ dòng close_browsers_gently_in_rdp() ở đây
            main()
        except Exception as e:
            logging.error("Lỗi khi chạy main(): %s", e)
        time.sleep(3 * 60 * 60)











