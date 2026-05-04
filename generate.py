#!/usr/bin/env python3
"""
iPAS AI 中級 每日出題腳本
每天從 data/ 資料夾的考題 HTML 中隨機抽 100 題，產生 index.html
"""

import re, glob, os, random, json, sys
from datetime import date, datetime, timezone, timedelta

# 台灣時間 UTC+8
TW_TZ = timezone(timedelta(hours=8))
today = datetime.now(TW_TZ).date()
seed_date = str(today)

# 允許指定日期（測試用）
if len(sys.argv) > 1:
    seed_date = sys.argv[1]
    today = date.fromisoformat(seed_date)

print(f"Generating questions for: {today}")

# ── 題目解析 ────────────────────────────────────────────────────────
def extract_questions(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    topic = os.path.basename(filepath).replace('_exam.html', '').replace('_', ' ')

    results = []
    parts = content.split('<div class="question-card"')

    for part in parts[1:]:
        content_m = re.search(r'<div class="question-content"[^>]*>([\s\S]*?)</div>', part)
        correct_label_m = re.search(
            r'<div class="option-item correct"[\s\S]*?<div class="option-label"[^>]*>([\s\S]*?)</div>', part)
        all_opts = re.findall(
            r'<div class="option-item[^"]*"[\s\S]*?<div class="option-label"[^>]*>([\s\S]*?)</div>'
            r'[\s\S]*?<div class="option-text"[^>]*>([\s\S]*?)</div>', part)

        # 解析
        exp_text = ''
        exp_sections = part.split('explanation-content')
        if len(exp_sections) > 1:
            raw = exp_sections[1].lstrip('>')
            exp_text = re.sub(r'<[^>]+>', '', raw[:3000]).strip()
            exp_text = re.sub(r'\s+', ' ', exp_text).strip()[:700]

        if content_m and all_opts:
            q_text = re.sub(r'<[^>]+>', '', content_m.group(1)).strip()
            q_text = re.sub(r'\s+', ' ', q_text).strip()

            correct_ans = '？'
            if correct_label_m:
                correct_ans = re.sub(r'<[^>]+>', '', correct_label_m.group(1)).strip()

            opts_clean = []
            for a, b in all_opts:
                label = re.sub(r'<[^>]+>', '', a).strip()
                text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', b)).strip()
                opts_clean.append([label, text])

            results.append({
                'topic': topic,
                'question': q_text,
                'options': opts_clean,
                'answer': correct_ans,
                'explanation': exp_text,
            })

    return results


data_dir = os.path.join(os.path.dirname(__file__), 'data')
all_files = sorted(glob.glob(os.path.join(data_dir, '*.html')))
print(f"Found {len(all_files)} exam files")

all_questions = []
for fp in all_files:
    qs = extract_questions(fp)
    all_questions.extend(qs)

print(f"Total questions pool: {len(all_questions)}")

# ── 抽題（依日期 seed，同一天重跑結果相同）────────────────────────
random.seed(seed_date)
selected = random.sample(all_questions, min(100, len(all_questions)))

# ── 產生 HTML ──────────────────────────────────────────────────────
weekday_zh = ['一','二','三','四','五','六','日']
weekday = weekday_zh[today.weekday()]
date_str = f"{today.year} 年 {today.month} 月 {today.day} 日（星期{weekday}）"

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>iPAS AI 中級 每日練習 {today}</title>
<style>
  :root {{
    --blue: #1a73e8;
    --green: #2e7d32;
    --bg: #f0f4f8;
    --card: #ffffff;
    --tag-bg: #e3f0ff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Microsoft JhengHei", "PingFang TC", Arial, sans-serif;
         background: var(--bg); color: #1a1a1a; padding: 16px; }}
  .container {{ max-width: 860px; margin: 0 auto; }}

  /* Header */
  .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #1a73e8 100%);
             color: #fff; padding: 28px 24px; border-radius: 14px;
             text-align: center; margin-bottom: 24px; }}
  .header h1 {{ font-size: 1.7rem; margin-bottom: 6px; }}
  .header p  {{ opacity: .85; font-size: .95rem; }}

  /* Controls */
  .controls {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .btn {{ padding: 9px 18px; border: none; border-radius: 8px; cursor: pointer;
          font-size: .9rem; font-weight: 600; transition: opacity .2s; }}
  .btn:hover {{ opacity: .85; }}
  .btn-primary {{ background: var(--blue); color: #fff; }}
  .btn-secondary {{ background: #fff; color: var(--blue); border: 2px solid var(--blue); }}
  .progress-info {{ margin-left: auto; align-self: center; font-size: .9rem; color: #555; }}

  /* Question card */
  .q-card {{ background: var(--card); border-radius: 12px; padding: 20px 22px;
             margin-bottom: 18px; box-shadow: 0 2px 8px rgba(0,0,0,.07);
             border-left: 4px solid var(--blue); }}
  .q-meta {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .q-num  {{ font-size: .8rem; color: #888; }}
  .q-tag  {{ background: var(--tag-bg); color: var(--blue); padding: 2px 9px;
             border-radius: 20px; font-size: .75rem; font-weight: 600; }}
  .q-text {{ font-size: 1.05rem; font-weight: 700; line-height: 1.65;
             margin-bottom: 14px; }}

  /* Options */
  .options {{ display: flex; flex-direction: column; gap: 7px; }}
  .option  {{ display: flex; gap: 10px; padding: 9px 14px; border-radius: 8px;
              background: #f4f6fa; cursor: pointer; transition: background .15s;
              border: 2px solid transparent; }}
  .option:hover {{ background: #e8f0fe; }}
  .option.selected {{ border-color: var(--blue); background: #e8f0fe; }}
  .option.correct  {{ border-color: var(--green); background: #e8f5e9; }}
  .option.wrong    {{ border-color: #c62828; background: #ffebee; }}
  .opt-label {{ font-weight: 700; color: var(--blue); min-width: 22px; }}

  /* Answer */
  .answer-section {{ margin-top: 14px; padding: 14px 16px;
                     background: #f1f8e9; border-radius: 8px;
                     border-left: 3px solid var(--green); display: none; }}
  .answer-section.visible {{ display: block; }}
  .ans-title {{ font-weight: 700; color: var(--green); margin-bottom: 6px; }}
  .explanation {{ font-size: .93rem; line-height: 1.75; color: #333; }}

  /* Footer */
  .footer {{ text-align: center; color: #aaa; font-size: .8rem;
             margin-top: 28px; padding-bottom: 30px; }}

  @media (max-width: 600px) {{
    .header h1 {{ font-size: 1.3rem; }}
    .q-text {{ font-size: .97rem; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>📚 iPAS AI 中級｜每日練習</h1>
  <p>{date_str}　共 {len(selected)} 題　涵蓋 L21 AI應用規劃 ＋ L22 數據分析</p>
</div>

<div class="controls">
  <button class="btn btn-primary" onclick="toggleAll(true)">顯示所有答案</button>
  <button class="btn btn-secondary" onclick="toggleAll(false)">隱藏所有答案</button>
  <span class="progress-info" id="prog">已作答 0 / {len(selected)} 題</span>
</div>

"""

for i, q in enumerate(selected, 1):
    opts_html = ''
    for j, (label, text) in enumerate(q['options']):
        is_correct = label.strip() == q['answer'].strip()
        opts_html += f'<div class="option" data-label="{label}" data-correct="{str(is_correct).lower()}" onclick="choose(this,{i})">' \
                     f'<span class="opt-label">{label}</span><span>{text}</span></div>\n'

    html += f"""<div class="q-card" id="q{i}">
  <div class="q-meta">
    <span class="q-num">第 {i} 題</span>
    <span class="q-tag">{q['topic']}</span>
  </div>
  <div class="q-text">{q['question']}</div>
  <div class="options" id="opts{i}">
{opts_html}  </div>
  <div class="answer-section" id="ans{i}">
    <div class="ans-title">✅ 正確答案：{q['answer']}</div>
    <div class="explanation">{q['explanation']}</div>
  </div>
</div>
"""

html += f"""
<div class="footer">iPAS AI 中級每日練習 ｜ {today} ｜ 自動產生</div>
</div>

<script>
const TOTAL = {len(selected)};
let answered = new Set();

function choose(el, qn) {{
  const opts = document.getElementById('opts'+qn);
  if (opts.dataset.done) return;
  opts.dataset.done = '1';
  // Mark all options
  opts.querySelectorAll('.option').forEach(o => {{
    if (o.dataset.correct === 'true')  o.classList.add('correct');
    else if (o === el) o.classList.add('wrong');
  }});
  el.classList.add('selected');
  // Show answer
  document.getElementById('ans'+qn).classList.add('visible');
  answered.add(qn);
  document.getElementById('prog').textContent = '已作答 ' + answered.size + ' / ' + TOTAL + ' 題';
}}

function toggleAll(show) {{
  for (let i=1; i<=TOTAL; i++) {{
    let sec = document.getElementById('ans'+i);
    if (show) sec.classList.add('visible');
    else sec.classList.remove('visible');
  }}
}}
</script>
</body>
</html>"""

output = os.path.join(os.path.dirname(__file__), 'index.html')
with open(output, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Done! index.html written ({len(html):,} bytes)")
print(f"Topics covered: {len(set(q['topic'] for q in selected))}")
