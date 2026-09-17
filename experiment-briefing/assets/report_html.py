"""Shared HTML primitives for briefing pages.

The page generators own their narrative and tables; what lives here is the part
that must stay identical between them - the design system, the tab behaviour,
the numeric table shell, and image embedding. Editing a page means editing its
generator, never the generated HTML.

Drop this next to your report generator and import from it. It needs only
Pillow, and only for `embed`.
"""
import base64
import io

def embed(path, quality=90):
    """Image path in, WebP data URI out; typically ~2.5x smaller than the PNG.

    Inlining is what makes the page one file: it survives being emailed,
    copied to a share, or opened from disk with no server behind it.
    """
    from PIL import Image
    buffer = io.BytesIO()
    Image.open(path).convert('RGB').save(buffer, 'WEBP', quality=quality, method=6)
    return 'data:image/webp;base64,'+base64.b64encode(buffer.getvalue()).decode()


def table_html(labels, rows, group_key='group', unit='', corner='', count_unit=''):
    """A numeric table where each row is one group x one series.

    Each cell is `(value, secondary)` - the second number renders muted next to
    the first, for a stricter variant of the same measure - or `None` for a
    condition that did not run. `count_unit` names what the per-row count is
    (samples, windows, runs). Set `thin: True` on a row whose count is too
    small to read as a rate; it gets a dagger.
    """
    head = ''.join(f'<th>{escape(t)}</th>' for t in labels)
    body = []
    for row in rows:
        cells = []
        for cell in row['cells']:
            if cell is None:
                cells.append('<td class="na">—</td>')
            elif cell[1] is None:
                cells.append(f'<td>{cell[0]:.0f}</td>')
            else:
                cells.append(f'<td>{cell[0]:.0f} <span class="strict">/ {cell[1]:.0f}</span></td>')
        mark = '<sup class="thin-mark">†</sup>' if row.get('thin') else ''
        body.append(
            f'<tr><th scope="row">{escape(row[group_key])}</th>'
            f'<td class="role"><span class="swatch" style="background:{row["color"]}"></span>'
            f'{escape(row["role"])}<span class="count">{row["gt"]} {escape(count_unit)}{mark}</span></td>'
            +''.join(cells)+'</tr>')
    caption = f'<caption>{escape(unit)}</caption>' if unit else ''
    return (f'<table class="data">{caption}<thead><tr>'
            f'<th>{escape(corner)}</th><th>类型</th>{head}</tr></thead><tbody>'
            +''.join(body)+'</tbody></table>')


def signed(value):
    """Signed number with a typographic minus, so tables match the figures."""
    return f'{value:+d}'.replace('-', '\u2212')


def escape(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


CSS = """
:root{--ink:#122b3d;--muted:#526979;--paper:#f5f6f3;--card:#ffffff;--line:#dce3df;
--teal:#087f73;--warn:#8a4b12;--warn-bg:#fdf3e4;--navy:#102b3e}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:78px}
body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.75 'Noto Sans CJK SC','Microsoft YaHei','PingFang SC',sans-serif}
a{color:var(--teal)}
header{position:sticky;top:0;z-index:20;background:#f5f6f3f2;backdrop-filter:blur(12px);
border-bottom:1px solid var(--line)}
.nav{max-width:1280px;margin:auto;display:flex;align-items:center;justify-content:space-between;
gap:18px;padding:12px 28px}
.brand{display:flex;gap:10px;align-items:center;font-size:14px;font-weight:700;white-space:nowrap}
.mark{background:var(--ink);color:#fff;padding:2px 8px;border-radius:4px;letter-spacing:2px}
.navlinks{display:flex;gap:20px;font-size:13px}.navlinks a{color:var(--muted);text-decoration:none}
.navlinks a:hover{color:var(--teal)}
main{max-width:1280px;margin:auto;padding:0 28px 90px}
section{padding-top:56px}
h1{font-size:40px;line-height:1.28;margin:.2em 0 .5em}
h2{font-size:26px;margin:0 0 .25em}h3{font-size:18px;margin:0 0 .4em}h4{font-size:15px;margin:0 0 .3em}
p{margin:.55em 0}
.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
font-weight:700}
.section-head{display:flex;gap:18px;align-items:flex-start;border-top:2px solid var(--ink);
padding-top:18px;margin-bottom:26px}
.section-no{font-size:13px;font-weight:800;color:var(--teal);padding-top:6px}
.section-head p{color:var(--muted);margin:.3em 0 0;max-width:72ch}
.hero{padding-top:44px}
.hero p.lede{font-size:18px;color:var(--muted);max-width:74ch}
.asks{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));margin:26px 0}
.ask{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.ask .eyebrow{color:var(--teal)}
.ask p{font-size:14.5px;margin:.4em 0 0}
.ask .verdict{font-size:13px;color:var(--muted);margin-top:.7em;padding-top:.6em;
border-top:1px dashed var(--line)}
.notice{background:var(--warn-bg);border:1px solid #e8c89a;border-left:5px solid #c8801f;
border-radius:10px;padding:18px 22px;margin:8px 0 6px}
.notice h3{color:var(--warn)}
.notice p{font-size:14.5px;margin:.4em 0}
.kpis{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));margin:30px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.kpi span{display:block;font-size:12.5px;color:var(--muted)}
.kpi strong{display:block;font-size:27px;line-height:1.25;margin:.15em 0;font-weight:800;
font-variant-numeric:tabular-nums}
.grid{display:grid;gap:16px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.grid.three{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.card p{font-size:14.5px;color:var(--muted)}
.card p strong{color:var(--ink)}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.tabs .label{font-size:12.5px;color:var(--muted);align-self:center;padding-right:4px}
.theme-toggle{font:inherit;font-size:12.5px;cursor:pointer;background:var(--card);
border:1px solid var(--line);border-radius:999px;padding:5px 12px;color:var(--muted);
white-space:nowrap;flex-shrink:0}
.theme-toggle:hover{border-color:var(--teal);color:var(--teal)}
@media print{.theme-toggle{display:none}}
.tab{font:inherit;font-size:13.5px;cursor:pointer;background:var(--card);border:1px solid var(--line);
border-radius:999px;padding:7px 15px;color:var(--muted)}
.tab:hover{border-color:var(--teal)}
/* The selected pill inverts, so its text has to track the surface rather than
   be a fixed white - in dark mode --ink is the light colour. */
.tab[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:var(--paper);
font-weight:700}
figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:12px;overflow:hidden}
figure img{width:100%;display:block;border-radius:6px}
figcaption{font-size:13px;color:var(--muted);padding:10px 6px 2px}
table.data{width:100%;border-collapse:collapse;font-size:14px;background:var(--card);
border:1px solid var(--line);border-radius:12px;overflow:hidden;font-variant-numeric:tabular-nums}
table.data caption{caption-side:top;text-align:left;font-size:12.5px;color:var(--muted);
padding:0 0 8px}
table.data th,table.data td{padding:9px 11px;border-bottom:1px solid var(--line);text-align:right}
table.data thead th{background:#eef1ec;font-size:12.5px;color:var(--muted);font-weight:700}
table.data th:first-child,table.data td:first-child,table.data td.role,
table.data thead th:nth-child(2){text-align:left}
table.data tbody tr:last-child th,table.data tbody tr:last-child td{border-bottom:0}
table.data td.role{white-space:nowrap}
table.data .strict{color:var(--muted)}
table.data .na{color:#9fb0ba}
.swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:7px;
vertical-align:baseline}
.count{color:var(--muted);font-size:12px;margin-left:8px}
.badge{display:inline-block;font-size:11px;font-weight:700;border-radius:999px;padding:1px 9px;
margin-left:7px;vertical-align:1px}
.badge.out{background:#fdf0e2;color:#8a4b12;border:1px solid #e3c39a}
.badge.in{background:#e6f2ef;color:#07655c;border:1px solid #b3d5cd}
.out-of-domain{color:#8a4b12}
.thin-mark{color:#b3621c;font-weight:700}
.footnote{font-size:13px;color:var(--muted);margin-top:10px}
.pill{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:999px;
padding:3px 11px;color:var(--muted);background:var(--card);margin-right:6px}
.plan{border-left:3px solid var(--teal);padding-left:16px;margin:16px 0}
.plan.alt{border-left-color:var(--line)}
.plan h4{font-size:16px}
ul{padding-left:1.15em}li{margin:.3em 0;font-size:14.5px}
pre{background:var(--navy);color:#dbe7ec;border-radius:10px;padding:15px 17px;overflow:auto;
font-size:12.5px;line-height:1.7}
code{background:#e8ece7;border-radius:4px;padding:1px 5px;font-size:13px}
pre code{background:none;padding:0;color:inherit}
footer{border-top:1px solid var(--line);margin-top:60px;padding:22px 0;font-size:13px;
color:var(--muted)}
@media(max-width:620px){
/* A long title plus a full nav cannot both fit; let the links scroll rather
   than push the page wider than the viewport. No effect where they already fit. */
.nav{gap:10px;padding:12px 16px}
.brand{flex-shrink:0}
.navlinks{overflow-x:auto;gap:14px;scrollbar-width:none}
.navlinks a{white-space:nowrap}
.navlinks::-webkit-scrollbar{display:none}
main{padding:0 16px 70px}h1{font-size:30px}}
@media print{header{position:static}.tabs{display:none}
/* Tab panels are hidden by attribute, which print must undo or the paper copy
   silently loses whichever weight was not selected. */
[data-panel][hidden],.tabpanel[hidden]{display:block!important}
section{break-inside:avoid;padding-top:24px}}
"""

JS = """
for (const group of document.querySelectorAll('[data-tabs]')) {
  const scope = document.querySelector(group.dataset.scope || 'body');
  group.addEventListener('click', event => {
    const button = event.target.closest('.tab');
    if (!button) return;
    for (const other of group.querySelectorAll('.tab'))
      other.setAttribute('aria-pressed', String(other === button));
    const key = group.dataset.tabs, value = button.dataset.value;
    scope.dataset[key] = value;
    for (const panel of scope.querySelectorAll(`[data-panel-${key}]`))
      panel.hidden = ![...Object.entries(panel.dataset)]
        .filter(([name]) => name.startsWith('panel'))
        .every(([name, want]) => scope.dataset[name.slice(5).toLowerCase()] === want);
  });
  group.querySelector('.tab').click();
}

// Theme toggle. The page already follows the OS setting; this exists because
// the reader's machine and the room are not the same thing - a light laptop in
// a dark meeting room, or a projector that washes out the dark palette.
// Deliberately not persisted: one page, one session, no storage to explain.
{
  const btn = document.querySelector('[data-theme-toggle]');
  if (btn) {
    const dark = () => matchMedia('(prefers-color-scheme: dark)').matches;
    const showing = () => document.documentElement.dataset.theme
      || (dark() ? 'dark' : 'light');
    const paint = () => { btn.textContent = showing() === 'dark' ? '☀ 浅色' : '☾ 深色'; };
    btn.addEventListener('click', () => {
      document.documentElement.dataset.theme = showing() === 'dark' ? 'light' : 'dark';
      paint();
    });
    paint();
  }
}
"""
