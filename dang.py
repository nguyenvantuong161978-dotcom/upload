
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  TOOL ĐĂNG VIDEO YOUTUBE TỰ ĐỘNG                                   ║
# ║  Sử dụng PyAutoGUI + nhận diện ảnh + Google Sheets                 ║
# ║                                                                      ║
# ║  CẤU TRÚC FILE:                                                     ║
# ║   S1  - IMPORTS & SETUP                                             ║
# ║   S2  - CẤU HÌNH KÊNH & ĐƯỜNG DẪN                                  ║
# ║   S3  - CẤU HÌNH CỘT GOOGLE SHEETS                                 ║
# ║   S4  - CẤU HÌNH ICON TEMPLATES                                     ║
# ║   S5  - CẤU HÌNH HUMAN-LIKE (timing, click offset, bezier...)      ║
# ║   S6  - HÀM CƠ SỞ (sleep, click, paste, scale)                    ║
# ║   S7  - GOOGLE SHEETS (kết nối, đọc, ghi)                          ║
# ║   S8  - QUẢN LÝ FILE & THƯ MỤC                                     ║
# ║   S9  - AUTOMATION TRÌNH DUYỆT (open_run, wait_image, close)       ║
# ║   S10 - BƯỚC 1: UPLOAD FILE & NHẬP METADATA                        ║
# ║   S11 - BƯỚC 2: PHỤ ĐỀ, END SCREEN, THẺ                           ║
# ║   S12 - BƯỚC 3-4: HẸN LỊCH & CẬP NHẬT TRẠNG THÁI                  ║
# ║   S13 - MAIN LOOP                                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S1 - IMPORTS & SETUP                                                │
# └──────────────────────────────────────────────────────────────────────┘

import os
import logging
import time
import random
import math
import ctypes
import shutil
from types import SimpleNamespace
from datetime import datetime, timedelta

from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pyautogui
import pyperclip

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
pyautogui.FAILSAFE = False

# Bật DPI-aware để PyAutoGUI/Windows dùng cùng hệ quy chiếu
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S2 - CẤU HÌNH KÊNH & ĐƯỜNG DẪN (đọc từ config.json)               │
# └──────────────────────────────────────────────────────────────────────┘

import json

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    CFG = json.load(_f)

# Tự nhận diện từ vị trí dang.py:
# C:\Users\{user}\Documents\{CHANNEL_CODE}\upload\dang.py
_UPLOAD_DIR    = os.path.dirname(os.path.abspath(__file__))        # ...\upload
_CHANNEL_DIR   = os.path.dirname(_UPLOAD_DIR)                      # ...\{CHANNEL_CODE}
_AUTO_CHANNEL  = os.path.basename(_CHANNEL_DIR)                    # CHANNEL_CODE
_USER_HOME     = os.path.expanduser("~")                           # C:\Users\{user}

CHANNEL_CODE      = CFG.get("CHANNEL_CODE", _AUTO_CHANNEL)
RUN_BROWSER_EXE   = CFG.get("RUN_BROWSER_EXE", os.path.join(_CHANNEL_DIR, f"{_AUTO_CHANNEL}.exe"))
LOCAL_DONE_ROOT   = CFG.get("LOCAL_DONE_ROOT", os.path.join(_USER_HOME, "Desktop", "done"))
SERVER_DONE_ROOT  = CFG.get("SERVER_DONE_ROOT", r"\\tsclient\D\AUTO\done")
UPLOAD_URL        = "https://www.youtube.com/upload"

# Google Sheets — hỗ trợ cả tên field cũ và mới
SPREADSHEET_NAME  = CFG.get("SPREADSHEET_NAME", "")
INPUT_SHEET       = CFG.get("INPUT_SHEET", CFG.get("SHEET_NAME", "INPUT"))
SOURCE_SHEET      = CFG.get("SOURCE_SHEET", "NGUON")
CREDENTIAL_PATH   = CFG.get("CREDENTIAL_PATH", "creds.json")
STATUS_OK         = CFG.get("STATUS_OK", "EDIT XONG")
STATUS_COL        = CFG.get("STATUS_COL", 48)

logging.info(f"Config: CHANNEL={CHANNEL_CODE}, SHEET={SPREADSHEET_NAME}, BROWSER={RUN_BROWSER_EXE}")

# Đường dẫn thư mục video
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
FOLDER_PATTERN    = os.path.join(LOCAL_DONE_ROOT, "{code}")


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S3 - CẤU HÌNH CỘT GOOGLE SHEETS (zero-based index)                 │
# └──────────────────────────────────────────────────────────────────────┘

IDX_CHANNEL_AI = 34   # AI - mã kênh
IDX_STATUS_AV  = 47   # AV - trạng thái (value = STATUS_OK)
IDX_TITLE_BB   = 53   # BB - tiêu đề video
IDX_DESC_BC    = 54   # BC - mô tả video
IDX_LINK_BD    = 55   # BD - link video card 1
IDX_LINK_BE    = 56   # BE - link video card 2
IDX_LINK_BF    = 57   # BF - link video card 3
IDX_LINK_BG    = 58   # BG - link video card 4
IDX_DATE_BI    = 60   # BI - ngày hẹn lịch
IDX_TIME_BJ    = 61   # BJ - giờ hẹn lịch


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S4 - CẤU HÌNH ICON TEMPLATES                                        │
# └──────────────────────────────────────────────────────────────────────┘

ICON_DIR = os.path.join(BASE_DIR, "icon")

# Bước Upload
TEMPLATE_SELECT_BTN       = os.path.join(ICON_DIR, "chonfile.png")
TEMPLATE_OPEN_READY       = os.path.join(ICON_DIR, "open.png")
TEMPLATE_FILENAME         = os.path.join(ICON_DIR, "filename.png")

# Bước 1 - Metadata
TEMPLATE_NEXT_BTN         = os.path.join(ICON_DIR, "tiep.png")
TEMPLATE_DANHSACHPHAT     = os.path.join(ICON_DIR, "danhsachphat.png")
TEMPLATE_THU_NGHIEM       = os.path.join(ICON_DIR, "thunghiem.png")  # A/B test thumbnail

# Bước 2 - Phụ đề & End Screen
TEMPLATE_DOI_TAI          = os.path.join(ICON_DIR, "doitai.png")   # đang tải video, chờ biến mất
TEMPLATE_LOI              = os.path.join(ICON_DIR, "loi.png")     # video bị lỗi (mp4 hỏng)
TEMPLATE_BUOC2            = os.path.join(ICON_DIR, "buoc2.png")
TEMPLATE_STEP2_THEM       = os.path.join(ICON_DIR, "them.png")
TEMPLATE_TAITEPLEN        = os.path.join(ICON_DIR, "taiteplen.png")
TEMPLATE_TIEPTUC          = os.path.join(ICON_DIR, "tieptuc.png")
TEMPLATE_DONE             = os.path.join(ICON_DIR, "xong.png")
TEMPLATE_ENDSCREEN        = os.path.join(ICON_DIR, "manhinhketthuc.png")
TEMPLATE_CHON_ENDSCREEN   = os.path.join(ICON_DIR, "chonmanhinhketthuc.png")
TEMPLATE_DANGKY           = os.path.join(ICON_DIR, "dangky.png")
TEMPLATE_SAVE             = os.path.join(ICON_DIR, "luu.png")

# Bước 2 - Thẻ (Cards)
TEMPLATE_KETTHUC_OK       = os.path.join(ICON_DIR, "ketthucok.png")
TEMPLATE_THE              = os.path.join(ICON_DIR, "the.png")
TEMPLATE_THE1             = os.path.join(ICON_DIR, "the1.png")
TEMPLATE_CHONVIDEO_CUTHE  = os.path.join(ICON_DIR, "chonmotvideocuthe.png")
TEMPLATE_TAGVIDEO         = os.path.join(ICON_DIR, "tagvideo.png")

# Bước 3-4 - Hẹn lịch
TEMPLATE_CHEDO_HIEN_THI   = os.path.join(ICON_DIR, "chedohienthi.png")
TEMPLATE_HENLICH          = os.path.join(ICON_DIR, "henlich.png")
TEMPLATE_TIME             = os.path.join(ICON_DIR, "time.png")
TEMPLATE_SCHEDULE_PUBLISH = os.path.join(ICON_DIR, "lenlich.png")
TEMPLATE_KIEM_TRA         = os.path.join(ICON_DIR, "kiemtra.png")
TEMPLATE_DA_LEN_LICH      = os.path.join(ICON_DIR, "dalenlichchovideo.png")


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S5 - CẤU HÌNH HUMAN-LIKE                                            │
# │                                                                      │
# │ Mục đích: Mọi thao tác chuột/bàn phím đều mô phỏng hành vi người   │
# │ thật, tránh bị hệ thống phát hiện là tool tự động.                  │
# │                                                                      │
# │ Tất cả tham số đều có thể bật/tắt và chỉnh ngay tại đây.           │
# └──────────────────────────────────────────────────────────────────────┘

HUMAN = SimpleNamespace(

    # ── Timing (thời gian nghỉ giữa các thao tác) ──
    # Tăng cho RDP lag — khoảng rộng hơn để tự nhiên
    tiny=(0.8, 1.5),             # cũ: 0.5-0.9  → giữa phím Tab, Ctrl+V
    small=(1.8, 3.0),            # cũ: 1.2-2.0  → sau Enter nhẹ, click nhỏ
    medium=(3.5, 6.0),           # cũ: 2.5-4.0  → chờ UI load
    long=(7.0, 12.0),            # cũ: 5.0-8.0  → chờ hộp thoại, trang load

    # ── Retry (chờ khi dò ảnh) ──
    retry_interval=(1.5, 2.8),   # cũ: 1.2-2.0

    # ── Timeout & Confidence (nhận diện ảnh) ──
    click_timeout=(150, 240),    # cũ: 120-180  → chờ ảnh 2.5-4 phút
    click_confidence=(0.80, 0.92),  # cũ: 0.85-0.95  → bớt khó tính cho RDP mờ
    step2_timeout=(200, 300),    # cũ: 150-240  → bước 2 chờ 3.3-5 phút
    browser_wait=(18, 30),       # cũ: 12-20    → chờ browser khởi động lâu hơn

    # ── Click Offset: lệch tâm khi click vào ảnh ──
    # Người thật không bao giờ click chính giữa nút
    # Offset tính theo % kích thước ảnh, đảm bảo luôn nằm trong ảnh
    click_offset_enabled=True,
    click_offset_ratio=0.35,      # offset tối đa = 35% nửa chiều rộng/cao ảnh

    # ── Mouse Curve: di chuột theo đường cong Bezier ──
    # Người thật di chuột theo đường cong, không thẳng tắp
    mouse_curve_enabled=True,
    mouse_move_duration=(0.35, 0.7),    # cũ: 0.25-0.45  → di chuột chậm hơn
    mouse_curve_strength=(0.15, 0.35),
    mouse_curve_steps=30,

    # ── Hover Before Click: dừng lại trước khi click ──
    # Đôi khi người thật di chuột tới rồi "suy nghĩ" mới click
    hover_enabled=True,
    hover_chance=0.35,            # cũ: 0.30  → 35% hover trước
    hover_delay=(0.15, 0.5),     # cũ: 0.1-0.35  → dừng lâu hơn

    # ── Micro Jitter: rung nhẹ chuột ──
    # Tay người không bao giờ giữ chuột hoàn toàn yên
    jitter_enabled=True,
    jitter_px=(1, 3),             # rung 1-3 pixel

    # ── Random Micro Pause: dừng suy nghĩ giữa các bước ──
    # Người thật đôi khi dừng vài giây để xem/đọc
    micro_pause_chance=0.20,      # cũ: 0.15  → 20% dừng suy nghĩ
    micro_pause_sec=(2.0, 5.0),   # cũ: 1.5-4.0  → dừng lâu hơn

    # ── Random Scroll: cuộn nhẹ trước thao tác ──
    # Người thật hay cuộn trang lên/xuống để xem lại
    scroll_enabled=True,
    scroll_chance=0.10,           # 10% xác suất cuộn
    scroll_amount=(-2, 2),        # số lần cuộn (âm = lên, dương = xuống)
)


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S6 - HÀM CƠ SỞ (sleep, click, paste, scale, bezier)               │
# └──────────────────────────────────────────────────────────────────────┘

def rand(a, b):
    """Random float trong [a, b]."""
    return random.uniform(a, b)

# Alias ngắn gọn
r = rand


def _get_scale():
    """Tính tỉ lệ (screenshot px) / (logical px) theo 2 trục."""
    sw, sh = pyautogui.size()
    iw, ih = pyautogui.screenshot().size
    sx = iw / (sw or 1)
    sy = ih / (sh or 1)
    return sx, sy


def _to_logical(x, y):
    """Đổi toạ độ từ ảnh chụp sang logical px."""
    sx, sy = _get_scale()
    return int(x / sx), int(y / sy)


def rsleep(bucket="small"):
    """Sleep ngẫu nhiên theo bucket timing."""
    lo, hi = getattr(HUMAN, bucket)
    time.sleep(r(lo, hi))


def maybe_micro_pause():
    """Đôi khi dừng suy nghĩ như người thật."""
    if random.random() < HUMAN.micro_pause_chance:
        pause = r(*HUMAN.micro_pause_sec)
        logging.debug("Micro pause %.1fs", pause)
        time.sleep(pause)


def maybe_random_scroll():
    """Đôi khi cuộn trang nhẹ như người thật đang xem lại."""
    if HUMAN.scroll_enabled and random.random() < HUMAN.scroll_chance:
        amount = random.randint(*HUMAN.scroll_amount)
        if amount != 0:
            pyautogui.scroll(amount)
            logging.debug("Random scroll %d", amount)
            time.sleep(r(0.2, 0.5))


def _bezier_move(target_x, target_y, duration=None):
    """
    Di chuột theo đường cong Bezier 3 điểm (quadratic).
    Mô phỏng cách người thật di chuột: không bao giờ đi thẳng.
    """
    if duration is None:
        duration = r(*HUMAN.mouse_move_duration)

    start_x, start_y = pyautogui.position()
    steps = HUMAN.mouse_curve_steps

    # Điểm kiểm soát Bezier: lệch sang 1 bên ngẫu nhiên
    mid_x = (start_x + target_x) / 2
    mid_y = (start_y + target_y) / 2
    dist = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
    strength = r(*HUMAN.mouse_curve_strength)
    offset = dist * strength

    # Lệch vuông góc với đường thẳng
    angle = math.atan2(target_y - start_y, target_x - start_x) + math.pi / 2
    direction = random.choice([-1, 1])
    ctrl_x = mid_x + direction * offset * math.cos(angle)
    ctrl_y = mid_y + direction * offset * math.sin(angle)

    step_delay = duration / steps
    for i in range(1, steps + 1):
        t = i / steps
        # Quadratic Bezier: B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
        bx = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + t ** 2 * target_x
        by = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + t ** 2 * target_y
        pyautogui.moveTo(int(bx), int(by), _pause=False)
        time.sleep(step_delay)


def _human_move_to(x, y):
    """Di chuột tới (x, y) theo kiểu người thật (Bezier hoặc thẳng)."""
    if HUMAN.mouse_curve_enabled:
        _bezier_move(x, y)
    else:
        pyautogui.moveTo(x, y, duration=r(*HUMAN.mouse_move_duration))


def click_once(x, y, img_size=None):
    """
    Click tại toạ độ ảnh (x, y) với đầy đủ hiệu ứng human-like:
    1. Chuyển physical → logical coords
    2. Thêm offset ngẫu nhiên TRONG PHẠM VI ẢNH (không bao giờ click ra ngoài)
    3. Di chuột theo đường cong Bezier
    4. Hover trước click (30% chance)
    5. Micro jitter (rung nhẹ tay)
    6. Click
    7. Micro pause ngẫu nhiên sau click

    img_size: (width, height) của ảnh template đã tìm được.
              Nếu có, offset sẽ nằm trong phạm vi ảnh.
              Nếu không có, offset nhỏ cố định ±5px.
    """
    lx, ly = _to_logical(x, y)

    # 1) Random offset — click ở vị trí khác trong ảnh, KHÔNG ra ngoài
    if HUMAN.click_offset_enabled:
        if img_size:
            # img_size = (width, height) tính bằng physical pixels
            # Chuyển sang logical pixels
            sx, sy = _get_scale()
            half_w = (img_size[0] / sx) / 2
            half_h = (img_size[1] / sy) / 2
            # Offset tối đa = ratio * nửa kích thước ảnh
            max_ox = half_w * HUMAN.click_offset_ratio
            max_oy = half_h * HUMAN.click_offset_ratio
            lx += int(r(-max_ox, max_ox))
            ly += int(r(-max_oy, max_oy))
        else:
            # Fallback: offset nhỏ an toàn
            lx += random.randint(-5, 5)
            ly += random.randint(-3, 3)

    # 2) Di chuột theo đường cong Bezier
    _human_move_to(lx, ly)

    # 3) Hover trước click (như suy nghĩ)
    if HUMAN.hover_enabled and random.random() < HUMAN.hover_chance:
        time.sleep(r(*HUMAN.hover_delay))

    # 4) Micro jitter — rung nhẹ tay
    if HUMAN.jitter_enabled:
        jx = random.randint(*HUMAN.jitter_px) * random.choice([-1, 1])
        jy = random.randint(*HUMAN.jitter_px) * random.choice([-1, 1])
        pyautogui.moveRel(jx, jy, duration=0.05)

    # 5) Click
    pyautogui.click()

    # 6) Micro pause ngẫu nhiên sau click
    maybe_micro_pause()


def move_click(x, y, img_size=None):
    """Alias cho click_once (giữ tương thích code cũ)."""
    click_once(x, y, img_size=img_size)


def _img_size(pos):
    """Lấy (w, h) từ kết quả wait_image nếu có, None nếu không."""
    if pos and hasattr(pos, 'w') and hasattr(pos, 'h'):
        return (pos.w, pos.h)
    return None


def paste_text(text: str):
    """Dán text bằng clipboard (Ctrl+V)."""
    if text is None:
        return
    pyperclip.copy(text)
    rsleep("tiny")
    pyautogui.hotkey('ctrl', 'v')
    rsleep("tiny")


def press_key(key, n=1, bucket="tiny"):
    """Nhấn phím n lần, mỗi lần nghỉ theo bucket."""
    for _ in range(n):
        pyautogui.press(key)
        rsleep(bucket)


def norm(s):
    """Strip whitespace, trả None nếu không phải str."""
    return s.strip() if isinstance(s, str) else None


def _parse_date(s):
    for f in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), f).date()
        except Exception:
            pass
    return None


def _parse_time(s):
    for f in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s.strip(), f).time()
        except Exception:
            pass
    return None


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S7 - GOOGLE SHEETS (kết nối, đọc, ghi)                              │
# └──────────────────────────────────────────────────────────────────────┘


def gs_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIAL_PATH, scope)
    return gspread.authorize(creds)


def get_rows(client, sheet_name):
    try:
        return client.open(SPREADSHEET_NAME).worksheet(sheet_name).get_all_values()
    except Exception as e:
        logging.error(f"Loi get_rows('{SPREADSHEET_NAME}', '{sheet_name}'): {type(e).__name__}: {e}")
        raise


def find_row_by_code(rows, code):
    for row in rows[1:]:
        if row and len(row) > 0 and norm(row[0]) == code:
            return row
    return None


def update_source_status(client, code, status="ĐÃ ĐĂNG"):
    """Tìm dòng trong sheet NGUON có cột G == code, ghi status vào cột M."""
    try:
        ws = client.open(SPREADSHEET_NAME).worksheet(SOURCE_SHEET)
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if len(row) > 12 and norm(row[6]) == code:
                ws.update_cell(i, 13, status)
                logging.info("Đã cập nhật '%s' cho mã %s dòng %d (sheet NGUON).", status, code, i)
                return True
        logging.warning("Không tìm thấy mã %s trong sheet NGUON (cột G).", code)
        return False
    except Exception as e:
        logging.error("Lỗi cập nhật sheet NGUON: %s", e)
        return False


def get_all_ready_codes(rows):
    """Lấy tất cả code cùng kênh, trạng thái OK, lịch hôm nay và giờ > hiện tại."""
    now = datetime.now()
    out = []
    for row in rows[1:]:
        if len(row) > 61 and norm(row[IDX_CHANNEL_AI]) == CHANNEL_CODE and norm(row[IDX_STATUS_AV]) == STATUS_OK:
            d = _parse_date(norm(row[IDX_DATE_BI]) or "")
            t = _parse_time(norm(row[IDX_TIME_BJ]) or "")
            if not d or not t:
                continue
            target_dt = datetime.combine(d, t)
            if d == now.date() and target_dt > now:
                code = norm(row[0])
                if code:
                    out.append(code)
    return out


def get_tomorrow_codes(rows):
    """Lấy code có lịch đúng NGÀY MAI."""
    tomorrow = datetime.now().date() + timedelta(days=1)
    out = []
    for row in rows[1:]:
        if len(row) > 61 and norm(row[IDX_CHANNEL_AI]) == CHANNEL_CODE and norm(row[IDX_STATUS_AV]) == STATUS_OK:
            d = _parse_date(norm(row[IDX_DATE_BI]) or "")
            if d and d == tomorrow:
                code = norm(row[0])
                if code:
                    out.append(code)
    return out


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S8 - QUẢN LÝ FILE & THƯ MỤC                                        │
# └──────────────────────────────────────────────────────────────────────┘

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def has_required_files(dir_path: str) -> bool:
    """Kiểm tra thư mục có đủ: >=1 mp4, >=1 srt, >=1 ảnh."""
    if not os.path.isdir(dir_path):
        return False
    names = os.listdir(dir_path)
    has_mp4 = any(n.lower().endswith(".mp4") for n in names)
    has_srt = any(n.lower().endswith(".srt") for n in names)
    has_img = any(os.path.splitext(n)[1].lower() in IMG_EXTS for n in names)
    return has_mp4 and has_srt and has_img


def get_file_sizes(dir_path: str) -> dict:
    """Trả về dict {filename_gốc: size} của các file bắt buộc (mp4, srt, ảnh).
    Giữ nguyên tên file GỐC (viết hoa/thường) để copy đúng."""
    result = {}
    if not os.path.isdir(dir_path):
        return result
    for name in os.listdir(dir_path):
        ext = os.path.splitext(name)[1].lower()
        if ext == ".mp4" or ext == ".srt" or ext in IMG_EXTS:
            fp = os.path.join(dir_path, name)
            try:
                result[name] = os.path.getsize(fp)  # giữ tên gốc
            except Exception:
                pass
    return result


def verify_local_matches_server(local_folder: str, server_folder: str) -> bool:
    """So sánh TỪNG FILE giữa local và server (case-insensitive).
    Trả về True nếu mọi file trên server đều có ở local với CÙNG dung lượng."""
    server_files = get_file_sizes(server_folder)
    local_files = get_file_sizes(local_folder)

    if not server_files:
        return True

    # Tạo dict lowercase để so sánh case-insensitive
    local_lower = {k.lower(): v for k, v in local_files.items()}

    for name, server_size in server_files.items():
        local_size = local_lower.get(name.lower())
        if local_size is None:
            logging.warning(f"  Thieu file o local: {name}")
            return False
        if local_size != server_size:
            logging.warning(f"  File bi loi: {name} (local={local_size:,} bytes, server={server_size:,} bytes)")
            return False

    return True


def verify_mp4_readable(file_path):
    """Kiểm tra file mp4 có đọc được không.
    Đọc header (8 bytes đầu) + đọc 1 chunk cuối file.
    File bị cắt cụt sẽ thiếu dữ liệu cuối."""
    try:
        size = os.path.getsize(file_path)
        if size < 8:
            logging.warning(f"  MP4 qua nho ({size} bytes): {file_path}")
            return False

        with open(file_path, 'rb') as f:
            # Đọc 8 bytes đầu — mp4 header thường là ftyp
            header = f.read(8)
            if b'ftyp' not in header and b'moov' not in header and b'mdat' not in header:
                logging.warning(f"  MP4 header khong hop le: {file_path}")
                return False

            # Đọc 1MB cuối file — nếu file bị cắt cụt sẽ lỗi hoặc thiếu
            read_pos = max(0, size - 1024 * 1024)
            f.seek(read_pos)
            tail = f.read()
            if len(tail) < min(1024 * 1024, size - read_pos):
                logging.warning(f"  MP4 khong doc duoc cuoi file: {file_path}")
                return False

        logging.info(f"  MP4 OK: {os.path.basename(file_path)} ({size / (1024**3):.2f} GB)")
        return True
    except Exception as e:
        logging.warning(f"  MP4 loi doc: {file_path}: {e}")
        return False


COPY_CHUNK_SIZE = 64 * 1024 * 1024  # 64MB mỗi chunk — phù hợp file 10GB qua mạng
COPY_MAX_RETRIES = 5
# Ngưỡng file "lớn" (>100MB) sẽ dùng robocopy thay vì Python copy
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024


def _copy_chunked(src, dst, src_size):
    """Copy file theo từng chunk 64MB. Retry từng chunk nếu mất kết nối.
    Không copy lại từ đầu khi đứt giữa chừng."""
    src_name = os.path.basename(src)
    copied = 0
    last_log_pct = -1
    CHUNK_RETRIES = 5       # retry mỗi chunk tối đa 5 lần
    CHUNK_RETRY_WAIT = 30   # chờ 30s giữa mỗi retry chunk

    with open(dst, 'wb') as fdst:
        while copied < src_size:
            chunk_ok = False
            for chunk_try in range(1, CHUNK_RETRIES + 1):
                try:
                    with open(src, 'rb') as fsrc:
                        fsrc.seek(copied)
                        chunk = fsrc.read(COPY_CHUNK_SIZE)
                    if not chunk:
                        chunk_ok = True
                        break
                    fdst.write(chunk)
                    fdst.flush()
                    copied += len(chunk)
                    chunk_ok = True
                    break
                except Exception as e:
                    logging.warning(f"    Chunk loi tai {copied:,}/{src_size:,} "
                                    f"(lan {chunk_try}/{CHUNK_RETRIES}): {e}")
                    if chunk_try < CHUNK_RETRIES:
                        time.sleep(CHUNK_RETRY_WAIT)

            if not chunk_ok:
                logging.error(f"    THAT BAI sau {CHUNK_RETRIES} lan retry chunk: {src_name}")
                return False

            # Log tiến độ mỗi 10%
            if src_size > LARGE_FILE_THRESHOLD:
                pct = int(copied * 100 / src_size)
                if pct // 10 > last_log_pct // 10:
                    last_log_pct = pct
                    logging.info(f"    {src_name}: {pct}% ({copied:,}/{src_size:,} bytes)")

        # Flush OS → đĩa
        fdst.flush()
        os.fsync(fdst.fileno())

    # Kiểm tra dung lượng cuối cùng
    dst_size = os.path.getsize(dst)
    return dst_size == src_size


def _copy_robocopy(src_dir, dst_dir, filename):
    """Dùng robocopy (có sẵn trên Windows) để copy 1 file lớn.
    Robocopy được thiết kế cho copy qua mạng: tự retry, chịu lỗi tốt."""
    import subprocess
    cmd = [
        'robocopy',
        src_dir,            # thư mục nguồn
        dst_dir,            # thư mục đích
        filename,           # chỉ copy 1 file này
        '/Z',               # restartable mode — copy từng phần, resume khi đứt
        '/R:10',            # retry 10 lần mỗi file
        '/W:30',            # chờ 30s giữa mỗi retry
        '/NP',              # không hiện progress bar
        '/NDL',             # không hiện tên thư mục
        '/NJH', '/NJS',     # không hiện header/summary
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        # Robocopy exit code: 0=no copy needed, 1=copied OK, >=8=error
        if result.returncode >= 8:
            logging.warning(f"  Robocopy loi (code {result.returncode}):")
            if result.stdout.strip():
                logging.warning(f"  STDOUT: {result.stdout.strip()[:500]}")
            if result.stderr.strip():
                logging.warning(f"  STDERR: {result.stderr.strip()[:500]}")
        else:
            logging.info(f"  Robocopy OK (code {result.returncode}): {filename}")
        return result.returncode < 8
    except Exception as e:
        logging.warning(f"  Robocopy exception: {e}")
        return False


def copy_single_file(src, dst, max_retries=COPY_MAX_RETRIES):
    """Copy 1 file an toàn. File lớn (>100MB) dùng robocopy, nhỏ dùng chunk.
    Retry tối đa 5 lần, chờ lâu hơn giữa mỗi lần.
    Kiểm tra dung lượng CHÍNH XÁC sau mỗi lần copy."""
    src_size = os.path.getsize(src)
    src_name = os.path.basename(src)
    src_dir = os.path.dirname(src)
    dst_dir = os.path.dirname(dst)
    is_large = src_size > LARGE_FILE_THRESHOLD

    last_error = ""

    if is_large:
        logging.info(f"  File lon ({src_size / (1024**3):.1f} GB): {src_name}")

    for attempt in range(1, max_retries + 1):
        try:
            # Xóa file cũ nếu có (file lỗi từ lần trước)
            if os.path.exists(dst):
                os.remove(dst)

            # === COPY ===
            ok = False
            if is_large:
                # File lớn + ổ mạng thường: dùng robocopy
                logging.info(f"  [{attempt}/{max_retries}] Thu robocopy: {src_name}")
                ok = _copy_robocopy(src_dir, dst_dir, src_name)
                if ok and os.path.exists(dst):
                    dst_size = os.path.getsize(dst)
                    ok = (dst_size == src_size)
                    if not ok:
                        logging.warning(f"  Robocopy xong nhung size sai "
                                        f"(dst={dst_size:,}, src={src_size:,})")

            if not ok:
                # Robocopy fail → chờ 30s cho nhả file trước khi chunked copy
                if is_large:
                    logging.info(f"  Robocopy khong duoc -> cho 30s roi thu chunked copy")
                    time.sleep(30)
                logging.info(f"  [{attempt}/{max_retries}] Chunked copy: {src_name}")
                ok = _copy_chunked(src, dst, src_size)

            # === KIỂM TRA ===
            if ok:
                dst_size = os.path.getsize(dst)
                if dst_size == src_size:
                    if attempt > 1:
                        logging.info(f"  Retry thanh cong (lan {attempt}): "
                                     f"{src_name} ({src_size:,} bytes)")
                    return True
                else:
                    last_error = f"size khong khop (src={src_size:,}, dst={dst_size:,})"
                    logging.warning(f"  [{attempt}/{max_retries}] {src_name}: {last_error}")
            else:
                last_error = "copy that bai"
                logging.warning(f"  [{attempt}/{max_retries}] Copy that bai: {src_name}")

            # Xóa file lỗi
            if os.path.exists(dst):
                os.remove(dst)

        except Exception as exc:
            last_error = str(exc)
            logging.warning(f"  [{attempt}/{max_retries}] Loi copy {src_name}: {exc}")
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                except Exception:
                    pass

        # Chờ trước khi retry — Permission denied cần chờ lâu hơn
        if attempt < max_retries:
            if "permission" in last_error.lower() or "denied" in last_error.lower():
                wait = attempt * 60  # 60s, 120s, 180s — file có thể đang bị lock
                logging.info(f"  Permission denied -> cho {wait}s (file co the dang bi lock)...")
            else:
                wait = attempt * 30  # 30s, 60s, 90s, 120s
                logging.info(f"  Cho {wait}s truoc khi thu lai...")
            time.sleep(wait)

    logging.error(f"  THAT BAI sau {max_retries} lan: {src_name} ({src_size:,} bytes)")
    return False


def ensure_local_folder(code):
    """Đảm bảo thư mục local có đủ file ĐÚNG dung lượng.
    Copy TỪNG FILE, kiểm tra dung lượng, retry nếu lỗi."""
    local_folder  = os.path.join(LOCAL_DONE_ROOT, code)
    server_folder = os.path.join(SERVER_DONE_ROOT, code)

    local_enough  = os.path.isdir(local_folder) and has_required_files(local_folder)
    server_enough = has_required_files(server_folder)

    # Trường hợp 1: Local đã có file — kiểm tra từng file khớp server
    if local_enough:
        if server_enough:
            if verify_local_matches_server(local_folder, server_folder):
                logging.info(f"Local da du bo va khop server: {local_folder}")
                return True
            else:
                logging.info(f"Local co file bi loi/thieu -> copy lai tu server.")
                # Tiếp tục xuống phần copy bên dưới
        else:
            logging.info(f"Local da du bo; server khong san. Giu nguyen: {local_folder}")
            return True

    # Trường hợp 2: Cần copy từ server
    if not server_enough:
        logging.error(f"Server thieu bo hoac khong co: {server_folder}")
        return False

    # Tạo thư mục local nếu chưa có
    os.makedirs(local_folder, exist_ok=True)

    # Copy TỪNG FILE — chỉ copy file thiếu hoặc sai dung lượng
    server_files = get_file_sizes(server_folder)
    local_files = get_file_sizes(local_folder)
    local_lower = {k.lower(): v for k, v in local_files.items()}
    all_ok = True

    for filename, server_size in server_files.items():
        src_path = os.path.join(server_folder, filename)  # tên gốc từ server
        dst_path = os.path.join(local_folder, filename)   # giữ nguyên tên gốc

        # Nếu local đã có (case-insensitive) và đúng dung lượng → bỏ qua
        local_size = local_lower.get(filename.lower())
        if local_size == server_size:
            logging.info(f"  OK (da co): {filename} ({server_size:,} bytes)")
            continue

        # Copy file (retry tối đa 3 lần)
        logging.info(f"  Dang copy: {filename} ({server_size:,} bytes)...")
        if not copy_single_file(src_path, dst_path, max_retries=3):
            all_ok = False
            logging.error(f"  KHONG THE COPY: {filename}")

    if not all_ok:
        logging.error(f"Co file copy that bai trong: {local_folder}")
        return False

    # Xác nhận lần cuối: đủ bộ + khớp dung lượng
    if not has_required_files(local_folder):
        logging.error(f"Sau copy, local van thieu bo: {local_folder}")
        return False

    if not verify_local_matches_server(local_folder, server_folder):
        logging.error(f"Sau copy, van co file khong khop: {local_folder}")
        return False

    # Kiểm tra mp4 có đọc được không
    for name in os.listdir(local_folder):
        if name.lower().endswith(".mp4"):
            mp4_path = os.path.join(local_folder, name)
            if not verify_mp4_readable(mp4_path):
                logging.error(f"MP4 bi loi sau copy: {mp4_path}")
                return False

    logging.info(f"Copy hoan tat va xac nhan khop 100%%: {local_folder}")
    return True


def delete_server_folder(code):
    """Xóa thư mục server sau khi đã đăng xong."""
    server_folder = os.path.join(SERVER_DONE_ROOT, code)
    if os.path.isdir(server_folder):
        try:
            shutil.rmtree(server_folder)
            logging.info(f"Da xoa thu muc server: {server_folder}")
        except Exception as e:
            logging.warning(f"Khong xoa duoc server {server_folder}: {e}")


def cleanup_posted_codes():
    """Xóa thư mục local của các mã đã 'ĐÃ ĐĂNG'."""
    logging.info("Don cac ma da dang...")
    client = gs_client()
    ws = client.open(SPREADSHEET_NAME).worksheet(INPUT_SHEET)
    rows = ws.get_all_values()

    for row in rows[1:]:
        code = row[0].strip() if len(row) > 0 else ""
        status = row[STATUS_COL - 1].strip() if len(row) >= STATUS_COL else ""
        if code and status.upper() == "ĐÃ ĐĂNG":
            folder_path = os.path.join(LOCAL_DONE_ROOT, code)
            if os.path.isdir(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    logging.info(f"Da xoa: {folder_path}")
                except Exception as e:
                    logging.warning(f"Khong xoa duoc {folder_path}: {e}")


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S9 - AUTOMATION TRÌNH DUYỆT                                         │
# └──────────────────────────────────────────────────────────────────────┘

def open_run_and_execute(command_line):
    """Win+R → paste lệnh → Enter."""
    pyautogui.hotkey('win', 'r')
    rsleep("small")
    try:
        pyperclip.copy(command_line)
        rsleep("tiny")
        pyautogui.hotkey('ctrl', 'v')
        rsleep("tiny")
    except Exception as e:
        logging.warning("Paste vao Run bi loi: %s -> fallback typewrite", e)
        pyautogui.typewrite(command_line, interval=0.02)
    pyautogui.press('enter')
    rsleep("medium")


def close_browsers_gently_in_rdp():
    """Đóng trình duyệt 3 lớp: nhẹ → mạnh → taskkill."""
    # Xóa temp
    logging.info("Xoa cac file trong thu muc temp...")
    open_run_and_execute('cmd /c del /q /f /s "%temp%\\*.*" >nul 2>&1')
    rsleep("small")

    exebase = os.path.splitext(os.path.basename(RUN_BROWSER_EXE))[0]

    # Lần 1: đóng nhẹ bằng CloseMainWindow()
    ps_close = (
        "$names=@('chrome','msedge','firefox','{ex}');"
        "$procs=Get-Process -ErrorAction SilentlyContinue | ?{{ $names -contains $_.ProcessName }};"
        "foreach($p in $procs){{ if($p.MainWindowHandle -ne 0){{ $null=$p.CloseMainWindow() }} }}"
    ).format(ex=exebase)
    open_run_and_execute(f'powershell -NoProfile -WindowStyle Hidden -Command "{ps_close}"')
    rsleep("small")

    # Lần 2: Stop-Process -Force
    ps_kill = (
        "$names=@('chrome','msedge','firefox','{ex}');"
        "foreach($n in $names){{ $p=Get-Process -Name $n -ErrorAction SilentlyContinue; if($p){{ $p | Stop-Process -Force }}}};"
        "$pf=Get-Process -ErrorAction SilentlyContinue | Where-Object {{ $_.ProcessName -like 'firefox*' }}; if($pf){{ $pf | Stop-Process -Force }};"
    ).format(ex=exebase)
    open_run_and_execute(f'powershell -NoProfile -WindowStyle Hidden -Command "{ps_kill}"')
    rsleep("small")

    # Lần 3: taskkill mạnh
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


def wait_and_click_image(img_path, timeout_sec=30, confidence=0.85):
    """Chờ ảnh xuất hiện rồi click. Tự giảm dần confidence.
    Click ngẫu nhiên TRONG PHẠM VI ẢNH (không ra ngoài)."""
    logging.info("Cho anh (click): %s ...", os.path.basename(img_path))
    end = time.time() + timeout_sec
    confidence_levels = [confidence, 0.8, 0.75, 0.7, 0.65, 0.6]

    while time.time() < end:
        for conf in confidence_levels:
            try:
                # Dùng locateOnScreen để lấy box (left, top, width, height)
                box = pyautogui.locateOnScreen(img_path, confidence=conf)
                if box:
                    # Tâm ảnh
                    cx = box.left + box.width // 2
                    cy = box.top + box.height // 2
                    img_size = (box.width, box.height)
                    click_once(cx, cy, img_size=img_size)
                    logging.info("Da click: %s tai (%d,%d) size=%dx%d conf=%.2f",
                                 os.path.basename(img_path), cx, cy, box.width, box.height, conf)
                    return True
            except Exception:
                pass
        time.sleep(r(*HUMAN.retry_interval))

    logging.error("Khong tim thay anh trong ~%ss: %s", timeout_sec, os.path.basename(img_path))
    return False


def wait_image(img_path, timeout_sec=30, confidence=0.85):
    """Chờ ảnh xuất hiện (KHÔNG click).
    Trả về SimpleNamespace(x, y, w, h) hoặc None.
    x, y = tâm ảnh. w, h = kích thước ảnh (để click_once biết phạm vi)."""
    logging.info("Cho anh (khong click): %s ...", os.path.basename(img_path))
    end = time.time() + timeout_sec
    last_err = None

    while time.time() < end:
        try:
            box = pyautogui.locateOnScreen(img_path, confidence=confidence)
            if box:
                cx = box.left + box.width // 2
                cy = box.top + box.height // 2
                logging.info("Da thay: %s tai (%d,%d) size=%dx%d",
                             os.path.basename(img_path), cx, cy, box.width, box.height)
                return SimpleNamespace(x=cx, y=cy, w=box.width, h=box.height)
        except Exception as e:
            last_err = e
        time.sleep(r(*HUMAN.retry_interval))

    if last_err:
        logging.debug("wait_image last error: %s", last_err)
    logging.error("Het thoi gian cho: %s", os.path.basename(img_path))
    return None


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S10 - BƯỚC 1: UPLOAD FILE & NHẬP METADATA                           │
# └──────────────────────────────────────────────────────────────────────┘

def file_dialog_select_first_mp4(target_folder):
    """Hộp thoại Open: chọn file .mp4 đầu tiên."""
    rsleep("long")

    # Click filename.png trước khi nhập đường dẫn
    logging.info("Tim va click 'filename.png' truoc khi nhap duong dan...")
    if not wait_and_click_image(TEMPLATE_FILENAME,
                                timeout_sec=int(r(*HUMAN.click_timeout)),
                                confidence=r(*HUMAN.click_confidence)):
        logging.warning("Khong tim thay 'filename.png', tiep tuc voi Ctrl+L")
    rsleep("medium")

    # Ctrl+L → dán path → Enter
    pyautogui.hotkey('ctrl', 'l'); rsleep("tiny")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(target_folder)
    pyautogui.press('enter'); rsleep("medium")

    # Alt+N → focus ô File Name → dán *.mp4 → Enter
    pyautogui.keyDown('alt')
    pyautogui.press('n')
    pyautogui.keyUp('alt')
    rsleep("small")  # chờ ô File Name focus (RDP lag)
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text('*.mp4')
    rsleep("small")  # chờ trước khi Enter
    pyautogui.press('enter'); rsleep("long")

    # Chọn file đầu và mở
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.press('space'); rsleep("tiny")
    press_key('tab', 2, "small")
    pyautogui.press('enter'); rsleep("long")


def file_dialog_select_thumbnail():
    """Hộp thoại Open: chọn thumbnail."""
    rsleep("medium")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.press('space'); rsleep("small")
    press_key('tab', 4, "tiny")
    pyautogui.press('enter'); rsleep("long")


def file_dialog_select_srt():
    """Hộp thoại Open: chọn file SRT."""
    logging.info("Tim va click 'filename.png' truoc khi nhap SRT...")
    if not wait_and_click_image(TEMPLATE_FILENAME,
                                timeout_sec=int(r(*HUMAN.click_timeout)),
                                confidence=r(*HUMAN.click_confidence)):
        logging.warning("Khong tim thay 'filename.png', tiep tuc nhap truc tiep")
    rsleep("small")

    paste_text('*.srt'); rsleep("tiny")
    pyautogui.press('enter'); rsleep("small")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.hotkey('shift', 'tab'); rsleep("tiny")
    pyautogui.press('space'); rsleep("medium")
    press_key('tab', 4, "tiny")
    pyautogui.press('enter'); rsleep("long")


def handle_metadata_flow(active_row):
    """
    Bước 1: Nhập metadata video.
    Tiêu đề (BB) → Mô tả (BC) → Thumbnail → Danh sách phát → Click Tiếp.
    """
    title = norm(active_row[IDX_TITLE_BB]) if len(active_row) > IDX_TITLE_BB else ""
    desc  = norm(active_row[IDX_DESC_BC])  if len(active_row) > IDX_DESC_BC  else ""

    # === Dán TIÊU ĐỀ ===
    logging.info("Dan TIEU DE (BB): %s", (title or "(rong)"))
    rsleep("long")
    maybe_random_scroll()
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(title or "")

    # Kiểm tra có thử nghiệm A/B thumbnail không (thunghiem.png)
    # Nếu CÓ: Tab×3 (có thêm 1 ô A/B) — Nếu KHÔNG: Tab×2
    pos_ab = wait_image(TEMPLATE_THU_NGHIEM, timeout_sec=5, confidence=0.75)
    if pos_ab:
        logging.info("Phat hien thu nghiem A/B -> Tab x3 de xuong mo ta.")
        press_key('tab', 3, "tiny")
    else:
        logging.info("Khong co thu nghiem A/B -> Tab x2 de xuong mo ta.")
        press_key('tab', 2, "tiny")
    rsleep("small")

    # === Dán MÔ TẢ ===
    logging.info("Dan MO TA (BC).")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(desc or "")

    # Enter → Tab×2 → chọn THUMBNAIL
    pyautogui.press('enter'); rsleep("tiny")
    press_key('tab', 2, "tiny")
    rsleep("small")

    # END×2 → Enter → mở hộp thoại chọn thumbnail
    logging.info("Nhan END de cuon xuong cuoi trang...")
    pyautogui.press('end'); rsleep("small")
    pyautogui.press('end'); rsleep("medium")
    pyautogui.press('enter'); rsleep("small")

    # Chờ hộp thoại Open
    pos_thumb_open = wait_image(TEMPLATE_OPEN_READY,
                                timeout_sec=int(r(*HUMAN.click_timeout)),
                                confidence=r(*HUMAN.click_confidence))
    if pos_thumb_open:
        file_dialog_select_thumbnail()
    else:
        logging.error("Khong thay hop thoai Open khi chon thumbnail.")
        return

    # === Chọn DANH SÁCH PHÁT ===
    logging.info("Cho anchor 'danhsachphat.png'...")
    pos_dsp = wait_image(TEMPLATE_DANHSACHPHAT,
                         timeout_sec=int(r(*HUMAN.click_timeout)),
                         confidence=r(*HUMAN.click_confidence))
    if not pos_dsp:
        logging.error("Khong tim thay 'danhsachphat.png' => bo qua chon danh sach phat.")
    else:
        move_click(pos_dsp.x, pos_dsp.y, img_size=_img_size(pos_dsp)); rsleep("small")
        pyautogui.press('tab'); rsleep("tiny")
        pyautogui.press('enter'); rsleep("small")
        press_key('tab', 2, "tiny")
        pyautogui.press('enter'); rsleep("small")

    # === Click TIẾP để sang Bước 2 ===
    logging.info("Tim va click nut 'Tiep' de qua Buoc 2...")
    pos = wait_image(TEMPLATE_NEXT_BTN,
                     timeout_sec=int(r(*HUMAN.click_timeout)),
                     confidence=r(*HUMAN.click_confidence))
    if pos:
        click_once(pos.x, pos.y, img_size=_img_size(pos))
    else:
        logging.warning("Khong tim thay nut 'Tiep' sau khi nhap metadata.")


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S11 - BƯỚC 2: PHỤ ĐỀ, END SCREEN, THẺ (CARDS)                      │
# └──────────────────────────────────────────────────────────────────────┘

def handle_step2_flow(active_row):
    """
    Bước 2 gồm 4 phần:
    A) Upload phụ đề SRT
    B) Thiết lập End Screen (2 video + 1 playlist + 1 đăng ký)
    C) Thêm Thẻ Cards (1 playlist + 4 video + timestamps)
    D) Chuyển sang bước Hẹn lịch
    """
    CLICK_TIMEOUT_SEC = int(r(*HUMAN.click_timeout))
    CLICK_CONFIDENCE  = r(*HUMAN.click_confidence)
    STEP2_TIMEOUT_SEC = int(r(*HUMAN.step2_timeout))

    # ─── A) VÀO BƯỚC 2 & UPLOAD PHỤ ĐỀ SRT ───

    logging.info("Vao Buoc 2 (anchor buoc2.png, fallback them.png)...")
    pos_buoc2 = wait_image(TEMPLATE_BUOC2, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_buoc2:
        logging.info("Khong thay buoc2.png -> thu them.png")
        pos_buoc2 = wait_image(TEMPLATE_STEP2_THEM, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_buoc2:
            logging.error("Khong thay buoc2.png / them.png => chua vao Buoc 2.")
            return

    # Lặp click để focus đúng vùng SRT
    MAX_TRIES = 5
    for attempt in range(1, MAX_TRIES + 1):
        logging.info(f"[B2 focus try {attempt}/{MAX_TRIES}] click buoc2 -> Tab*4 -> Enter")
        move_click(pos_buoc2.x, pos_buoc2.y, img_size=_img_size(pos_buoc2)); rsleep("small")
        press_key('tab', 4, "tiny")
        pyautogui.press('enter'); rsleep("small")

        logging.info("Kiem tra 'taiteplen.png' sau Enter...")
        pos_tlp = wait_image(TEMPLATE_TAITEPLEN, timeout_sec=10, confidence=CLICK_CONFIDENCE)
        if pos_tlp:
            logging.info("DA thay 'taiteplen.png' -> tiep tuc.")
            break
        else:
            logging.warning("Chua thay 'taiteplen.png' -> lap lai.")
            pos_buoc2 = wait_image(TEMPLATE_BUOC2, timeout_sec=15, confidence=CLICK_CONFIDENCE) or \
                        wait_image(TEMPLATE_STEP2_THEM, timeout_sec=5, confidence=CLICK_CONFIDENCE)
            if not pos_buoc2:
                logging.error("Mat anchor buoc2/them -> dung Buoc 2.")
                return
    else:
        logging.error(f"Sau {MAX_TRIES} lan van khong thay 'taiteplen.png' -> dung Buoc 2.")
        return

    # Chờ vùng tải phụ đề
    logging.info("Cho 'taiteplen.png' (vung Tai tep len phu de)...")
    if not wait_image(TEMPLATE_TAITEPLEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Khong thay 'taiteplen.png' => khong the mo khu tai phu de.")
        return
    rsleep("long")

    # Click taiteplen → tieptuc → mở hộp thoại Open SRT
    pos_tlp = wait_image(TEMPLATE_TAITEPLEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_tlp:
        logging.error("Khong thay 'taiteplen.png'.")
        return
    move_click(pos_tlp.x, pos_tlp.y, img_size=_img_size(pos_tlp))
    rsleep("long")

    logging.info("Tim va click 'tieptuc.png' de mo hop thoai Open (SRT)...")
    if not wait_and_click_image(TEMPLATE_TIEPTUC, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.warning("Khong thay 'tieptuc.png' -> fallback Tab*3 roi Enter.")
        press_key('tab', 3, "tiny")
        pyautogui.press('enter'); rsleep("long")
    else:
        rsleep("long")

    # Hộp thoại Open: chọn SRT
    pos_open = wait_image(TEMPLATE_OPEN_READY, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_open:
        logging.error("Khong thay open.png khi them SRT.")
        return
    file_dialog_select_srt()

    # Chờ xong.png rồi click
    logging.info("Cho 'xong.png' sau khi upload SRT...")
    pos_done = wait_image(TEMPLATE_DONE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_done:
        logging.error("Khong thay xong.png sau khi them SRT.")
        return
    rsleep("medium")
    move_click(pos_done.x, pos_done.y, img_size=_img_size(pos_done)); rsleep("medium")

    # ─── B) THIẾT LẬP END SCREEN ───

    logging.info("Cho 'manhinhketthuc.png'...")
    if not wait_image(TEMPLATE_ENDSCREEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Khong thay manhinhketthuc.png sau khi them SRT.")
        return

    # Mở editor End Screen
    press_key('tab', 2, "tiny")
    pyautogui.press('enter'); rsleep("medium")
    rsleep("medium")
    maybe_random_scroll()

    # Click chọn màn hình kết thúc
    if not wait_and_click_image(TEMPLATE_CHON_ENDSCREEN, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Khong thay 'chonmanhinhketthuc.png' trong editor End screen.")
        return
    press_key('tab', 3, "tiny")

    # Chọn Video 1 (Enter×2)
    press_key('enter', 2, "small")
    # Chọn Video 2 (Enter×2)
    press_key('enter', 2, "small")

    # Chọn Danh sách phát: Enter → 'd' → Enter → Tab×3 → Enter
    press_key('enter', 1, "small")
    rsleep("tiny")
    pyautogui.press('d'); rsleep("tiny")
    press_key('enter', 1, "small")
    press_key('tab', 3, "tiny")
    press_key('enter', 1, "small")

    # Chọn Đăng ký: Enter → click dangky.png
    press_key('enter', 1, "small")
    pos_dangky = wait_image(TEMPLATE_DANGKY, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if pos_dangky:
        move_click(pos_dangky.x, pos_dangky.y, img_size=_img_size(pos_dangky)); rsleep("small")
    else:
        logging.error("Khong thay 'dangky.png' => bo qua buoc chon Dang ky.")

    # Lưu End Screen
    logging.info("Cho 'luu.png' de luu man hinh ket thuc...")
    pos_save = wait_image(TEMPLATE_SAVE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_save:
        logging.error("Khong thay luu.png de luu man hinh ket thuc.")
        return
    move_click(pos_save.x, pos_save.y, img_size=_img_size(pos_save)); rsleep("medium")

    # ─── C) THÊM THẺ (CARDS) ───

    logging.info("Cho 'ketthucok.png' xac nhan da o man 'Man hinh ket thuc'...")
    if not wait_image(TEMPLATE_KETTHUC_OK, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE):
        logging.error("Khong thay 'ketthucok.png' sau khi Luu End Screen.")
        return
    rsleep("small")

    # Tab → Enter để vào thêm thẻ
    press_key('tab', 1, "tiny")
    pyautogui.press('enter'); rsleep("small")
    rsleep("small")

    # --- Helper: click nút Thẻ (the.png) ---
    def click_the_button(step_tag="the_button"):
        logging.info("Tim va click 'the.png' (nut The)...")
        # Park chuột ra xa để tránh overlay che template
        try:
            pyautogui.moveTo(10, 10, duration=min(0.2, r(*HUMAN.mouse_move_duration)))
            rsleep("tiny")
        except Exception:
            pass

        pos_the = wait_image(TEMPLATE_THE, timeout_sec=int(r(*HUMAN.step2_timeout)),
                             confidence=r(*HUMAN.click_confidence))
        if not pos_the:
            logging.error(f"Khong thay 'the.png' tai buoc {step_tag}.")
            return False

        try:
            click_once(pos_the.x, pos_the.y, img_size=_img_size(pos_the))
        except Exception as e:
            logging.error("Click vao 'the.png' that bai: %s", e)
            return False

        rsleep("small")
        return True

    # --- Helper: click nút the1.png ---
    def click_the1_button(step_tag="the1_button"):
        logging.info("Tim va click 'the1.png'...")
        pos = wait_image(TEMPLATE_THE1, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos:
            logging.error(f"Khong thay 'the1.png' tai buoc {step_tag}.")
            return False
        try:
            click_once(pos.x, pos.y, img_size=_img_size(pos))
        except Exception as e:
            logging.error("Click the1.png that bai: %s", e)
            return False
        rsleep("tiny")
        return True

    # --- Helper: thêm 1 playlist card ---
    def add_single_playlist_card():
        if not click_the_button(step_tag="playlist_open"):
            return False
        press_key('tab', 4, "tiny")
        pyautogui.press('enter'); rsleep("small")
        rsleep("small")
        press_key('tab', 3, "tiny")
        pyautogui.press('enter'); rsleep("medium")
        rsleep("small")
        return True

    # --- Helper: thêm 1 video card ---
    def add_single_video_card_from_column(active_row, idx_col, col_name=""):
        link = norm(active_row[idx_col]) if len(active_row) > idx_col else ""
        if not link:
            logging.warning("Cot %s rong, bo qua the video.", col_name or f"idx {idx_col}")
            return False

        if not click_the1_button(step_tag=f"video_{col_name or idx_col}__open_the1"):
            return False

        rsleep("tiny")
        press_key('tab', 1, "tiny")
        pyautogui.press('enter'); rsleep("medium")

        rsleep("small")
        pos_choose = wait_image(TEMPLATE_CHONVIDEO_CUTHE,
                                timeout_sec=int(r(*HUMAN.step2_timeout)),
                                confidence=r(*HUMAN.click_confidence))
        if not pos_choose:
            logging.error("Khong thay 'chonmotvideocuthe.png' -> bo qua the video %s.", col_name or idx_col)
            return False
        click_once(pos_choose.x, pos_choose.y, img_size=_img_size(pos_choose))

        press_key('tab', 3, "tiny")
        paste_text(link); rsleep("small")

        logging.info("Cho 'tagvideo.png' de chon video goi y...")
        pos_tag = wait_image(TEMPLATE_TAGVIDEO,
                             timeout_sec=int(r(*HUMAN.step2_timeout)),
                             confidence=r(*HUMAN.click_confidence))
        if not pos_tag:
            logging.error("Khong thay 'tagvideo.png' sau khi dan link video %s.", col_name or idx_col)
            return False
        click_once(pos_tag.x, pos_tag.y, img_size=_img_size(pos_tag))
        rsleep("medium")
        return True

    # --- Helper: thêm timestamp ---
    def add_timestamp_hhmmss(ts_value: str, step_label: str):
        if not click_the_button(step_tag=f"timestamp_{step_label}"):
            return False
        press_key('tab', 5, "tiny")
        paste_text(ts_value); rsleep("tiny")
        pyautogui.press('tab'); rsleep("small")
        return True

    # Thêm 1 playlist
    if not add_single_playlist_card():
        logging.warning("Them playlist card that bai — van tiep tuc voi video cards.")

    # Thêm 4 video card
    add_single_video_card_from_column(active_row, IDX_LINK_BD, col_name="BD")
    add_single_video_card_from_column(active_row, IDX_LINK_BE, col_name="BE")
    add_single_video_card_from_column(active_row, IDX_LINK_BF, col_name="BF")
    add_single_video_card_from_column(active_row, IDX_LINK_BG, col_name="BG")

    # Thêm timestamps
    add_timestamp_hhmmss("30:00:00", "30h")
    add_timestamp_hhmmss("10:00:00", "10m")
    add_timestamp_hhmmss("15:00:00", "15m")
    add_timestamp_hhmmss("20:00:00", "20m")
    add_timestamp_hhmmss("25:00:00", "25m")

    # Lưu Cards
    rsleep("small")
    logging.info("Cho 'luu.png' de luu cac the (Cards)...")
    pos_save_cards = wait_image(TEMPLATE_SAVE, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_save_cards:
        logging.error("Khong thay luu.png de luu cac the.")
        return
    move_click(pos_save_cards.x, pos_save_cards.y, img_size=_img_size(pos_save_cards)); rsleep("medium")

    # ─── D) CHUYỂN SANG BƯỚC HẸN LỊCH ───

    logging.info("Click 'Che do hien thi' de sang buoc hen lich...")
    pos_cdhien = wait_image(TEMPLATE_CHEDO_HIEN_THI, timeout_sec=STEP2_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
    if not pos_cdhien:
        logging.error("Khong thay 'chedohienthi.png' => khong the sang man hen lich.")
        return False
    move_click(pos_cdhien.x, pos_cdhien.y, img_size=_img_size(pos_cdhien))
    rsleep("long")
    return True


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S12 - BƯỚC 3-4: HẸN LỊCH & CẬP NHẬT TRẠNG THÁI                     │
# └──────────────────────────────────────────────────────────────────────┘

def handle_step3_4_flow(active_row, client, code):
    """
    Bước 3-4: Nhập ngày/giờ hẹn lịch → Click Lên lịch → Cập nhật trạng thái.
    """
    CLICK_TIMEOUT_SEC = int(r(*HUMAN.click_timeout))

    # Click henlich.png để vào màn hẹn lịch
    logging.info("Tim va click 'henlich.png' de vao man hen lich...")
    if not wait_and_click_image(TEMPLATE_HENLICH, timeout_sec=CLICK_TIMEOUT_SEC):
        logging.error("Khong tim thay 'henlich.png' => khong the vao man hen lich.")
        return False

    logging.info("Da vao man hen lich, doi UI on dinh...")
    rsleep("medium")
    maybe_random_scroll()

    # Tab×8 → Enter → vào ô Ngày
    press_key('tab', 8, "tiny")
    pyautogui.press('enter'); rsleep("small")

    # === Dán NGÀY (BI) ===
    date_val = norm(active_row[IDX_DATE_BI]) if len(active_row) > IDX_DATE_BI else ""
    logging.info("Dan NGAY (BI): %s", date_val or "(rong)")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(date_val or "")
    pyautogui.press('enter'); rsleep("small")

    # === Dán GIỜ (BJ) ===
    time_val = norm(active_row[IDX_TIME_BJ]) if len(active_row) > IDX_TIME_BJ else ""
    logging.info("Dan GIO (BJ): %s", time_val or "(rong)")

    pos_time = wait_image(TEMPLATE_TIME, timeout_sec=CLICK_TIMEOUT_SEC)
    if not pos_time:
        logging.error("Khong thay 'time.png' (o Gio).")
        return False

    move_click(pos_time.x, pos_time.y, img_size=_img_size(pos_time)); rsleep("small")
    pyautogui.hotkey('ctrl', 'a'); rsleep("tiny")
    paste_text(time_val or "")
    pyautogui.press('enter'); rsleep("small")

    # === Click LÊN LỊCH ===
    logging.info("Tim va click 'lenlich.png' de xac nhan hen lich...")
    pos_publish = wait_image(TEMPLATE_SCHEDULE_PUBLISH, timeout_sec=CLICK_TIMEOUT_SEC)
    if not pos_publish:
        logging.error("Khong thay lenlich.png (nut Len lich).")
        return False

    move_click(pos_publish.x, pos_publish.y, img_size=_img_size(pos_publish)); rsleep("medium")

    # === KIỂM TRA: đôi khi cần click "kiemtra.png" để hoàn thành ===
    logging.info("Kiem tra xem co 'kiemtra.png' khong...")
    pos_kt = wait_image(TEMPLATE_KIEM_TRA, timeout_sec=10, confidence=0.75)
    if pos_kt:
        logging.info("Thay 'kiemtra.png' -> click de hoan thanh dang.")
        move_click(pos_kt.x, pos_kt.y, img_size=_img_size(pos_kt))
        rsleep("medium")
    else:
        logging.info("Khong thay 'kiemtra.png' -> khong can, tiep tuc.")

    # === CẬP NHẬT TRẠNG THÁI ===
    try:
        update_source_status(client, code, "ĐÃ ĐĂNG")
        logging.info("Da cap nhat 'DA DANG' cho ma %s.", code)
    except Exception as e:
        logging.warning("Cap nhat trang thai loi: %s", e)

    # Chờ 10 phút để YouTube xử lý
    logging.info("Cho 10 phut de YouTube xu ly truoc khi chuyen sang ma ke.")
    time.sleep(10 * 60)

    return True


# ┌──────────────────────────────────────────────────────────────────────┐
# │ S13 - MAIN LOOP                                                     │
# └──────────────────────────────────────────────────────────────────────┘

def pre_stage_tomorrow(input_rows):
    """Copy sẵn video ngày mai."""
    try:
        tomorrow_codes = get_tomorrow_codes(input_rows)
        if tomorrow_codes:
            tmr_ok = [c for c in tomorrow_codes
                      if has_required_files(os.path.join(SERVER_DONE_ROOT, c))
                      or has_required_files(os.path.join(LOCAL_DONE_ROOT, c))]
            if tmr_ok:
                logging.info(f"Pre-stage NGAY MAI: {len(tmr_ok)} ma: {tmr_ok}")
                for c in tmr_ok:
                    try:
                        ensure_local_folder(c)
                    except Exception as e:
                        logging.warning(f"Pre-stage loi {c}: {e}")
            else:
                logging.info("Khong co ma ngay mai du bo de pre-stage.")
        else:
            logging.info("Khong co ma ngay mai de pre-stage.")
    except Exception as e:
        logging.warning(f"Loi khi pre-stage ngay mai: {e}")


def wait_for_internet(max_wait=1800):
    """Chờ có mạng trước khi bắt đầu. Thử mỗi 30s, tối đa 30 phút."""
    import socket
    start = time.time()
    while time.time() - start < max_wait:
        try:
            socket.create_connection(("oauth2.googleapis.com", 443), timeout=10).close()
            return True
        except Exception:
            remaining = int(max_wait - (time.time() - start))
            logging.warning(f"Khong co mang. Thu lai sau 30s... (con {remaining}s)")
            time.sleep(30)
    logging.error("Het %d phut van khong co mang.", max_wait // 60)
    return False


def main():
    import traceback
    random.seed()

    # Kiểm tra mạng trước — tránh crash ngay khi gọi Google Sheets
    if not wait_for_internet():
        logging.error("Khong co mang -> bo qua phien nay.")
        return

    try:
        cleanup_posted_codes()
    except Exception as e:
        logging.warning(f"cleanup_posted_codes loi (khong anh huong): {e}")

    BROWSER_LAUNCH_WAIT_SEC = int(r(*HUMAN.browser_wait))
    CLICK_TIMEOUT_SEC       = int(r(*HUMAN.click_timeout))
    CLICK_CONFIDENCE        = r(*HUMAN.click_confidence)

    client     = gs_client()
    input_rows = get_rows(client, INPUT_SHEET)

    # === Xác định danh sách mã cần đăng ===
    ready_codes = get_all_ready_codes(input_rows)
    if not ready_codes:
        logging.info(f"Khong co ma thoa ({CHANNEL_CODE}, {STATUS_OK}) cho hom nay. Pre-stage ngay mai.")
        pre_stage_tomorrow(input_rows)
        return

    # Lọc: chỉ giữ mã có đủ file ở local hoặc server
    ready_codes = [c for c in ready_codes
                   if has_required_files(os.path.join(LOCAL_DONE_ROOT, c))
                   or has_required_files(os.path.join(SERVER_DONE_ROOT, c))]
    for c in set(get_all_ready_codes(input_rows)) - set(ready_codes):
        logging.warning("Bo ma %s: thieu bo o ca local & server.", c)

    if not ready_codes:
        logging.info("Khong con ma hop le sau khi kiem tra thu muc. Pre-stage ngay mai.")
        pre_stage_tomorrow(input_rows)
        return

    logging.info(f"Phien nay se dang {len(ready_codes)} ma: {ready_codes}")

    # Pre-stage tất cả mã
    for c in ready_codes:
        try:
            ensure_local_folder(c)
        except Exception as e:
            logging.warning(f"Prestage loi {c}: {e}")

    # Đóng browser cũ → mở browser mới
    close_browsers_gently_in_rdp()
    rsleep("small")

    logging.info("Mo trinh duyet: %s", RUN_BROWSER_EXE)
    open_run_and_execute(RUN_BROWSER_EXE)
    time.sleep(BROWSER_LAUNCH_WAIT_SEC)

    # === VÒNG LẶP ĐĂNG TỪNG MÃ ===
    first_time = True
    processed_codes = set()
    error_retry_count = {}  # đếm số lần retry khi video lỗi

    for round_idx, code in enumerate(ready_codes, 1):
      try:
        if code in processed_codes:
            logging.info("Ma %s da xu ly. Bo qua.", code)
            continue

        logging.info("=== Vong dang #%d | CODE: %s ===", round_idx, code)

        active_row = find_row_by_code(input_rows, code)
        if not active_row:
            logging.error("Khong tim thay dong du lieu cho ma: %s", code)
            continue

        target_folder = FOLDER_PATTERN.format(code=code)
        logging.info("Thu muc ma: %s", target_folder)

        if not ensure_local_folder(code):
            logging.error(f"Khong the chuan bi thu muc video cho ma {code} => bo qua.")
            continue

        # Mở tab mới (trừ lần đầu)
        if not first_time:
            pyautogui.hotkey('ctrl', 't'); rsleep("small")

        # Điều hướng tới trang upload
        logging.info("Di toi: %s", UPLOAD_URL)
        pyautogui.hotkey('ctrl', 'l'); rsleep("tiny")
        paste_text(UPLOAD_URL)
        pyautogui.press('enter'); rsleep("medium")

        # Phóng to cửa sổ
        logging.info("Phong to cua so trinh duyet...")
        try:
            pyautogui.keyDown('alt'); pyautogui.press('space'); pyautogui.keyUp('alt'); rsleep("tiny")
            pyautogui.press('x'); rsleep("small")
        except Exception:
            logging.warning("Phong to bang Alt+Space -> X that bai.")
        try:
            pyautogui.keyDown('win'); pyautogui.press('up'); pyautogui.keyUp('win'); rsleep("small")
        except Exception:
            logging.warning("Phong to bang Win+Up that bai.")

        pyautogui.press('f5'); rsleep("medium")

        # Chờ nút Select files
        logging.info("Cho nut Select files (chonfile.png)...")
        if not wait_and_click_image(TEMPLATE_SELECT_BTN,
                                    timeout_sec=CLICK_TIMEOUT_SEC,
                                    confidence=CLICK_CONFIDENCE):
            logging.warning("Het han chua thay chonfile.png -> F5 roi thu lai.")
            try:
                pyautogui.press('f5')
            except Exception:
                pass
            rsleep("medium")
            if not wait_and_click_image(TEMPLATE_SELECT_BTN,
                                        timeout_sec=max(20, CLICK_TIMEOUT_SEC // 2),
                                        confidence=CLICK_CONFIDENCE):
                logging.error("Khong click duoc nut Select files. Bo qua ma %s.", code)
                continue

        # Chờ hộp thoại Open
        logging.info("Cho hop thoai Open (open.png)...")
        pos_open = wait_image(TEMPLATE_OPEN_READY, timeout_sec=CLICK_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_open:
            logging.error("Khong thay open.png. Bo qua ma %s.", code)
            first_time = False
            continue

        # Chọn .mp4
        logging.info("Chon .mp4 dau tien trong: %s", target_folder)
        file_dialog_select_first_mp4(target_folder)
        logging.info("Da chon video — YouTube bat dau upload.")

        # Chờ metadata sẵn sàng
        pos_next = wait_image(TEMPLATE_NEXT_BTN, timeout_sec=CLICK_TIMEOUT_SEC, confidence=CLICK_CONFIDENCE)
        if not pos_next:
            logging.error("Khong thay giao dien metadata voi ma %s. Bo qua.", code)
            first_time = False
            continue

        # === THỰC HIỆN 3 BƯỚC CHÍNH ===
        handle_metadata_flow(active_row)      # Bước 1

        # === KIỂM TRA VIDEO ĐANG TẢI (doitai.png) TRƯỚC KHI VÀO BƯỚC 2 ===
        skip_step2 = False
        logging.info("Kiem tra video dang tai (doitai.png)...")
        pos_doitai = wait_image(TEMPLATE_DOI_TAI, timeout_sec=15, confidence=0.75)

        if pos_doitai:
            # Video đang tải → chờ tối đa 1 tiếng cho nó biến mất
            logging.info("Video dang tai! Cho toi da 1 tieng de tai xong...")
            WAIT_UPLOAD_MAX = 60 * 60  # 1 tiếng
            end_wait = time.time() + WAIT_UPLOAD_MAX
            check_count = 0
            video_error = False

            while time.time() < end_wait:
                time.sleep(60)  # chờ 1 phút rồi mới kiểm tra lại
                check_count += 1

                # Kiểm tra loi.png — video bị lỗi (mp4 hỏng)
                pos_loi = wait_image(TEMPLATE_LOI, timeout_sec=5, confidence=0.70)
                if pos_loi:
                    logging.error("PHAT HIEN LOI VIDEO (loi.png)! MP4 bi hong.")
                    video_error = True
                    break

                still_uploading = wait_image(TEMPLATE_DOI_TAI, timeout_sec=30, confidence=0.70)
                if not still_uploading:
                    logging.info("Video da tai xong! Tiep tuc Buoc 2 binh thuong.")
                    break
                remaining = int((end_wait - time.time()) / 60)
                logging.info(f"Van dang tai... lan kiem tra {check_count}, con ~{remaining} phut.")
            else:
                # Hết 1 tiếng vẫn chưa xong → bỏ qua Step 2
                logging.warning("Het 1 tieng van chua tai xong -> bo qua Buoc 2, chuyen thang hen lich.")
                skip_step2 = True

            # === XỬ LÝ VIDEO LỖI: đóng browser → xóa local → copy lại → thử lại ===
            if video_error:
                retries = error_retry_count.get(code, 0)
                if retries >= 2:
                    logging.error(f"Ma {code} da loi {retries} lan -> BO QUA vinh vien.")
                    continue

                error_retry_count[code] = retries + 1
                logging.info(f"Dong browser, xoa file loi, copy lai tu server (lan thu {retries + 1}/2)...")
                close_browsers_gently_in_rdp()
                rsleep("small")

                # Xóa thư mục local bị lỗi
                local_folder_err = os.path.join(LOCAL_DONE_ROOT, code)
                try:
                    if os.path.isdir(local_folder_err):
                        shutil.rmtree(local_folder_err, ignore_errors=True)
                        logging.info(f"Da xoa local loi: {local_folder_err}")
                except Exception as ex:
                    logging.warning(f"Khong xoa duoc local: {ex}")

                # Copy lại từ server
                copy_ok = ensure_local_folder(code)
                if not copy_ok:
                    logging.error(f"Copy lai tu server that bai -> bo qua ma {code}.")
                    continue

                # Thêm mã này lại cuối danh sách để thử lại
                ready_codes.append(code)
                logging.info(f"Da them lai ma {code} vao cuoi danh sach de thu lai.")

                # Mở lại browser
                logging.info("Mo lai browser...")
                open_run_and_execute(RUN_BROWSER_EXE)
                time.sleep(BROWSER_LAUNCH_WAIT_SEC)
                first_time = True
                continue

        else:
            logging.info("Khong thay doitai.png -> video da san sang, vao Buoc 2 binh thuong.")

        if not skip_step2:
            handle_step2_flow(active_row)         # Bước 2 đầy đủ
        else:
            # Bỏ qua Step 2, chỉ click "Chế độ hiển thị" để sang Step 3-4
            logging.info("Bo qua Buoc 2 -> click 'Che do hien thi' de sang hen lich...")
            wait_and_click_image(TEMPLATE_CHEDO_HIEN_THI,
                                 timeout_sec=int(r(*HUMAN.click_timeout)),
                                 confidence=r(*HUMAN.click_confidence))
            rsleep("long")

        ok = handle_step3_4_flow(active_row, client, code)  # Bước 3-4

        if not ok:
            logging.error("Dang/len lich khong xac nhan duoc => bo qua.")
            continue

        processed_codes.add(code)
        first_time = False

      except Exception as ex_code:
        logging.error(f"LOI KHONG XAC DINH voi ma {code}: {ex_code}")
        logging.error("Chi tiet:\n%s", traceback.format_exc())
        logging.info(f"Bo qua ma {code}, tiep tuc ma tiep theo...")
        first_time = False
        continue

    logging.info("Da hoan thanh %d/%d ma trong danh sach.", len(processed_codes), len(ready_codes))

    # Pre-stage ngày mai
    pre_stage_tomorrow(input_rows)


if __name__ == "__main__":
    import traceback
    fail_count = 0
    while True:
        try:
            main()
            fail_count = 0  # reset nếu chạy thành công
        except Exception as e:
            fail_count += 1
            logging.error("Loi khi chay main(): %s", e)
            logging.error("Chi tiet loi:\n%s", traceback.format_exc())
            # Lỗi mạng → chờ 2 phút
            if "resolve" in str(e).lower() or "connection" in str(e).lower():
                logging.info("Loi mang -> cho 2 phut roi thu lai.")
                time.sleep(2 * 60)
                continue
            # Lỗi khác → chờ tăng dần: 1p, 2p, 5p, 10p (tối đa 10 phút)
            wait_min = min(fail_count * 2, 10)
            logging.info(f"Loi lan {fail_count} -> cho {wait_min} phut roi thu lai.")
            time.sleep(wait_min * 60)
            continue
        # Chạy xong OK → chờ 30 phút rồi kiểm tra lại (thay vì 3 tiếng)
        logging.info("Xong phien. Cho 30 phut roi kiem tra ma moi...")
        time.sleep(30 * 60)
