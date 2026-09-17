"""Inline SVG charts for the self-contained report pages.

The pages have to survive being emailed as one file, so there is no chart
library and no network: every mark is SVG written here. Colours come from the
validated categorical palette, addressed by CSS variable so the page's dark
mode restyles the charts without a second set of hexes.

Conventions follow the project's chart rules: 2px lines, markers large enough
to hit, recessive axes, a legend whenever there is more than one series, the
last point of each series labelled directly, and a hover layer. Values are also
always available as a table next to the chart, which is what makes the low
contrast of some palette slots acceptable.
"""
SERIES_VARS = ['--series-1', '--series-2', '--series-3']
SERIES_LIGHT = ['#2a78d6', '#eb6834', '#1baf7a']
SERIES_DARK = ['#3987e5', '#d95926', '#199e70']


def escape(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def line_chart(series, x_labels, caption='', y_label='%', width=470, height=250,
               y_max=100, y_ticks=(0, 25, 50, 75, 100), value_format='{:.0f}'):
    """One panel: shared x categories, one polyline per series, points hoverable.

    `series` is a list of {'name', 'slot', 'values'} where `values` may hold
    None for a condition that did not run - the line breaks there rather than
    inventing a point.
    """
    left, right, top, bottom = 44, 62, 16, 34
    plot_w, plot_h = width-left-right, height-top-bottom
    step = plot_w/max(len(x_labels)-1, 1)

    def x_of(i):
        return left+i*step

    def y_of(v):
        return top+plot_h*(1-v/y_max)

    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{escape(caption)}">']
    taken = []          # y positions already used by a direct label
    for tick in y_ticks:
        y = y_of(tick)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" '
                     f'y2="{y:.1f}"/>')
        parts.append(f'<text class="axis" x="{left-8}" y="{y+4:.1f}" text-anchor="end">'
                     f'{tick}</text>')
    for i, label in enumerate(x_labels):
        parts.append(f'<text class="axis" x="{x_of(i):.1f}" y="{top+plot_h+20}" '
                     f'text-anchor="middle">{escape(label)}</text>')
    for index, entry in enumerate(series):
        slot = entry.get('slot', index)
        colour = f'var({SERIES_VARS[slot % len(SERIES_VARS)]})'
        runs, current = [], []
        for i, value in enumerate(entry['values']):
            if value is None:
                if len(current) > 1:
                    runs.append(current)
                current = []
            else:
                current.append((i, value))
        if len(current) > 1:
            runs.append(current)
        for run in runs:
            points = ' '.join(f'{x_of(i):.1f},{y_of(v):.1f}' for i, v in run)
            parts.append(f'<polyline class="series" points="{points}" stroke="{colour}"/>')
        last = None
        for i, value in enumerate(entry['values']):
            if value is None:
                continue
            last = (i, value)
            tip = (f"{entry['name']} · {x_labels[i]} · "
                   f"{value_format.format(value)}{y_label}")
            parts.append(f'<circle class="dot" cx="{x_of(i):.1f}" cy="{y_of(value):.1f}" '
                         f'r="4.5" fill="{colour}" data-tip="{escape(tip)}"/>')
        if last:
            # Series that end at the same value would stack their labels on top
            # of each other, which is exactly where the interesting ties are.
            # Nudge to the nearest free slot that is still inside the plot, so
            # a displaced label never lands on the x axis.
            base = y_of(last[1])+4
            y = next((base+d for d in (0, -13, 13, -26, 26, -39, 39)
                      if top+8 <= base+d <= top+plot_h
                      and not any(abs(base+d-used) < 12 for used in taken)), base)
            taken.append(y)
            parts.append(f'<text class="point-label" x="{x_of(last[0])+9:.1f}" '
                         f'y="{y:.1f}" fill="{colour}">'
                         f'{escape(value_format.format(last[1])+y_label)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


SEQ_STEPS = 7
# One hue, light to dark, from the validated sequential ramp. Dark mode is
# stepped for the dark surface rather than flipped: in both modes a higher
# value stands further from the page, so "stronger colour means larger" holds
# either way. Ink per step is whichever of the two text colours measured over
# 4.5:1 on it - none of these fourteen pairs is left to judgement.
SEQ_LIGHT = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#5598e7', '#256abf', '#184f95', '#0d366b']
SEQ_DARK = ['#0d366b', '#184f95', '#256abf', '#3987e5', '#5598e7', '#86b6ef', '#b7d3f6']
SEQ_INK_LIGHT = ['#0b0b0b']*4+['#ffffff']*3
SEQ_INK_DARK = ['#ffffff']*3+['#0b0b0b']*4


def heat_step(value, low=0., high=100.):
    """Quantise a magnitude onto the sequential ramp, 1..SEQ_STEPS."""
    if value is None:
        return None
    span = max(high-low, 1e-9)
    index = int((value-low)/span*SEQ_STEPS)
    return min(max(index, 0), SEQ_STEPS-1)+1


def heatmap(rows, columns, cells, caption='', row_label='', column_label='',
            cell_w=88, cell_h=46, value_format='{:.0f}', unit='%', blank='—'):
    """A 2D condition grid as coloured cells, one hue by magnitude.

    `cells` maps (row_index, column_index) to a dict with 'value' and 'tip';
    a missing key is drawn as an explicitly empty cell rather than as zero,
    because "this condition could not be built" and "this condition scored
    nothing" are different statements and must not share an encoding.
    """
    left, top, right, bottom = 132, 34, 16, 30
    width = left+cell_w*len(columns)+right
    height = top+cell_h*len(rows)+bottom
    parts = [f'<svg class="heat" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{escape(caption)}">']
    for c, label in enumerate(columns):
        parts.append(f'<text class="axis" x="{left+cell_w*c+cell_w/2:.1f}" y="{top-12}" '
                     f'text-anchor="middle">{escape(label)}</text>')
    if column_label:
        parts.append(f'<text class="axis-name" x="{left+cell_w*len(columns)/2:.1f}" '
                     f'y="{height-8}" text-anchor="middle">{escape(column_label)}</text>')
    for r, label in enumerate(rows):
        parts.append(f'<text class="axis" x="{left-10}" y="{top+cell_h*r+cell_h/2+4:.1f}" '
                     f'text-anchor="end">{escape(label)}</text>')
    if row_label:
        parts.append(f'<text class="axis-name" transform="translate(14,'
                     f'{top+cell_h*len(rows)/2:.1f}) rotate(-90)" text-anchor="middle">'
                     f'{escape(row_label)}</text>')
    for r in range(len(rows)):
        for c in range(len(columns)):
            x, y = left+cell_w*c, top+cell_h*r
            entry = cells.get((r, c))
            # 2px surface gap between fills, as between any adjacent marks.
            box = (f'x="{x+1}" y="{y+1}" width="{cell_w-2}" height="{cell_h-2}" rx="4"')
            if entry is None or entry.get('value') is None:
                parts.append(f'<rect class="cell-empty" {box}/>')
                parts.append(f'<text class="cell-ink-muted" x="{x+cell_w/2:.1f}" '
                             f'y="{y+cell_h/2+4:.1f}" text-anchor="middle">{escape(blank)}</text>')
                continue
            step = heat_step(entry['value'], entry.get('low', 0.), entry.get('high', 100.))
            text = value_format.format(entry['value'])+unit
            parts.append(f'<rect class="cell" {box} fill="var(--seq-{step})" '
                         f'data-tip="{escape(entry.get("tip", text))}"/>')
            parts.append(f'<text class="cell-ink" x="{x+cell_w/2:.1f}" '
                         f'y="{y+cell_h/2+4:.1f}" text-anchor="middle" '
                         f'fill="var(--seq-ink-{step})">{escape(text)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def heat_scale(low=0, high=100, unit='%', title=''):
    """The ramp's own key; a heatmap without one is unreadable."""
    swatches = ''.join(
        f'<i style="background:var(--seq-{i})"></i>' for i in range(1, SEQ_STEPS+1))
    return (f'<div class="heat-key">{escape(title)}'
            f'<span class="heat-end">{low}{unit}</span>'
            f'<span class="heat-ramp">{swatches}</span>'
            f'<span class="heat-end">{high}{unit}</span></div>')


def legend(series):
    """Identity is never colour alone: every swatch carries its name."""
    items = []
    for index, entry in enumerate(series):
        slot = entry.get('slot', index)
        items.append(f'<span class="key"><i style="background:'
                     f'var({SERIES_VARS[slot % len(SERIES_VARS)]})"></i>'
                     f'{escape(entry["name"])}</span>')
    return f'<div class="legend">{"".join(items)}</div>'


def panel(title, series, x_labels, note='', **kwargs):
    """A titled chart with its legend; used as one cell of a small-multiple grid."""
    body = legend(series)+line_chart(series, x_labels, caption=title, **kwargs)
    tail = f'<p class="chart-note">{escape(note)}</p>' if note else ''
    return (f'<figure class="chart-card"><figcaption class="chart-title">{escape(title)}'
            f'</figcaption>{body}{tail}</figure>')


def _ramp_vars(steps, inks):
    return ''.join(f'--seq-{i}:{c};--seq-ink-{i}:{k};'
                   for i, (c, k) in enumerate(zip(steps, inks), 1))


# Every dark value, written once and emitted under two scopes below. `{s}` is
# the scope prefix. Declaring them only inside the media query would mean the
# toggle can force light but never force dark - which is the case a viewer on a
# light laptop actually hits, and the one a projector needs in reverse.
_DARK = """
{s} body{{--ink:#eef2f0;--muted:#a7b6bd;--paper:#14181a;--card:#1d2225;--line:#333c40;
--teal:#4cc0b1;--warn:#e0a86a;--warn-bg:#2b2217;--navy:#0a1418}}
{s} .viz-root{{--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;""" \
    +_ramp_vars(SEQ_DARK, SEQ_INK_DARK)+"""}}
{s} table.data thead th{{background:#252b2f}}
{s} .mark{{background:#eef2f0;color:#14181a}}
{s} header{{background:#14181af2}}
{s} code{{background:#252b2f}}
{s} figure img{{filter:brightness(.92)}}
"""


def _dark_rules():
    """Dark under both scopes: the OS setting, and an explicit toggle.

    The `:where(:not([data-theme=light]))` guard has zero specificity, so an
    explicit light stamp still beats OS-dark; `[data-theme=dark]` carries real
    specificity and so beats the default in either direction.
    """
    media = _DARK.format(s=':root:where(:not([data-theme=light]))')
    forced = _DARK.format(s=':root[data-theme=dark]')
    return f'@media (prefers-color-scheme:dark){{{media}}}\n{forced}'


CHART_CSS = """
.viz-root{--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;"""+_ramp_vars(
    SEQ_LIGHT, SEQ_INK_LIGHT)+"""}
.heat{width:100%;height:auto;display:block;overflow:visible}
.heat .axis{font-size:11.5px;fill:var(--muted)}
.heat .axis-name{font-size:12px;font-weight:700;fill:var(--muted)}
.heat .cell{stroke:var(--card);stroke-width:2}
.heat .cell-empty{fill:none;stroke:var(--line);stroke-width:1;stroke-dasharray:3 3}
.heat .cell-ink{font-size:12.5px;font-weight:700}
.heat .cell-ink-muted{font-size:12.5px;fill:var(--muted)}
.heat-key{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);
padding:0 0 10px;flex-wrap:wrap}
.heat-ramp{display:inline-flex;gap:2px}
.heat-ramp i{width:20px;height:11px;border-radius:2px;display:inline-block}
.heat-end{font-variant-numeric:tabular-nums}
.chart-grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:14px 16px 10px;margin:0}
.chart-title{font-size:14px;font-weight:700;color:var(--ink);padding:0 0 6px}
.chart{width:100%;height:auto;display:block;overflow:visible}
.chart .grid{stroke:var(--line);stroke-width:1}
.chart .axis{font-size:11px;fill:var(--muted)}
.chart .series{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.chart .dot{stroke:var(--card);stroke-width:2}
.chart .point-label{font-size:11px;font-weight:700}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12.5px;color:var(--muted);
padding:0 0 8px}
.legend .key{display:inline-flex;align-items:center;gap:6px}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
.chart-note{font-size:12px;color:var(--muted);margin:6px 0 0}
#tip{position:fixed;z-index:60;pointer-events:none;background:var(--navy);color:#fff;
font-size:12px;padding:5px 9px;border-radius:6px;opacity:0;transition:opacity .1s}
#tip[data-on]{opacity:1}
"""+_dark_rules()

CHART_JS = """
const tip = document.createElement('div');
tip.id = 'tip';
document.body.appendChild(tip);
document.addEventListener('pointerover', event => {
  const host = event.target.closest('[data-tip]');
  if (!host) return;
  tip.textContent = host.dataset.tip;
  tip.setAttribute('data-on', '');
});
document.addEventListener('pointermove', event => {
  if (!tip.hasAttribute('data-on')) return;
  tip.style.left = Math.min(event.clientX + 14, innerWidth - tip.offsetWidth - 8) + 'px';
  tip.style.top = (event.clientY - tip.offsetHeight - 12) + 'px';
});
document.addEventListener('pointerout', event => {
  if (event.target.closest('[data-tip]')) tip.removeAttribute('data-on');
});
"""
