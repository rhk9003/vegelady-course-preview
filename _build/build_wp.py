#!/usr/bin/env python3
"""組裝 WordPress 上線版：一段可貼進 Elementor「HTML」小工具的程式碼。

跟預覽版（build.py）共用 _src/index.html 與 styles.css，差別：
- 拿掉文字修改器（review.js／review.css／review-core.js）、預覽列、預覽註記
- 整頁包進 shadow DOM（#ys-free-course），主題樣式進不來、頁面樣式也不外漏
- 圖片換成 WordPress 媒體庫網址（_wp/media-map.json；沒有對照時用 --assets-base）
- 頁內錨點與選單改由 script 處理（原生 #id 跳轉進不了 shadow DOM）
- --layout site（預設，2026-10-13 Dennis 定）：頁面範本維持「Elementor 全寬」、保留官網頁首頁尾，
  所以拿掉頁面自己的頁首（logo＋頁內導覽）與頁尾，只留手機底部報名按鈕；
  --layout canvas：Elementor Canvas 用，頁首頁尾都由本頁提供

Pixel Cat 轉換（官網現有事件 free-course，URL 觸發 https://lin.ee/fqVra6s）：
Pixel Cat 在 document ready 時用 jQuery 找「href 完全等於該網址的 <a>」綁 click，
shadow DOM 裡的按鈕它找不到。所以在 host 底下（light DOM、不會顯示）放一個同網址的
隱藏連結 #ys-free-course-line 給它綁；頁面上每顆 LINE 按鈕被點時，
用 jQuery(proxy).triggerHandler('click') 只執行 Pixel Cat 綁的事件（不跳頁、不冒泡），
按鈕本身照常開 LINE。一次點擊＝一次 free-course（瀏覽器像素＋CAPI，同一組 event_id 去重）。

    python3 _build/build_wp.py                      # 用 _wp/media-map.json，同時輸出 _wp/elementor-data.json
    python3 _build/build_wp.py --assets-base ../assets/ --out _wp/test/widget-local.html
"""
import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE_URL = "https://lin.ee/fqVra6s"
FONTS = ("https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700"
         "&family=Noto+Serif+TC:wght@400;500;600;700&display=swap")

# 預覽版頁尾（build.py 的 FOOT）去掉預覽註記與「原先修課頁」連結（只有 --layout canvas 用）
FOOTER = """<footer class="site-footer"><div class="wrap"><div class="footer-inner"><div><a class="logo" href="#main" aria-label="回到頁首"><img src="{assets}logo-mark.png" alt="" width="46" height="46"><span class="logo-text">羽試國考培育學院<small>VEGELADY</small></span></a><p>羽化成蝶｜和更高版本的自己相識</p></div><div class="footer-links"><a href="https://vegelady.com/">官網首頁</a><a href="mailto:dura@vegelady.com">聯絡信箱</a></div></div><div class="footer-bottom"><span>羽試培育工作室 © All Rights Reserved.｜統編 00618628</span><span>聯絡電話 0983934599</span></div></div></footer>"""

# 手機底部按鈕（兩種版面都有，收進 shadow DOM）
MOBILE_CTA = """<div class="mobile-cta"><span>免費線上先修班</span><a href="{line}" target="_blank" rel="noopener noreferrer">免費報名 ↗</a></div>"""

# shadow DOM 用的補充樣式（接在 styles.css 後面）
EXTRA_CSS = """
:host{all:initial;display:block}
.ys-page{position:relative;text-align:left}
.ys-page [id]{scroll-margin-top:96px}
@media(max-width:800px){.ys-page [id]{scroll-margin-top:76px}}
"""
# canvas 版面：本頁頁尾在最後，手機底部按鈕要讓出位置（site 版面改由 body 讓）
CANVAS_CSS = "@media(max-width:800px){.ys-page{padding-bottom:64px}}"

SCRIPT = """<script>
(function () {
  var host = document.getElementById('ys-free-course');
  var tpl = document.getElementById('ys-free-course-tpl');
  if (!host || !tpl || host.shadowRoot) return;
  var root = host.attachShadow({ mode: 'open' });
  root.appendChild(tpl.content.cloneNode(true));
  var page = root.querySelector('.ys-page');
  var LINE = '__LINE__';
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var toggle = root.querySelector('.menu-toggle');
  function closeMenu() {
    page.classList.remove('menu-open');
    if (toggle) { toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', '開啟導覽選單'); }
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = page.classList.toggle('menu-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? '關閉導覽選單' : '開啟導覽選單');
    });
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

  // Pixel Cat：轉送給 light DOM 的隱藏連結（它綁的是 href 完全相同的 <a>）
  function sendConversion() {
    var proxy = document.getElementById('ys-free-course-line');
    if (proxy && window.jQuery) window.jQuery(proxy).triggerHandler('click');
  }

  root.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href === LINE) { sendConversion(); return; }
    if (href.charAt(0) === '#' && href.length > 1) {
      var target = root.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      closeMenu();
      target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    }
  });
})();
</script>"""


def strip_review_attrs(html: str) -> str:
    html = re.sub(r'\sdata-sec="[^"]*"', "", html)
    return re.sub(r"\sdata-c(?=[\s>/])", "", html)


def shadow_css(css: str) -> str:
    css = css.replace(":root{", ":host{", 1)
    css = re.sub(r"(^|\})html\{[^}]*\}", r"\1", css, count=1)
    css, n = re.subn(r"(^|\})body\{", r"\1.ys-page{", css, count=1)
    assert n == 1, "styles.css 找不到 body{"
    css = css.replace(".menu-open .main-nav", ".ys-page.menu-open .main-nav")
    return css + EXTRA_CSS


def build(assets_base: str, media: dict, layout: str) -> str:
    body = strip_review_attrs((ROOT / "_src" / "index.html").read_text(encoding="utf-8")).strip()
    if layout == "site":
        body, n = re.subn(r'<header class="site-header".*?</header>\n?', "", body, count=1, flags=re.S)
        assert n == 1, "_src/index.html 找不到 site-header"
        tail = MOBILE_CTA
    else:
        tail = FOOTER + "\n" + MOBILE_CTA
    body += "\n" + tail.format(assets="../assets/", line=LINE_URL)

    def img(m):
        name = m.group(1)
        return media.get(name) or (assets_base + name)
    body = re.sub(r"\.\./assets/([\w.-]+)", img, body)
    left = re.findall(r"\.\./assets/", body)
    assert not left, "有圖片沒換到網址"

    css = shadow_css((ROOT / "styles.css").read_text(encoding="utf-8"))
    if layout == "canvas":
        css += CANVAS_CSS
    for needle in ("</template>", "</style>", "</script>"):
        assert needle not in css and needle not in body, f"內容裡有 {needle}，會提前關閉 template"
    assert body.count(f'href="{LINE_URL}"') == 5, "LINE 按鈕應該是 5 顆（內容 4＋手機底部 1）"

    return (
        "<!-- 羽試・免費先修班銷售頁（D&J 製作，原始檔：rhk9003/vegelady-course-preview 的 _src＋_build/build_wp.py）。\n"
        "     整段貼進 Elementor「HTML」小工具；頁面範本：" + ("Elementor 全寬（保留官網頁首頁尾）" if layout == "site" else "Elementor Canvas") + "。\n"
        "     轉換：Pixel Cat 的 free-course（URL 觸發 " + LINE_URL + "）綁在下面的隱藏連結上，改 LINE 網址要兩邊一起改。 -->\n"
        f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link rel="stylesheet" href="{FONTS.replace("&", "&amp;")}">\n'
        # 手機底部按鈕固定在畫面下緣，官網頁尾最後一段要讓出位置
        + ('<style>@media(max-width:800px){body{padding-bottom:64px}}</style>\n' if layout == "site" else "")
        +
        f'<div id="ys-free-course"><a id="ys-free-course-line" href="{LINE_URL}" hidden aria-hidden="true" tabindex="-1" style="display:none"></a></div>\n'
        '<template id="ys-free-course-tpl"><style>' + css + "</style>\n"
        '<div class="ys-page">\n' + body + "\n</div></template>\n"
        + SCRIPT.replace("__LINE__", LINE_URL) + "\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets-base", default="")
    ap.add_argument("--media-map", default=str(ROOT / "_wp" / "media-map.json"))
    ap.add_argument("--out", default=str(ROOT / "_wp" / "free-course-elementor.html"))
    ap.add_argument("--layout", choices=["site", "canvas"], default="site")
    args = ap.parse_args()
    media_path = pathlib.Path(args.media_map)
    media = json.loads(media_path.read_text(encoding="utf-8")) if media_path.exists() and not args.assets_base else {}
    if not media and not args.assets_base:
        raise SystemExit("沒有 _wp/media-map.json，請用 --assets-base 指定圖片網址前綴")
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    html = build(args.assets_base, media, args.layout)
    out.write_text(html, encoding="utf-8")
    print(out, len(html.encode("utf-8")), "bytes")
    # Elementor 內容：一個滿版、無內距的容器＋一個 HTML 小工具（REST 寫 _elementor_data 用）
    pad = {"unit": "px", "top": "0", "right": "0", "bottom": "0", "left": "0", "isLinked": True}
    data = [{"id": "ys7c1a01", "elType": "container", "isInner": False,
             "settings": {"content_width": "full", "padding": pad, "margin": pad,
                          "flex_gap": {"unit": "px", "size": 0, "column": "0", "row": "0", "isLinked": True}},
             "elements": [{"id": "ys7c1a02", "elType": "widget", "widgetType": "html",
                           "settings": {"html": html}, "elements": []}]}]
    data_out = out.with_name("elementor-data.json")
    data_out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(data_out)


if __name__ == "__main__":
    main()
