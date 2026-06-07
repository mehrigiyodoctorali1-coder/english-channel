#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
English free course — Telegram avtomatik poster (rasm + ketma-ket rejim)
========================================================================
Kontent bankidan keyingi postni rasm-karta bilan kanalga yuboradi.
Pillow bo'lsa rasm bilan (sendPhoto), bo'lmasa matn bilan (sendMessage).

Ishlatish:
    python telegram_poster.py              # ketma-ket: keyingi yuborilmagan post
    python telegram_poster.py --dry-run    # yubormasdan, ko'rsatadi
    python telegram_poster.py --test-connection
    python telegram_poster.py --slot morning   # (eski) slot bo'yicha tanlash
"""

import json
import os
import sys
import time
import uuid
import argparse
import mimetypes
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CONTENT_FILE = os.path.join(BASE_DIR, "content_bank.json")
STATE_FILE = os.path.join(BASE_DIR, "posted_log.json")
NEWS_FILE = os.path.join(BASE_DIR, "news_today.txt")

API = "https://api.telegram.org/bot{token}/{method}"

# Rasm generatori (ixtiyoriy)
try:
    import image_designer
    HAS_IMAGE = True
except Exception:
    HAS_IMAGE = False


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def telegram_call(token, method, params):
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error_code": e.code,
                "description": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def send_message(token, chat_id, text):
    return telegram_call(token, "sendMessage", {
        "chat_id": chat_id, "text": text, "disable_web_page_preview": "true"})


def send_photo(token, chat_id, photo_path, caption):
    """Multipart/form-data orqali rasm + izoh yuboradi (stdlib bilan)."""
    url = API.format(token=token, method="sendPhoto")
    boundary = "----WebKitBoundary" + uuid.uuid4().hex
    with open(photo_path, "rb") as f:
        photo_bytes = f.read()
    fname = os.path.basename(photo_path)
    ctype = mimetypes.guess_type(fname)[0] or "image/png"

    parts = []
    def add_field(name, value):
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    add_field("chat_id", chat_id)
    add_field("caption", caption)
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="photo"; filename="{fname}"\r\n'.encode())
    parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
    parts.append(photo_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error_code": e.code,
                "description": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def current_slot(cfg):
    tz = timezone(timedelta(hours=cfg.get("timezone_offset", 5)))
    now_hour = datetime.now(tz).hour
    schedule = cfg.get("schedule", {"morning": 8, "midday": 14, "evening": 20})
    best = None
    for name, hour in sorted(schedule.items(), key=lambda x: x[1]):
        if now_hour >= hour:
            best = name
    return best or min(schedule, key=schedule.get)


def pick_post(content, state, slot=None):
    """slot berilsa - o'sha slotdan; aks holda KETMA-KET (array tartibida)."""
    posted_ids = set(state.get("posted", []))
    if slot:
        candidates = [p for p in content["posts"] if p.get("slot") == slot] \
                     or content["posts"]
    else:
        candidates = content["posts"]  # ketma-ket: butun ro'yxat tartibi

    fresh = [p for p in candidates if p["id"] not in posted_ids]
    if not fresh:
        log("Barcha postlar yuborilgan. Yangi sikl boshlanadi.")
        ids = {p["id"] for p in candidates}
        state["posted"] = [pid for pid in state.get("posted", []) if pid not in ids]
        fresh = candidates

    if slot:
        order = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
        fresh.sort(key=lambda p: (order.get(p.get("level", "B1"), 3), p["id"]))
        return fresh[0]
    return fresh[0]  # ketma-ket: ro'yxatdagi birinchi yuborilmagan


def deliver(token, chat_id, post):
    """Rasm bilan (imkon bo'lsa) yoki matn bilan yuboradi."""
    text = post["text"]
    if HAS_IMAGE:
        try:
            card = image_designer.make_card(post)
            res = send_photo(token, chat_id, card, text)
            if res.get("ok"):
                log("Rasm + izoh yuborildi.")
                return True
            log(f"sendPhoto xato: {res.get('description')} — matnga o'tilyapti.")
        except Exception as e:
            log(f"Rasm yaratilmadi ({e}) — matnga o'tilyapti.")
    res = send_message(token, chat_id, text)
    if res.get("ok"):
        log("Matn yuborildi.")
        return True
    log(f"Yuborilmadi: {res.get('description')}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["morning", "midday", "evening"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test-connection", action="store_true")
    args = parser.parse_args()

    cfg = load_json(CONFIG_FILE) or {}
    # Token/kanal: avval muhit o'zgaruvchisi (GitHub Secrets), keyin config.json
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("bot_token", "")).strip()
    chat_id = (os.environ.get("TELEGRAM_CHANNEL_ID") or cfg.get("channel_id", "")).strip()

    if args.test_connection:
        res = telegram_call(token, "getMe", {})
        log(f"Bot ulandi: @{res['result']['username']}" if res.get("ok")
            else f"Ulanmadi: {res.get('description')}")
        return

    if not args.dry_run and (not token or token.startswith("BU_YERGA")):
        log("XATO: config.json ichida bot_token to'ldirilmagan.")
        sys.exit(1)

    content = load_json(CONTENT_FILE)
    if not content:
        log("XATO: content_bank.json topilmadi.")
        sys.exit(1)

    state = load_json(STATE_FILE, default={"posted": []})
    n = int(os.environ.get("POSTS_PER_RUN", cfg.get("posts_per_run", 3)))
    gap = cfg.get("post_gap_seconds", 20)            # postlar orasidagi pauza
    answer_delay = cfg.get("answer_delay_seconds", 90)  # test javobigacha

    # ── Dry-run: n ta postni ko'rsatish ──
    if args.dry_run:
        for i in range(n):
            post = pick_post(content, state, slot=args.slot)
            state.setdefault("posted", []).append(post["id"])
            print(f"\n===== POST {i+1}/{n} ({post['id']} · {post.get('type')}) =====\n" + post["text"])
            if post.get("answer"):
                print("\n--- JAVOB ---\n" + post["answer"])
        return

    # ── Haqiqiy: n ta post ketma-ket ──
    sent = 0
    for i in range(n):
        post = pick_post(content, state, slot=args.slot)
        log(f"[{i+1}/{n}] {post['id']} ({post.get('type')} - {post.get('level')}) rasm={'ha' if HAS_IMAGE else 'yoq'}")
        if not deliver(token, chat_id, post):
            log("Yuborilmadi — to'xtatildi.")
            break
        state.setdefault("posted", []).append(post["id"])
        state["last_run"] = datetime.now().isoformat()
        save_json(STATE_FILE, state)
        sent += 1
        if post.get("answer"):
            log(f"Javob {answer_delay}s dan keyin...")
            time.sleep(answer_delay)
            r = send_message(token, chat_id, post["answer"])
            log("Javob yuborildi." if r.get("ok") else f"Javob xato: {r.get('description')}")
        if i < n - 1:
            time.sleep(gap)

    # ── Kunlik yangilik — run oxirida bir marta ──
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            news = f.read().strip()
        if news:
            r = send_message(token, chat_id, news)
            if r.get("ok"):
                log("Kunlik yangilik yuborildi.")
                os.remove(NEWS_FILE)

    log(f"Tugadi. {sent} ta post yuborildi.")


if __name__ == "__main__":
    main()
