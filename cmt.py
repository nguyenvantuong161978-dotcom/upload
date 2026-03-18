# -*- coding: utf-8 -*-
import os, json, time, re
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai

# ========== CẤU HÌNH ==========
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
STATE_FILE = "replied_ids.txt"
TRANS_DIR = "transcripts"

DRY_RUN = False                  # True: chỉ in, không đăng
POSTS_PER_RUN = 10              # Giới hạn số comment mỗi lần
SLEEP_BETWEEN_POSTS = 0.5        # Giãn cách giữa các post

# Gemini API key (thay bằng key của bạn)
genai.configure(api_key="AIzaSyDmAmqL-qB3g69DzvDelx3ZDVCs1QSE3FQ")
MODEL_NAME = "models/gemini-2.5-flash"

# ========== KHỞI TẠO ==========
os.makedirs(TRANS_DIR, exist_ok=True)

# ========== TIỆN ÍCH YOUTUBE ==========
def get_youtube():
    import certifi, httplib2
    from google_auth_httplib2 import AuthorizedHttp
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    base_http = httplib2.Http(timeout=60, ca_certs=certifi.where())
    authed_http = AuthorizedHttp(creds, http=base_http)
    return build("youtube", "v3", http=authed_http, cache_discovery=False)

def my_channel_id(yt):
    res = yt.channels().list(part="id,snippet", mine=True).execute()
    items = res.get("items", [])
    if not items:
        raise ValueError("❌ Không tìm thấy channel nào được liên kết với tài khoản này.")
    if len(items) > 1:
        print("⚠️ Có nhiều kênh liên kết với tài khoản này:")
        for idx, it in enumerate(items, start=1):
            print(f"   {idx}. {it['snippet']['title']} → {it['id']}")
        choice = input("👉 Nhập số thứ tự kênh bạn muốn dùng: ").strip()
        try:
            ch = items[int(choice)-1]
        except:
            ch = items[0]
    else:
        ch = items[0]
    print(f"✅ Đang dùng kênh: {ch['snippet']['title']} ({ch['id']})")
    return ch["id"]

def uploads_playlist_id(yt, channel_id):
    res = yt.channels().list(part="contentDetails", id=channel_id).execute()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def list_all_video_ids(yt, uploads_pl_id):
    vids, page_token = [], None
    while True:
        r = yt.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_pl_id,
            maxResults=50,
            pageToken=page_token
        ).execute()
        vids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
        page_token = r.get("nextPageToken")
        if not page_token:
            break
    return vids

def fetch_all_threads_for_videos(yt, video_ids):
    total_videos = len(video_ids)
    print(f"📼 Found {total_videos} videos → scanning all comments...")
    for idx, vid in enumerate(video_ids, start=1):
        print(f"🔍 [{idx}/{total_videos}] Scanning video {vid} ...")
        page_token = None
        while True:
            try:
                r = yt.commentThreads().list(
                    part="snippet,replies",
                    videoId=vid,
                    order="time",
                    textFormat="plainText",
                    maxResults=100,
                    pageToken=page_token
                ).execute()
            except HttpError as e:
                msg = str(e)
                if "commentsDisabled" in msg or "forbidden" in msg:
                    print(f"⚠️ Skip video {vid}: comments disabled/private")
                else:
                    print(f"⚠️ Skip video {vid}: {e}")
                break
            for it in r.get("items", []):
                yield it, vid
            page_token = r.get("nextPageToken")
            if not page_token:
                break
        time.sleep(0.3)

# ========== LƯU TRẠNG THÁI ==========
def load_state():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(x.strip() for x in f if x.strip())

def save_state(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(seen)))

def already_replied_by_me(thread, my_ch):
    replies = (thread.get("replies") or {}).get("comments") or []
    for r in replies:
        author = ((r.get("snippet") or {}).get("authorChannelId") or {}).get("value")
        if author == my_ch:
            return True
    return False

def top_comment_info(thread):
    t = (thread.get("snippet") or {}).get("topLevelComment") or {}
    s = t.get("snippet") or {}
    return t.get("id"), s.get("authorDisplayName"), (s.get("textDisplay") or s.get("textOriginal") or "").strip()

# ========== LẤY NỘI DUNG VIDEO ==========
def fetch_and_cache_transcript(video_id, yt=None):
    cache_path = os.path.join(TRANS_DIR, f"{video_id}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    try:
        parts = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        text = " ".join(p.get("text", "") for p in parts)
        if text.strip():
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(text)
            return text
    except (TranscriptsDisabled, NoTranscriptFound):
        pass
    except Exception as e:
        print("⚠️ Transcript fetch error:", e)

    if yt:
        try:
            r = yt.videos().list(part="snippet", id=video_id).execute()
            items = r.get("items", [])
            if items:
                desc = items[0]["snippet"].get("description", "")
                if desc.strip():
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(desc)
                    return desc
        except Exception as e:
            print("⚠️ Description fallback error:", e)

    with open(cache_path, "w", encoding="utf-8") as f:
        f.write("")
    return ""

def pick_relevant_snippet(transcript_text, comment_text, max_chars=900):
    if not transcript_text:
        return ""
    stop = set(["the","and","for","that","this","with","are","was","but","not","you","your","have","has","had","they","their","from","what","when","where","which","who","how","a","an","in","on","is","it","of","to"])
    tokens = re.findall(r"[A-Za-z0-9']{3,}", comment_text.lower())
    keywords = [t for t in tokens if t not in stop]
    sents = re.split(r'(?<=[.!?])\s+', transcript_text)
    if keywords:
        hits = [s.strip() for s in sents if any(k in s.lower() for k in keywords)]
        if hits:
            snippet = " ".join(hits)
            return snippet[:max_chars].strip()
    return transcript_text[:max_chars].strip()

# ========== SINH PHẢN HỒI ==========
def gen_reply_with_prompt(prompt_text):
    model = genai.GenerativeModel(MODEL_NAME)
    r = model.generate_content(prompt_text)
    reply = (r.text or "").strip()
    if not reply:
        reply = "Thanks for watching and sharing your thoughts!"
    sentences = re.split(r'(?<=[.!?])\s+', reply)
    return " ".join(sentences[:2]).strip()

def post_reply(yt, parent_id, text):
    body = {"snippet": {"parentId": parent_id, "textOriginal": text.strip()}}
    return yt.comments().insert(part="snippet", body=body).execute()

# ========== MAIN ==========
def main():
    yt = get_youtube()
    my_ch = my_channel_id(yt)
    print("🔎 Your channel ID:", my_ch)

    seen = load_state()
    posted = 0

    upl = uploads_playlist_id(yt, my_ch)
    video_ids = list_all_video_ids(yt, upl)
    print(f"📼 Found {len(video_ids)} videos. Scanning comments...")

    scanned = 0
    for th, vid in fetch_all_threads_for_videos(yt, video_ids):
        scanned += 1
        if not (th.get("snippet") or {}).get("canReply", True):
            continue
        if already_replied_by_me(th, my_ch):
            cid, _, _ = top_comment_info(th)
            if cid: seen.add(cid)
            continue

        cid, author, text = top_comment_info(th)
        if not cid or not text or cid in seen:
            continue

        # Lấy transcript / description
        context_text = fetch_and_cache_transcript(vid, yt)
        snippet = pick_relevant_snippet(context_text, text, max_chars=900)

        prompt = (
            "You are a YouTube community manager. "
            "Reply in natural American English, max 2 short sentences, polite, thoughtful; "
            "no emojis, no hashtags. If hostile, de-escalate calmly.\n\n"
            "Channel theme: family betrayal, revenge, karma, emotional healing.\n"
        )
        if snippet:
            prompt += f"\nContext from the video:\n{snippet}\n"
        prompt += f"\nViewer comment: {text}\nTask: reply briefly and naturally."

        try:
            reply = gen_reply_with_prompt(prompt)
        except Exception as e:
            print("⚠️ Gemini error:", e)
            reply = "Thank you for sharing your thoughts with us."

        print(f"\n[{scanned}] 👤 {author}\n💬 {text}\n📝 {reply}")
        try:
            if not DRY_RUN:
                post_reply(yt, cid, reply)
                posted += 1
            seen.add(cid)
            time.sleep(SLEEP_BETWEEN_POSTS)
        except Exception as e:
            print("⚠️ Error posting:", e)
            seen.add(cid)

        if posted >= POSTS_PER_RUN:
            print(f"\n⏹️ Đạt giới hạn {POSTS_PER_RUN} comment. Tạm dừng.")
            break

    save_state(seen)
    print(f"\n✅ Done at {datetime.now(timezone.utc).isoformat()} | Scanned: {scanned} | Posted: {posted}")

if __name__ == "__main__":
    while True:
        print("\n==============================")
        print(f"🚀 Bắt đầu chạy lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            main()
        except Exception as e:
            print("⚠️ Lỗi khi chạy main():", e)
        print(f"✅ Hoàn tất lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⏰ Đang chờ 12 tiếng trước lần chạy tiếp theo...\n")
        time.sleep(12 * 60 * 60)  # 12 tiếng = 12*60*60 giây

