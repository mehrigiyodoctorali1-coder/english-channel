#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_cards.py — content_bank.json dagi har bir kurs posti uchun
images/<id>.png karta-rasm yaratadi (image_designer asosida).
Yangi ko'nikma turlari uchun temalar qo'shilgan (fayl o'zgartirilmaydi, runtime).
"""
import os, json
import image_designer as idg

BASE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(BASE, "images")
os.makedirs(IMAGES, exist_ok=True)

# Yangi ko'nikma temalari (gradient yuqori, past)
idg.THEMES.update({
    "speaking":  ((37, 99, 235), (29, 78, 216)),
    "writing":   ((13, 148, 136), (8, 145, 178)),
    "reading":   ((5, 150, 105), (4, 120, 87)),
    "listening": ((124, 58, 237), (76, 29, 149)),
    "review":    ((234, 88, 12), (190, 24, 93)),
})
idg.TYPE_LABEL.update({
    "speaking": "SPEAKING", "writing": "WRITING", "reading": "READING",
    "listening": "LISTENING", "review": "REVIEW",
})

data = json.load(open(os.path.join(BASE, "content_bank.json"), encoding="utf-8"))
n = 0
for p in data["posts"]:
    out = os.path.join(IMAGES, f"{p['id']}.png")
    card = dict(p)
    card["emoji"] = ""   # markaziy emoji "tofu" artefaktidan qochish (toza diz