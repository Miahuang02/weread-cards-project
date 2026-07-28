#!/usr/bin/env python3
"""
generate_html.py
读取 highlights.json，生成手机卡片网页 index.html
交互：单张卡片占满屏幕，点击/滑动切换下一张，支持按书筛选和搜索
"""
import json
from pathlib import Path
from html import escape

DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"
OUTPUT_FILE = Path(__file__).parent.parent / "index.html"


def load_highlights():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html(highlights):
    books = {}
    for h in highlights:
        name = h.get("book", "未知")
        if name not in books:
            books[name] = 0
        books[name] += 1

    cards_json = json.dumps(highlights, ensure_ascii=False)

    books_options = "".join(
        f'<option value="{escape(name)}">{escape(name)} ({count})</option>'
        for name, count in sorted(books.items())
    )

    html = HTML_TEMPLATE.replace("__BOOKS_OPTIONS__", books_options)
    html = html.replace("__CARDS_JSON__", cards_json)
    return html


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>微信读书划线卡片</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { height: 100%; overflow: hidden; }
:root {
  --bg: #f5f5f7;
  --card-bg: #ffffff;
  --text: #1d1d1f;
  --text-secondary: #86868b;
  --accent: #0071e3;
  --border: #d2d2d7;
}
body {
  font-family: -apple-system, "PingFang SC", "Helvetica Neue", "Noto Sans CJK SC", sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-tap-highlight-color: transparent;
  touch-action: pan-y;
}
/* 顶部控制栏 */
.header {
  position: fixed; top:0; left:0; right:0; z-index:10;
  background: rgba(245,245,247,0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 10px 14px 8px;
  transform: translateY(0);
  transition: transform 0.25s ease;
}
.header.hidden { transform: translateY(-100%); }
.header h1 { font-size:16px; font-weight:600; margin-bottom:8px; }
.controls { display:flex; gap:8px; align-items:center; }
.controls input[type=text] {
  flex:1; padding:8px 12px; font-size:14px;
  border:1px solid var(--border); border-radius:10px;
  background:var(--card-bg); outline:none;
}
.controls input[type=text]:focus { border-color:var(--accent); }
.controls select {
  padding:8px 10px; font-size:14px; max-width:45%;
  border:1px solid var(--border); border-radius:10px;
  background:var(--card-bg); color:var(--text);
}
/* 全屏卡片容器 */
.stage {
  position: fixed; top:0; left:0; width:100%; height:100%;
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.card {
  width: 100%; max-width: 560px;
  height: 76vh; max-height: 720px;
  background: var(--card-bg);
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
  padding: 32px 28px;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
}
.card-text {
  font-size: clamp(18px, 5vw, 28px);
  line-height: 1.7;
  color: var(--text);
  font-weight: 400;
  width: 100%;
  overflow-y: auto;
}
.card-book {
  position: absolute; top: 20px; left: 0; right: 0;
  font-size: 13px; color: var(--accent);
  font-weight: 500; padding: 0 20px;
}
.card-chapter {
  position: absolute; bottom: 20px; left: 0; right: 0;
  font-size: 12px; color: var(--text-secondary);
}
.card-hint {
  position: absolute; bottom: 48px; left: 0; right: 0;
  font-size: 11px; color: #bbb;
}
.empty {
  text-align:center; color:var(--text-secondary); font-size:15px;
}
/* 底部进度条 */
.progress {
  position: fixed; bottom:0; left:0; right:0; z-index:10;
  height: 4px; background: rgba(0,0,0,0.06);
}
.progress-bar {
  height: 100%; background: var(--accent);
  width: 0%; transition: width 0.2s;
}
.progress-text {
  position: fixed; bottom: 10px; right: 14px; z-index:10;
  font-size: 12px; color: var(--text-secondary);
  background: rgba(255,255,255,0.8); padding: 2px 8px;
  border-radius: 10px;
}
/* 顶部切换按钮 */
.top-btns {
  position: fixed; top: 10px; right: 14px; z-index:11;
  display: flex; gap: 8px;
}
.top-btns button {
  width: 34px; height: 34px; border-radius: 50%;
  border: none; background: rgba(255,255,255,0.85);
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  font-size: 16px; color: var(--text-secondary);
  display: flex; align-items: center; justify-content: center;
}
</style>
</head>
<body>
<div class="header" id="header">
  <h1>📚 划线卡片</h1>
  <div class="controls">
    <input type="text" id="search" placeholder="搜索划线内容...">
    <select id="bookFilter">
      <option value="">全部书籍</option>
      __BOOKS_OPTIONS__
    </select>
  </div>
</div>

<div class="top-btns">
  <button id="toggleHeader" title="显示/隐藏控制栏">⚙️</button>
</div>

<div class="stage" id="stage">
  <div class="card" id="card" style="display:none;">
    <div class="card-book" id="cardBook"></div>
    <div class="card-text" id="cardText"></div>
    <div class="card-chapter" id="cardChapter"></div>
    <div class="card-hint">点击切换下一张 · 左滑上一张 · 右滑下一张</div>
  </div>
  <div class="empty" id="empty">加载中...</div>
</div>

<div class="progress" id="progress"><div class="progress-bar" id="progressBar"></div></div>
<div class="progress-text" id="progressText">0 / 0</div>

<script>
const ALL_CARDS = __CARDS_JSON__;
let cards = ALL_CARDS.slice();
let index = 0;

const header = document.getElementById('header');
const cardEl = document.getElementById('card');
const emptyEl = document.getElementById('empty');
const bookEl = document.getElementById('cardBook');
const textEl = document.getElementById('cardText');
const chapterEl = document.getElementById('cardChapter');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const searchBox = document.getElementById('search');
const bookFilter = document.getElementById('bookFilter');

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function updateCards() {
  let filtered = ALL_CARDS;
  const q = searchBox.value.trim();
  const bk = bookFilter.value;
  if (bk) filtered = filtered.filter(c => c.book === bk);
  if (q) filtered = filtered.filter(c =>
    c.text.includes(q) || (c.book && c.book.includes(q))
  );
  cards = filtered;
  index = 0;
  render();
}

function render() {
  if (cards.length === 0) {
    cardEl.style.display = 'none';
    emptyEl.style.display = 'block';
    emptyEl.textContent = '没有匹配的划线';
    progressBar.style.width = '0%';
    progressText.textContent = '0 / 0';
    return;
  }
  cardEl.style.display = 'flex';
  emptyEl.style.display = 'none';
  const c = cards[index];
  bookEl.innerHTML = esc(c.book);
  textEl.innerHTML = esc(c.text);
  chapterEl.innerHTML = esc(c.chapter || '');
  progressBar.style.width = ((index + 1) / cards.length * 100) + '%';
  progressText.textContent = (index + 1) + ' / ' + cards.length;
}

function next() {
  if (cards.length === 0) return;
  index = (index + 1) % cards.length;
  render();
}

function prev() {
  if (cards.length === 0) return;
  index = (index - 1 + cards.length) % cards.length;
  render();
}

// 点击切换
cardEl.addEventListener('click', function(e) {
  // 点击右侧下一张，左侧上一张，中间也可下一张
  const rect = cardEl.getBoundingClientRect();
  const x = e.clientX - rect.left;
  if (x < rect.width * 0.35) prev();
  else next();
});

// 滑动切换
let touchStartX = 0;
let touchStartY = 0;
cardEl.addEventListener('touchstart', function(e) {
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
}, {passive: true});

cardEl.addEventListener('touchend', function(e) {
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 40) {
    if (dx > 0) prev();
    else next();
  }
}, {passive: true});

// 键盘切换
document.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'ArrowDown') {
    e.preventDefault(); next();
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault(); prev();
  }
});

// 顶部控制栏显隐
document.getElementById('toggleHeader').addEventListener('click', function(e) {
  e.stopPropagation();
  header.classList.toggle('hidden');
});

searchBox.addEventListener('input', updateCards);
bookFilter.addEventListener('change', updateCards);

updateCards();
</script>
</body>
</html>"""


def main():
    highlights = load_highlights()
    html = generate_html(highlights)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"已生成卡片网页: {OUTPUT_FILE}")
    print(f"共 {len(highlights)} 条划线")


if __name__ == "__main__":
    main()
