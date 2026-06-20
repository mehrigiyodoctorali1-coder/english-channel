#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_course_content.py
=======================
30 kunlik B2 kursini (oylik-kontent/day-XX.txt) content_bank.json formatiga
aylantiradi va har post uchun lokal karta-rasm (images/<id>.png) yaratadi.

- Eski postlar "archived_posts" kalitiga ko'chiriladi (o'chmaydi).
- posted_log.json yangi kurs uchun reset qilinadi (eski nusxa saqlanadi).
- Tartib: day01 p1..p4, day02 p1..p4, ... day30 p4  (4 post/kun: 09,12,15,18)
"""
import os, re, json, glob, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DAYS_DIR = os.path.join(BASE, "oylik-kontent")
CONTENT = os.path.join(BASE, "content_bank.json")
STATE = os.path.join(BASE, "posted_log.json")
IMAGES = os.path.join(BASE, "images")
os.makedirs(IMAGES, exist_ok=True)

# Kun -> ko'nikma (7 kunlik rotatsiya)
ROT = ["speaking", "writing", "reading", "listening", "vocabulary", "grammar", "review"]

MARKER = re.compile(r'⏰\s*\d{2}:\d{2}\s*—\s*POST\s*\d+', re.UNICODE)
SEP = lambda s: s.strip() != "" and set(s.strip()) <= set("═")


def split_posts(text):
    parts = MARKER.split(text)
    bodies = []
    for b in parts[1:]:               # parts[0] = sarlavha bloki
        lines = b.split("\n")
        while lines and (lines[-1].strip() == "" or SEP(lines[-1])):
            lines.pop()
        while lines and (lines[0].strip() == "" or SEP(lines[0])):
            lines.pop(0)
        body = "\n".join(lines).strip()
        if body:
            bodies.append(body)
    return bodies


def first_emoji(line):
    for ch in line:
        if ord(ch) >= 0x2190 or ch in "🔁":
            return ch
        if ch.isalnum():
            break
    return ""


def title_of(line, emoji):
    t = line
    if emoji:
        t = t.replace(emoji, "", 1)
    return t.strip(" -—:·").strip()


def build():
    files = sorted(glob.glob(os.path.join(DAYS_DIR, "day-*.txt")))
    posts = []
    for f in files:
        m = re.search(r"day-(\d+)\.txt", f)
        day = int(m.group(1))
        skill = ROT[(day - 1) % 7]
        with open(f, encoding="utf-8") as fh:
            text = fh.read()
        bodies = split_posts(text)
        for i, body in enumerate(bodies, start=1):
            head = body.split("\n", 1)[0]
            emoji = first_emoji(head)
            title = title_of(head, emoji) or skill.upper()
            pid = f"c{day:02d}{'abcd'[i-1]}"
            posts.append({
                "id": pid,
                "type": skill,
                "level": "B2",
                "emoji": emoji,
                "title": title[:60],
                "text": body,
            })
    return posts


def main():
    course = build()
    print(f"Kursdan {len(course)} ta post tayyorlandi.")
    longest = max(len(p["text"]) for p in course)
    print(f"Eng uzun post matni: {longest} belgi (Telegram caption limiti 1024).")

    # --- Backup + integratsiya ---
    data = json.load(open(CONTENT, encoding="utf-8"))
    stamp = datetime.now().strftime("%Y%m%d")
    shutil.copy(CONTENT, os.path.join(BASE, f"content_bank_backup_{stamp}.json"))
    if os.path.exists(STATE):
        shutil.copy(STATE, os.path.join(BASE, f"posted_log_backup_{stamp}.json"))

    old_posts = data.get("posts", [])
    archived = data.get("archived_posts", []) + old_posts
    new_data = {
        "channel": data.get("channel", "English free course (@English_news_free)"),
        "note": "B2 IELTS kursi — 30 kun x 4 post (09:00,12:00,15:00,18:00). "
                "Ketma-ket. Eski postlar archived_posts ichida saqlangan.",
        "course_level": "B2",
        "posts": course,
        "archived_posts": archived,
    }
    json.dump(new_data, open(CONTENT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump({"posted": []}, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"content_bank.json yangilandi: {len(course)} kurs posti + {len(archived)} arxiv.")
    print("posted_log.json reset qilindi.")


if __name__ == "__main__":
    main()
