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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>微信读书划线卡片</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color: transparent; }

html, body {
  min-height: 100%;
  font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", serif;
  background: #faf9f7;
  color: #2c2c2e;
  -webkit-font-smoothing: antialiased;
  overscroll-behavior-x: none;
}

body {
  /* 允许整个页面自然滚动，避免 flexbox 内部滚动失效 */
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

:root {
  --bg: #faf9f7;
  --card-bg: #ffffff;
  --text: #2c2c2e;
  --text-secondary: #8e8e93;
  --accent: #6c63ff;
  --accent-light: #8b83ff;
  --border: #e5e5ea;
  --shadow: 0 12px 40px rgba(108, 99, 255, 0.08), 0 4px 12px rgba(0,0,0,0.04);
}

/* ============ 顶部控制栏 ============ */
.header {
  position: sticky; top: 0; z-index: 10;
  background: rgba(250,249,247,0.95);
  border-bottom: 1px solid var(--border);
  padding: 10px 16px 12px;
  transition: all 0.3s ease;
  overflow: hidden;
  max-height: 220px;
}
.header.collapsed {
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border-bottom: none;
  opacity: 0;
}
.header h1 {
  font-size:16px; font-weight:600; margin-bottom:10px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  letter-spacing: 0.5px;
  display: flex; align-items: center; justify-content: space-between;
}
.header h1 .toggle-btn {
  font-size: 13px; font-weight: 400;
  color: var(--accent); cursor: pointer;
  background: none; border: none;
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.controls { display:flex; gap:8px; align-items:center; }
.controls input[type=text] {
  flex:1; padding:9px 14px; font-size:14px;
  border:1px solid var(--border); border-radius:12px;
  background:var(--card-bg); outline:none;
  font-family: -apple-system, "PingFang SC", sans-serif;
  min-width: 0;
}
.controls select {
  padding:9px 12px; font-size:13px; max-width:42%;
  border:1px solid var(--border); border-radius:12px;
  background:var(--card-bg); color:var(--text);
  font-family: -apple-system, "PingFang SC", sans-serif;
  flex-shrink: 0;
}

/* ============ 卡片舞台 ============ */
.stage {
  min-height: calc(100vh - 200px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 12px 12px 16px;
}

.card {
  width: 100%;
  max-width: 580px;
  min-height: calc(100vh - 240px);
  background: var(--card-bg);
  border-radius: 24px;
  box-shadow: var(--shadow);
  padding: 40px 24px 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  transition: transform 0.15s ease, opacity 0.2s ease;
}
.card:active { transform: scale(0.98); }

.card-book {
  font-size: 13px; color: var(--accent);
  font-weight: 500;
  font-family: -apple-system, "PingFang SC", sans-serif;
  margin-bottom: 18px;
  width: 100%;
}

.card-text {
  font-size: clamp(16px, 4.2vw, 24px);
  line-height: 1.75;
  color: var(--text);
  font-weight: 400;
  width: 100%;
  letter-spacing: 0.3px;
  padding: 0 4px;
  word-break: break-word;
}

.card-chapter {
  font-size: 12px; color: var(--text-secondary);
  font-family: -apple-system, "PingFang SC", sans-serif;
  margin-top: 18px;
  width: 100%;
}

.card-hint {
  font-size: 10px; color: #d1d1d6;
  font-family: -apple-system, sans-serif;
  letter-spacing: 1px;
  margin-top: 12px;
}

.empty {
  text-align:center; color:var(--text-secondary); font-size:15px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  padding: 40px;
}

/* ============ 左右翻页按钮 ============ */
.nav-btns {
  position: sticky; bottom: env(safe-area-inset-bottom, 0px); z-index: 9;
  display: flex;
  justify-content: space-between;
  padding: 8px 12px 12px;
  gap: 12px;
  background: linear-gradient(to top, rgba(250,249,247,1) 0%, rgba(250,249,247,0.92) 70%, rgba(250,249,247,0) 100%);
}
.nav-btn {
  flex: 1;
  padding: 11px 0;
  border: none;
  border-radius: 14px;
  background: var(--card-bg);
  color: var(--accent);
  font-size: 15px;
  font-weight: 500;
  font-family: -apple-system, "PingFang SC", sans-serif;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.nav-btn:active { transform: scale(0.95); background: var(--accent); color: white; }

/* ============ 进度条 ============ */
.progress {
  position: sticky; bottom: 0; z-index: 8;
  height: 3px; background: rgba(0,0,0,0.04);
}
.progress-bar {
  height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-light));
  width: 0%; transition: width 0.3s ease;
  border-radius: 0 3px 3px 0;
}

/* ============ 底部跳转栏 ============ */
.jump-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center; gap: 6px;
  padding: 10px 16px 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  background: rgba(250,249,247,0.95);
  border-top: 1px solid var(--border);
  font-size: 13px; color: var(--text-secondary);
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.jump-bar #progressText {
  color: var(--accent); font-weight: 600;
  min-width: 90px; text-align: center;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}
.jump-label { font-size: 11px; }
.jump-bar input[type=number] {
  width: 56px; padding: 5px 8px; font-size: 14px;
  border: 1px solid var(--border); border-radius: 10px;
  text-align: center; outline: none;
  background: var(--card-bg);
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.jump-hint { font-size: 11px; }
.jump-bar button {
  padding: 5px 12px; font-size: 13px;
  border: none; border-radius: 10px;
  background: var(--accent); color: white;
  cursor: pointer; font-weight: 500;
}
.jump-bar button:active { background: var(--accent-light); }
</style>
</head>
<body>

<!-- 顶部控制栏 -->
<div class="header" id="header">
  <h1>
    <span>📚 划线卡片</span>
    <button class="toggle-btn" id="toggleHeader">收起 ▲</button>
  </h1>
  <div class="controls">
    <input type="text" id="search" placeholder="搜索划线内容...">
    <select id="bookFilter">
      <option value="">全部书籍</option>
      __BOOKS_OPTIONS__
    </select>
  </div>
</div>

<!-- 卡片区域 -->
<div class="stage" id="stage">
  <div class="card" id="card" style="display:none;">
    <div class="card-book" id="cardBook"></div>
    <div class="card-text" id="cardText"></div>
    <div class="card-chapter" id="cardChapter"></div>
    <div class="card-hint">点击卡片右半部分或下方按钮切换下一张</div>
  </div>
  <div class="empty" id="empty">加载中...</div>
</div>

<!-- 左右按钮 -->
<div class="nav-btns">
  <button class="nav-btn" id="prevBtn">‹ 上一张</button>
  <button class="nav-btn" id="nextBtn">下一张 ›</button>
</div>

<!-- 进度条 -->
<div class="progress"><div class="progress-bar" id="progressBar"></div></div>

<!-- 底部跳转栏 -->
<div class="jump-bar">
  <span id="progressText">0 / 0</span>
  <span class="jump-label">跳转</span>
  <input type="number" id="jumpInput" min="1" placeholder="页" inputmode="numeric">
  <span class="jump-hint">/ <span id="totalNum">0</span></span>
  <button id="jumpBtn">Go</button>
</div>

<script>
const ALL_CARDS = __CARDS_JSON__;
let shuffled = [];
let index = 0;
let round = 1;

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

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function cleanBookName(book) {
  if (!book) return '未知书名';
  if (book.indexOf('_') !== -1) return book.split('_').slice(1).join('_');
  return book;
}

function updateCards() {
  let filtered = ALL_CARDS;
  const q = searchBox.value.trim();
  const bk = bookFilter.value;
  if (bk) filtered = filtered.filter(c => c.book === bk);
  if (q) filtered = filtered.filter(c =>
    c.text.includes(q) || (c.book && c.book.includes(q))
  );
  shuffled = shuffle(filtered);
  index = 0;
  round = 1;
  render();
}

function render() {
  if (shuffled.length === 0) {
    cardEl.style.display = 'none';
    emptyEl.style.display = 'block';
    emptyEl.textContent = '没有匹配的划线';
    progressBar.style.width = '0%';
    progressText.textContent = '0 / 0';
    document.getElementById('totalNum').textContent = '0';
    return;
  }
  cardEl.style.display = 'flex';
  emptyEl.style.display = 'none';
  const c = shuffled[index];
  bookEl.innerHTML = esc(cleanBookName(c.book));
  textEl.innerHTML = esc(c.text);
  chapterEl.innerHTML = esc(c.chapter || '');
  progressBar.style.width = ((index + 1) / shuffled.length * 100) + '%';
  progressText.textContent = (index + 1) + '/' + shuffled.length + ' · 第' + round + '轮';
  document.getElementById('totalNum').textContent = shuffled.length;
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function next() {
  if (shuffled.length === 0) return;
  index++;
  if (index >= shuffled.length) {
    shuffled = shuffle(shuffled);
    index = 0;
    round++;
  }
  render();
}

function prev() {
  if (shuffled.length === 0) return;
  index--;
  if (index < 0) {
    round = Math.max(1, round - 1);
    index = shuffled.length - 1;
  }
  render();
}

// 点击切换
cardEl.addEventListener('click', function(e) {
  const rect = cardEl.getBoundingClientRect();
  const x = e.clientX - rect.left;
  if (x < rect.width * 0.35) prev();
  else next();
});

// 按钮切换
document.getElementById('prevBtn').addEventListener('click', function(e) {
  e.stopPropagation();
  prev();
});
document.getElementById('nextBtn').addEventListener('click', function(e) {
  e.stopPropagation();
  next();
});

// 滑动切换（轻触滑动，不阻止默认滚动）
let touchStartX = 0, touchStartY = 0, touchStartTime = 0, isSwiping = false;
const stage = document.getElementById('stage');

stage.addEventListener('touchstart', function(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'BUTTON') return;
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
  touchStartTime = Date.now();
  isSwiping = true;
}, {passive: true});

stage.addEventListener('touchend', function(e) {
  if (!isSwiping) return;
  isSwiping = false;
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  const dt = Date.now() - touchStartTime;
  // 明显水平滑动才翻页
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5 && dt < 600) {
    if (dx > 0) prev();
    else next();
  }
}, {passive: true});

// 键盘切换
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'ArrowDown') {
    e.preventDefault(); next();
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault(); prev();
  }
});

// ============ 防止系统返回手势退出页面 ============
function pushHistoryGuard() {
  try { history.pushState({guard: true, idx: Date.now()}, ''); } catch(e) {}
}
// 连续 push 多条，让返回手势留在本页
pushHistoryGuard();
pushHistoryGuard();
pushHistoryGuard();

window.addEventListener('popstate', function(e) {
  pushHistoryGuard();
  pushHistoryGuard();
  pushHistoryGuard();
  prev(); // 返回手势切换上一张卡片
});

// 顶部控制栏折叠
const toggleBtn = document.getElementById('toggleHeader');
toggleBtn.addEventListener('click', function(e) {
  e.stopPropagation();
  if (header.classList.contains('collapsed')) {
    header.classList.remove('collapsed');
    toggleBtn.textContent = '收起 ▲';
  } else {
    header.classList.add('collapsed');
    toggleBtn.textContent = '展开 ▼';
  }
});

// 跳转功能
const jumpInput = document.getElementById('jumpInput');
const jumpBtn = document.getElementById('jumpBtn');
function doJump() {
  const n = parseInt(jumpInput.value);
  if (isNaN(n) || n < 1 || n > shuffled.length) return;
  index = n - 1;
  render();
  jumpInput.value = '';
  jumpInput.blur();
}
jumpBtn.addEventListener('click', function(e) { e.stopPropagation(); doJump(); });
jumpInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') { e.preventDefault(); doJump(); }
  e.stopPropagation();
});
jumpInput.addEventListener('click', function(e) { e.stopPropagation(); });
searchBox.addEventListener('click', function(e) { e.stopPropagation(); });
bookFilter.addEventListener('click', function(e) { e.stopPropagation(); });

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
