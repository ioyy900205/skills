"""Skeleton for a briefing page generator. Copy, rename, and fill in.

    python <this>.py --run <运行目录> --out <页面目录>

The shape here is what the structure in SKILL.md looks like in code. Three
things are load-bearing and should survive your edits:

  1. `load()` reads the run directory; every number in the page comes from it.
     Nothing is typed twice, so a rerun can never leave the prose stale.
  2. Each section is a function taking `run`, so the narrative sits next to the
     numbers it describes and cannot drift from them.
  3. `build()` assembles and writes. Editing the page means editing this file.

Replace the MARKERS below. Delete sections you do not need - but keep the
order, because the order is what puts the conclusion first.
"""
import argparse
import json
from pathlib import Path

# Use the project's own modules if it has them; otherwise copy these two next
# to this file. Do not maintain a second copy of the design system.
from charts import CHART_CSS, CHART_JS, heat_scale, heatmap, panel
from report_html import CSS, JS, embed, escape

# MARKER: the configurations you compare with tabs (key -> display name).
VARIANTS = [('baseline', '基线'), ('treatment', '改动后')]


# --- data -------------------------------------------------------------------

def load(directory):
    """Everything the page needs, read once; fail early on missing core data."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f'run directory not found: {directory}')

    run = {'dir': directory}
    for name in ('config', 'summary'):        # MARKER: your run's files
        path = directory/f'{name}.json'
        if path.exists():
            run[name] = json.loads(path.read_text(encoding='utf-8'))

    if 'summary' not in run:
        raise FileNotFoundError(
            f'missing {directory / "summary.json"}; create a structured summary before building the report')
    if not isinstance(run['summary'], dict):
        raise ValueError('summary.json must contain a JSON object')
    return run


def variants_of(run):
    """Only the configurations this run actually produced; fail on schema drift."""
    got = [(k, n) for k, n in VARIANTS if k in run['summary']]
    if not got:
        expected = ', '.join(k for k, _ in VARIANTS)
        raise ValueError(
            f'none of the expected variants ({expected}) exist in summary.json; update VARIANTS')
    return got


def metric(run, variant, cell, key):
    """One number, or None where the condition did not run.

    Returning None rather than 0 matters: "did not run" and "scored zero" are
    different claims and the page must be able to draw them differently.
    """
    entry = run['summary'].get(variant, {}).get(cell)
    return None if entry is None else entry.get(key)


def mean(values):
    got = [v for v in values if v is not None]
    return sum(got)/len(got) if got else None


def pct(value):
    return '—' if value is None else f'{value:.0f}%'


# --- page pieces ------------------------------------------------------------

def heading(number, title, lede):
    return (f'<div class="section-head"><div class="section-no">{escape(number)}</div>'
            f'<div><h2>{escape(title)}</h2><p>{escape(lede)}</p></div></div>')


def kpi(label, value, note):
    """A KPI is a comparison, not a lone number - `note` is where that lives."""
    return (f'<div class="kpi"><span>{escape(label)}</span><strong>{escape(value)}</strong>'
            f'<span>{escape(note)}</span></div>')


def tabs(key, options, label='对比'):
    """Panels must carry data-panel-<key> and nothing named plain `data-panel`."""
    buttons = ''.join(
        f'<button class="tab" data-value="{escape(v)}" aria-pressed="false">{escape(n)}</button>'
        for v, n in options)
    return (f'<div class="tabs" data-tabs="{escape(key)}" data-scope="body">'
            f'<span class="label">{escape(label)}</span>{buttons}</div>')


def panels(run, render, key='variant'):
    """One hidden panel per configuration; `render(variant)` returns its body."""
    return ''.join(f'<div class="tabpanel" data-panel-{key}="{v}" hidden>{render(v)}</div>'
                   for v, _ in variants_of(run))


def figure_block(path, caption):
    """Inline figures; show missing evidence explicitly instead of hiding it."""
    if not Path(path).exists():
        return (f'<figure class="missing-figure">'
                f'<div class="figure-missing" role="note">未生成 / 缺失：{escape(caption)}</div>'
                f'<figcaption>{escape(caption)}</figcaption></figure>')
    return (f'<figure><img loading="lazy" src="{embed(path)}" alt="{escape(caption)}">'
            f'<figcaption>{escape(caption)}</figcaption></figure>')


def data_table(rows, columns, get, label='数据表'):
    """The numbers behind a chart, folded away under it.

    A chart is an argument; this is the evidence for it. Collapsed, it costs
    the skimming reader nothing and saves the checking reader from having to
    ask you for the numbers.
    """
    head = ''.join(f'<th>{escape(c)}</th>' for c in columns)
    body = ''
    for r, row in enumerate(rows):
        cells = ''.join(
            f'<td>{"—" if get(r, c) is None else f"{get(r, c):.1f}"}</td>'
            for c, _ in enumerate(columns))
        body += f'<tr><th scope="row">{escape(row)}</th>{cells}</tr>'
    return (f'<details><summary>{escape(label)}</summary>'
            f'<table class="data"><thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></details>')


# --- sections ---------------------------------------------------------------

def hero(run):
    """Title is the conclusion. KPIs carry the comparison. This is all the
    reader with thirty seconds will see, so it has to stand alone."""
    lead = variants_of(run)[0][0]
    headline = mean([metric(run, lead, c, 'score')
                     for c in run['summary'].get(lead, {})])
    return f'''<section class="hero" id="top">
<p class="eyebrow">MARKER: 一行副题</p>
<h1>MARKER：把结论写成标题，<br>不要写成主题</h1>
<p class="lede">MARKER：两三句说清做了什么、变量是什么、
其余条件怎么钉死的，以及最反直觉的那个发现。</p>
<div class="kpis">
{kpi('MARKER 指标一', pct(headline), 'MARKER：这个数字跟什么比')}
{kpi('MARKER 指标二', '—', 'MARKER：好消息')}
{kpi('MARKER 指标三', '—', 'MARKER：坏消息')}
</div>
<p class="footnote">MARKER：规模——多少条件 × 多少样本 × 多少配置，耗时，跳过了几个。</p>
</section>'''


def method_section(run):
    """Written so a reader can find fault with it. State what was held fixed
    and why, and state the constraint that stopped you going further."""
    return f'''<section id="method">
{heading('一', 'MARKER：怎么做的', 'MARKER：一句话说明这节让人检查什么。')}
<div class="grid three">
<div class="card"><h4>① MARKER</h4><p>MARKER</p></div>
<div class="card"><h4>② MARKER</h4><p>MARKER</p></div>
<div class="card"><h4>③ MARKER</h4><p>MARKER</p></div>
</div>
<div class="notice">
<h3>MARKER：把限制条件写在这里</h3>
<p>MARKER：为什么某个方向推不下去，以及那是不是被测对象的边界。</p>
</div>
</section>'''


def results_section(run):
    """Figure, then what to see in it. The list is the point; at least one
    item should be a caveat or something that cuts against the story."""
    body = heading('二', 'MARKER：主结果', 'MARKER：自变量是什么。')
    body += tabs('variant', variants_of(run))
    # MARKER: rows/columns/cells of your condition grid.
    rows, columns = ['条件 A', '条件 B'], ['档 1', '档 2', '档 3']

    def grid(variant):
        cells = {}
        for r, _ in enumerate(rows):
            for c, _ in enumerate(columns):
                value = metric(run, variant, f'{r}_{c}', 'score')   # MARKER
                cells[(r, c)] = {'value': value, 'tip': f'MARKER {value}'}
        return (heat_scale(0, 100, '%')
                +heatmap(rows, columns, cells, row_label='MARKER', column_label='MARKER')
                # The numbers behind the colours, one fold away.
                +data_table(rows, columns,
                            lambda r, c: metric(run, variant, f'{r}_{c}', 'score')))
    body += f'<div class="card">{panels(run, grid)}</div>'
    body += '''<h3>这张图说了什么</h3>
<ul>
<li><strong>MARKER 发现一。</strong>MARKER，数字从上面读回来。</li>
<li><strong>MARKER 发现二。</strong>MARKER。</li>
<li><strong>MARKER 限定或反直觉的一条。</strong>MARKER。</li>
</ul>'''
    series = [{'name': n, 'slot': i,
               'values': [metric(run, v, c, 'score') for c in ['0_0', '0_1', '0_2']]}
              for i, (v, n) in enumerate(variants_of(run))]     # MARKER
    body += ('<div class="chart-grid">'
             +panel('MARKER 趋势', series, columns, note='MARKER')+'</div>')
    return f'<section id="results">{body}</section>'


def evidence_section(run):
    """Every condition, including the ones that failed. A gallery of the wins
    would make the result read stronger than it is."""
    body = heading('三', '全部条件', '每一个条件都在，包括没成功的。')
    body += tabs('fig', variants_of(run), label='配置')
    body += panels(run, lambda v: figure_block(run['dir']/f'grid_{v}.png',
                                               f'MARKER：{dict(VARIANTS)[v]} 全条件'),
                   key='fig')
    body += '<h3>判据</h3><p>MARKER：怎么算一次成功，为什么这么算。</p>'
    return f'<section id="evidence">{body}</section>'


def boundary_section(run):
    """Without this the table gets read backwards - a limit of the input gets
    remembered as a flaw in the thing being measured, or vice versa."""
    return f'''<section id="boundary">
{heading('四', '哪些失败是原理性的，哪些是能改的', '这一节必须读，否则上面的表会被读反。')}
<div class="notice">
<h3>MARKER：这一档衡量的不是被测对象</h3>
<p>MARKER：说明该条件下输入里已经没有区分信息了，因此那里的失败是极限而非不足。</p>
</div>
<h3>真正的边界</h3>
<ul>
<li><strong>MARKER。</strong>信息充足却失败了，这是该跟进的。</li>
<li><strong>MARKER。</strong></li>
</ul>
</section>'''


def validity_section(run):
    """In-page and at normal size. A limitation the reader discovers on their
    own costs more credibility than the same limitation stated up front."""
    return f'''<section id="validity">
{heading('五', '口径与限制', '这些是读这一页时必须知道的边界。')}
<ul>
<li><strong>MARKER。</strong></li>
<li><strong>MARKER：这页答不了的问题。</strong></li>
</ul>
<h3>复现</h3>
<pre><code>MARKER: 完整命令</code></pre>
<p class="footnote">MARKER：配置/数据/权重哈希。</p>
</section>'''


# --- assembly ---------------------------------------------------------------

def build(run, out):
    links = [('method', '怎么做的'), ('results', '主结果'), ('evidence', '全部条件'),
             ('boundary', '边界'), ('validity', '口径')]
    nav = ''.join(f'<a href="#{k}">{escape(v)}</a>' for k, v in links)
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MARKER：页面标题</title>
<style>{CSS}{CHART_CSS}</style></head>
<body class="viz-root">
<header><div class="nav"><div class="brand"><span class="mark">MARKER</span>
MARKER 短标题</div><nav class="navlinks">{nav}</nav>
<button class="theme-toggle" data-theme-toggle type="button">☾ 深色</button></div></header>
<main>
{hero(run)}
{method_section(run)}
{results_section(run)}
{evidence_section(run)}
{boundary_section(run)}
{validity_section(run)}
</main>
<footer>本页由 <code>MARKER 脚本路径</code> 从运行目录生成，数字与图均为读回，不手写。</footer>
<script>{JS}{CHART_JS}</script>
</body></html>'''
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out/'index.html').write_text(page, encoding='utf-8')
    return out/'index.html'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    path = build(load(args.run), args.out)
    print(f'Wrote {path} ({path.stat().st_size/1e6:.1f} MB)')


if __name__ == '__main__':
    main()
