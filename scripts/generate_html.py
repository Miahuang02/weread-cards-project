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
  --bg: #faf9f7;
  --card-bg: #ffffff;
  --text: #2c2c2e;
  --text-secondary: #8e8e93;
  --accent: #6c63ff;
  --accent-light: #8b83ff;
  --border: #e5e5ea;
  --shadow: 0 12px 40px rgba(108, 99, 255, 0.08), 0 4px 12px rgba(0,0,0,0.04);
}
body {
  font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", serif;
  background: var(--bg);
  color: var(--text);
  -webkit-tap-highlight-color: transparent;
  touch-action: none; /* 防止浏览器默认滑动返回/前进 */
  overscroll-behavior: none;
  -webkit-font-smoothing: antialiased;
}
/* 顶部控制栏 */
.header {
  position: fixed; top:0; left:0; right:0; z-index:10;
  background: rgba(250,249,247,0.88);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--border);
  padding: 12px 16px 10px;
  transform: translateY(0);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
}
.header.hidden { transform: translateY(-100%); }
.header h1 {
  font-size:17px; font-weight:600; margin-bottom:10px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  letter-spacing: 0.5px;
}
.controls { display:flex; gap:8px; align-items:center; }
.controls input[type=text] {
  flex:1; padding:9px 14px; font-size:14px;
  border:1px solid var(--border); border-radius:12px;
  background:var(--card-bg); outline:none;
  font-family: -apple-system, "PingFang SC", sans-serif;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.controls input[type=text]:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(108,99,255,0.1);
}
.controls select {
  padding:9px 12px; font-size:13px; max-width:45%;
  border:1px solid var(--border); border-radius:12px;
  background:var(--card-bg); color:var(--text);
  font-family: -apple-system, "PingFang SC", sans-serif;
}
/* 全屏卡片容器 */
.stage {
  position: fixed; top:0; left:0; width:100%; height:100%;
  display: flex; align-items: center; justify-content: center;
  padding: 90px 16px 100px;
}
.card {
  width: 100%; max-width: 600px;
  height: auto; max-height: 100%;
  min-height: 50vh;
  background: var(--card-bg);
  border-radius: 28px;
  box-shadow: var(--shadow);
  padding: 48px 28px 60px;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  transition: transform 0.15s ease, opacity 0.2s ease;
  overflow: hidden;
}
.card:active { transform: scale(0.97); }
.card.fade-out { opacity: 0; transform: scale(0.95); }
.card-text {
  font-size: clamp(17px, 4.8vw, 26px);
  line-height: 1.7;
  color: var(--text);
  font-weight: 400;
  width: 100%;
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  letter-spacing: 0.5px;
  padding: 10px 0;
}
.card-text::-webkit-scrollbar { width: 3px; }
.card-text::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
.card-book {
  position: absolute; top: 24px; left: 0; right: 0;
  font-size: 13px; color: var(--accent);
  font-weight: 500; padding: 0 24px;
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.card-chapter {
  position: absolute; bottom: 24px; left: 0; right: 0;
  font-size: 12px; color: var(--text-secondary);
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.card-hint {
  position: absolute; bottom: 50px; left: 0; right: 0;
  font-size: 10px; color: #d1d1d6;
  font-family: -apple-system, sans-serif;
  letter-spacing: 1px;
}
.empty {
  text-align:center; color:var(--text-secondary); font-size:15px;
  font-family: -apple-system, "PingFang SC", sans-serif;
}
/* 底部进度条 */
.progress {
  position: fixed; bottom:0; left:0; right:0; z-index:9;
  height: 3px; background: rgba(0,0,0,0.04);
}
.progress-bar {
  height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-light));
  width: 0%; transition: width 0.3s ease;
  border-radius: 0 3px 3px 0;
}
.jump-bar {
  position: fixed; bottom: 0; left: 0; right: 0; z-index:10;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 16px;
  padding-bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  background: rgba(250,249,247,0.92);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-top: 1px solid var(--border);
  font-size: 13px; color: var(--text-secondary);
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.jump-bar #progressText {
  color: var(--accent); font-weight: 600;
  min-width: 100px; text-align: center;
  font-variant-numeric: tabular-nums;
}
.jump-label { font-size: 12px; }
.jump-bar input[type=number] {
  width: 64px; padding: 5px 8px; font-size: 14px;
  border: 1px solid var(--border); border-radius: 10px;
  text-align: center; outline: none;
  background: var(--card-bg);
  font-family: -apple-system, "PingFang SC", sans-serif;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.jump-bar input[type=number]:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(108,99,255,0.1);
}
.jump-hint { font-size: 12px; }
.jump-bar button {
  padding: 5px 14px; font-size: 13px;
  border: none; border-radius: 10px;
  background: var(--accent); color: white;
  cursor: pointer; font-weight: 500;
  transition: background 0.2s;
}
.jump-bar button:active { background: var(--accent-light); }
/* 顶部切换按钮 */
.top-btns {
  position: fixed; top: 12px; right: 16px; z-index:11;
  display: flex; gap: 8px;
}
.top-btns button {
  width: 36px; height: 36px; border-radius: 50%;
  border: none; background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  font-size: 16px; color: var(--text-secondary);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: transform 0.15s;
}
.top-btns button:active { transform: scale(0.9); }
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
    <div class="card-hint">点击切换下一张 · 左滑右滑翻看 · 随机顺序</div>
  </div>
  <div class="empty" id="empty">加载中...</div>
</div>

<div class="progress" id="progress"><div class="progress-bar" id="progressBar"></div></div>
<div class="jump-bar">
  <span id="progressText">0 / 0</span>
  <span class="jump-label">跳转:</span>
  <input type="number" id="jumpInput" min="1" placeholder="页码" inputmode="numeric">
  <span class="jump-hint">/ <span id="totalNum">0</span></span>
  <button id="jumpBtn">Go</button>
</div>

<script>
const ALL_CARDS = __CARDS_JSON__;
let shuffled = [];   // 当前轮次的随机顺序
let index = 0;       // 当前在 shuffled 中的位置
let round = 1;       // 当前是第几轮

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

// Fisher-Yates 洗牌算法
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
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
    return;
  }
  cardEl.style.display = 'flex';
  emptyEl.style.display = 'none';
  const c = shuffled[index];
  bookEl.innerHTML = esc(c.book);
  textEl.innerHTML = esc(c.text);
  chapterEl.innerHTML = esc(c.chapter || '');
  progressBar.style.width = ((index + 1) / shuffled.length * 100) + '%';
  progressText.textContent = (index + 1) + ' / ' + shuffled.length + ' · 第' + round + '轮';
  document.getElementById('totalNum').textContent = shuffled.length;
}

function next() {
  if (shuffled.length === 0) return;
  index++;
  // 看完一轮，重新洗牌开始新一轮
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
  // 回到上一轮的最后一张
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

// 滑动切换（监听整个页面，防止浏览器默认返回）
let touchStartX = 0;
let touchStartY = 0;
let touchStartTime = 0;
let isTouching = false;

document.addEventListener('touchstart', function(e) {
  // 跳过输入框上的滑动
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
  touchStartTime = Date.now();
  isTouching = true;
}, {passive: false});

document.addEventListener('touchmove', function(e) {
  if (!isTouching) return;
  const dx = e.touches[0].clientX - touchStartX;
  const dy = e.touches[0].clientY - touchStartY;
  // 水平滑动时阻止默认行为（防止浏览器返回/前进）
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) {
    e.preventDefault();
  }
}, {passive: false});

document.addEventListener('touchend', function(e) {
  if (!isTouching) return;
  isTouching = false;
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  const dt = Date.now() - touchStartTime;
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50 && dt < 500) {
    if (dx > 0) prev();
    else next();
  }
}, {passive: false});

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
