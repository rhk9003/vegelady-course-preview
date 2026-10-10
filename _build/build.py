#!/usr/bin/env python3
"""組裝銷售頁預覽（單一版本，輸出根目錄 index.html）。

原始檔在 _src/：
- 區塊用 data-sec="區塊名稱" 標記（修改單裡顯示的位置名稱）
- 可修改的文字用 data-c 標記（不可巢狀）
本腳本把 data-c 依出現順序換成 data-copy-id="copy-NNN" data-copy-label="區塊名稱"，
並補上共用的 <head>、預覽列、頁尾。改頁面文字請改 _src/ 後重跑：

    python3 _build/build.py

改了文字就要同步提高 revision（舊瀏覽器草稿會因原文不符被拒絕匯入，不會誤套）。
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

PAGES = {
    # 只做一版（D&J 文案）；輸出到根目錄 index.html。
    "index": {
        "out": "index.html",
        "prefix": "",
        "review_page": "landing",
        "title": "羽試・2026 高效搶分實戰先修班｜銷售頁預覽",
        "review_title": "羽試 先修班銷售頁",
        "revision": "yushi-lp-2026-10-10",
    },
}

HEAD = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="description" content="羽試國考培育學院免費先修班銷售頁排版預覽。"><meta name="theme-color" content="#a66440"><title>{title}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700&amp;family=Noto+Serif+TC:wght@400;500;600;700&amp;display=swap" rel="stylesheet"><link rel="stylesheet" href="{prefix}styles.css"><script defer src="{prefix}script.js"></script><link rel="stylesheet" href="{prefix}review.css"><script defer src="{prefix}review-core.js"></script><script defer src="{prefix}review.js"></script></head>
<body data-review-page="{review_page}" data-review-revision="{revision}" data-review-title="{review_title}">
<a class="skip-link" href="#main">跳至主要內容</a>
<div class="preview-bar"><span>羽試｜先修班銷售頁提案・設計預覽</span><span>右下角「提出文字修改」可直接留修改</span></div>
"""

FOOT = """<footer class="site-footer" data-sec="導覽與頁尾"><div class="wrap"><div class="footer-inner"><div><a class="logo" href="#main" aria-label="回到頁首"><img src="{prefix}assets/logo-mark.png" alt="" width="46" height="46"><span class="logo-text">羽試國考培育學院<small>VEGELADY</small></span></a><p data-c>羽化成蝶｜和更高版本的自己相識</p></div><div class="footer-links"><a href="https://vegelady.com/" target="_blank" rel="noopener noreferrer">官網首頁 ↗</a><a href="https://vegelady.com/free-course/" target="_blank" rel="noopener noreferrer">原先修課頁 ↗</a><a href="mailto:dura@vegelady.com">聯絡信箱</a></div></div><div class="footer-bottom"><span>羽試培育工作室 © All Rights Reserved.｜統編 00618628</span><span>聯絡電話 0983934599</span></div><p class="preview-note">版型預覽提案・非正式官網｜照片與原文取自羽試國考培育學院公開頁面（2026-10-09 讀取），報名按鈕連至目前的報名表。</p></div></footer>
<div class="mobile-cta"><span>免費線上先修班</span><a href="https://go.vegelady.com/#form" target="_blank" rel="noopener noreferrer">免費報名 ↗</a></div>
</body></html>
"""


def number_copy(html: str) -> str:
    out, n, label = [], 0, "頁首"
    for token in re.split(r"(<[^>]+>)", html):
        if token.startswith("<") and not token.startswith("</"):
            m = re.search(r'\sdata-sec="([^"]*)"', token)
            if m:
                label = m.group(1)
                token = token.replace(m.group(0), "", 1)
            if re.search(r"\sdata-c(?=[\s>/])", token):
                n += 1
                token = re.sub(r"\sdata-c(?=[\s>/])",
                               f' data-copy-id="copy-{n:03d}" data-copy-label="{label}"', token, count=1)
        out.append(token)
    return "".join(out)


def check_nesting(html: str, page: str) -> None:
    depth_stack = []
    for token in re.split(r"(<[^>]+>)", html):
        if not token.startswith("<") or token.startswith("<!"):
            continue
        tag = re.match(r"</?([a-zA-Z0-9]+)", token)
        if not tag:
            continue
        name = tag.group(1).lower()
        if name in {"br", "img", "meta", "link", "input", "source", "hr", "wbr"}:
            continue
        if token.startswith("</"):
            while depth_stack:
                open_name, has_copy = depth_stack.pop()
                if open_name == name:
                    break
            continue
        has_copy = "data-copy-id=" in token
        if has_copy and any(c for _, c in depth_stack):
            raise SystemExit(f"{page}: 可修改區塊巢狀：{token[:80]}")
        depth_stack.append((name, has_copy))


def main() -> None:
    for page, cfg in PAGES.items():
        body = (ROOT / "_src" / f"{page}.html").read_text(encoding="utf-8")
        body = body.replace("../assets/", cfg["prefix"] + "assets/")
        html = HEAD.format(**cfg) + body.strip() + "\n" + FOOT.replace("{prefix}", cfg["prefix"])
        html = number_copy(html)
        check_nesting(html, page)
        leftover = re.findall(r"\sdata-(?:c|sec)(?=[\s=>/])", html)
        assert not leftover, (page, leftover[:3])
        out = ROOT / cfg["out"]
        out.write_text(html, encoding="utf-8")
        print(page, html.count("data-copy-id="), "個可修改區塊 →", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
