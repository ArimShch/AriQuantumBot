"""HTML-виджет со схемой квантовой цепи (Bot API 10.4) в стиле AriQuantum."""
import zlib
from html import escape

# Геометрия, px
LABEL_W = 40     # область подписей кубитов слева
COL_W = 52       # ширина одной колонки (шага схемы)
ROW_H = 46       # расстояние между линиями кубитов
BOX = 36         # сторона квадрата гейта
PAD_X = 10       # отступ справа
PAD_Y = 14       # отступ сверху/снизу

# Лимиты Telegram: HTML до 32 КБ, до 4 КБ после сжатия zlib (уровень 9)
MAX_RAW = 32768
MAX_COMPRESSED = 4096

STYLES = ('classic', 'outline', 'cube')

_CSS = '''
:root{__LIGHT__}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){__DARK__}}
:root[data-theme=dark]{__DARK__}
*{box-sizing:border-box}
body{margin:0}
.w{position:relative;display:flex;background:var(--bg);color:var(--fg);border-radius:12px;height:__H__px;overflow:hidden;font:12px/1 system-ui,sans-serif}
.lb{flex:none}
.vp{position:relative;flex:1;min-width:0;overflow:hidden;touch-action:pan-y;cursor:grab}
.in{width:__W__px;transition:transform .25s ease}
.in.drag{transition:none}
svg{display:block}
.wr{stroke:var(--wire);stroke-width:1.5}
.cw{stroke:var(--muted);stroke-width:1.2}
.q{fill:var(--muted);font:600 12px ui-monospace,monospace}
.cn{stroke:var(--fg);stroke-width:1.6}
.t{fill:#292929;font:600 15px system-ui,sans-serif;text-anchor:middle}
.t2{font-size:12px}
.ang{fill:#292929;font:500 9.5px system-ui,sans-serif;text-anchor:middle}
.ar{position:absolute;top:50%;width:28px;height:28px;margin-top:-14px;border:0;border-radius:14px;background:var(--bar);color:#292929;font:600 18px/26px system-ui,sans-serif;padding:0;text-align:center;display:none;cursor:pointer}
.ar.l{left:6px}
.ar.r{right:6px}
.ar.on{display:block}
.sb{position:absolute;left:__LW__px;right:10px;bottom:4px;height:3px;border-radius:2px;background:var(--wire);display:none}
.sb.on{display:block}
.sb i{position:absolute;top:0;bottom:0;border-radius:2px;background:var(--bar)}
__STYLE__
'''

_STYLE_CSS = {
    'classic': '''
.g{fill:var(--bar)}
.gp{fill:var(--cap)}
.cd{fill:var(--fg)}
.tx{fill:var(--bar)}
.tp{stroke:#292929;stroke-width:1.8;fill:none}
.m{fill:var(--fg)}
.mp{stroke:var(--bg);stroke-width:1.6;fill:none}
''',
    'outline': '''
.g{fill:var(--bg);stroke:var(--fg);stroke-width:1.5}
.gp{fill:var(--bg);stroke:var(--cap);stroke-width:2}
.t,.ang{fill:var(--fg)}
.cd{fill:var(--bar);stroke:var(--fg);stroke-width:1.5}
.tx{fill:var(--bg);stroke:var(--fg);stroke-width:1.5}
.tp{stroke:var(--fg);stroke-width:1.5;fill:none}
.m{fill:var(--bg);stroke:var(--fg);stroke-width:1.5}
.mp{stroke:var(--fg);stroke-width:1.5;fill:none}
''',
    'cube': '''
.sh{fill:#585757}
.g{fill:var(--bar);stroke:#292929;stroke-width:1.5}
.gp{fill:var(--cap);stroke:#292929;stroke-width:1.5}
.cd{fill:var(--fg)}
.m{fill:var(--fg);stroke:#292929;stroke-width:1.5}
.mp{stroke:var(--bg);stroke-width:1.6;fill:none}
''',
}

_JS = '''
(function(){
var W=window.TelegramWidget;
try{var sc=W&&W.colorScheme;if(sc==='dark'||sc==='light')document.documentElement.setAttribute('data-theme',sc);}catch(e){}
var vp=document.getElementById('vp'),inn=document.getElementById('in'),L=document.getElementById('al'),R=document.getElementById('ar'),sb=document.getElementById('sb'),th=sb.firstChild;
var CW=__W__,x=0,max=0,sx=0,so=0,dr=false,moved=false;
function upd(){
  inn.style.transform='translateX('+(-x)+'px)';
  L.className='ar l'+(max>0&&x>1?' on':'');
  R.className='ar r'+(max>0&&x<max-1?' on':'');
  sb.className='sb'+(max>0?' on':'');
  if(max>0){var tw=sb.clientWidth,w=Math.max(24,tw*vp.clientWidth/CW);th.style.width=w+'px';th.style.left=((tw-w)*x/max)+'px';}
}
function lay(){max=Math.max(0,CW-vp.clientWidth);if(x>max)x=max;upd();}
function go(v){x=Math.min(max,Math.max(0,v));upd();}
L.addEventListener('click',function(e){e.stopPropagation();go(x-vp.clientWidth*0.7);});
R.addEventListener('click',function(e){e.stopPropagation();go(x+vp.clientWidth*0.7);});
vp.addEventListener('pointerdown',function(e){if(max<=0)return;dr=true;moved=false;sx=e.clientX;so=x;inn.className='in drag';try{vp.setPointerCapture(e.pointerId);}catch(_){}});
vp.addEventListener('pointermove',function(e){if(!dr)return;var d=e.clientX-sx;if(Math.abs(d)>3)moved=true;go(so-d);});
function end(){if(!dr)return;dr=false;inn.className='in';}
vp.addEventListener('pointerup',end);vp.addEventListener('pointercancel',end);
window.addEventListener('resize',lay);
lay();setTimeout(lay,150);setTimeout(lay,600);
})();
'''


def _split_gate(name: str) -> tuple[str, str]:
    """'Rx(π/3)' -> ('Rx', 'π/3'); 'H' -> ('H', '')"""
    if '(' in name:
        base, params = name.split('(', 1)
        return base, params.rstrip(')')
    return name, ''


def _layout(num_qubits: int, history: list) -> tuple[list[dict], int, dict[int, int]]:
    """
    Раскладка по колонкам «как можно раньше»: операция занимает самую раннюю колонку,
    свободную на всех кубитах между её самым верхним и самым нижним участником.
    Возвращает (операции, число колонок, {кубит: колонка первого измерения}).
    """
    free = [0] * num_qubits
    ops: list[dict] = []
    measured_from: dict[int, int] = {}

    for name, ctrls, targets in history:
        target = targets[0]
        qubits = list(ctrls) + [target]
        lo, hi = min(qubits), max(qubits)
        col = max(free[lo:hi + 1])
        for q in range(lo, hi + 1):
            free[q] = col + 1
        ops.append({'name': name, 'ctrls': list(ctrls), 'target': target, 'col': col})
        if name == 'M':
            measured_from.setdefault(target, col)

    return ops, (max(free) if ops else 0), measured_from


def build_circuit_widget(
    num_qubits: int,
    history: list,
    style: str = 'outline',
) -> tuple[str, int] | None:
    """
    Строит HTML-виджет схемы.

    - Гейты стоят в колонках «как можно раньше» (как и в ASCII-схеме).
    - После измерения линия кубита становится двойной (классический бит).
    - Длинная схема не помещается в пузырь: её можно листать пальцем или кнопками ‹ ›.
    - Цвета из брендбука; тема определяется клиентом (prefers-color-scheme / colorScheme).

    Returns:
        (html, height_px) либо None, если виджет не укладывается в лимиты Telegram
        (тогда вызывающий код показывает ASCII-схему).
    """
    if style not in STYLES:
        style = 'outline'
    cube = style == 'cube'

    ops, ncols, measured_from = _layout(num_qubits, history)
    ncols = max(ncols, 3)   # у пустой схемы всё равно должна быть видна «дорожка»

    width = ncols * COL_W + PAD_X   # ширина прокручиваемой части (подписи кубитов закреплены слева)
    height = PAD_Y * 2 + ROW_H * num_qubits
    full_height = height + 10   # место под индикатор прокрутки

    def wy(q: int) -> float:
        return PAD_Y + ROW_H * q + ROW_H / 2

    def cx(col: int) -> float:
        return col * COL_W + COL_W / 2

    parts: list[str] = []
    labels: list[str] = []

    # линии кубитов, подписи и классические (двойные) линии
    for q in range(num_qubits):
        y = wy(q)
        parts.append(f'<line class="wr" x1="0" y1="{y:g}" x2="{width - PAD_X}" y2="{y:g}"/>')
        labels.append(f'<text class="q" x="{LABEL_W - 10}" y="{y + 4:g}" text-anchor="end">q{q}</text>')
        if q in measured_from:
            x0 = cx(measured_from[q])
            for dy in (-2, 2):
                parts.append(
                    f'<line class="cw" x1="{x0:g}" y1="{y + dy:g}" x2="{width - PAD_X}" y2="{y + dy:g}"/>'
                )

    half = BOX / 2
    # вертикальные связи (под гейтами)
    for op in ops:
        if op['ctrls']:
            qs = op['ctrls'] + [op['target']]
            x = cx(op['col'])
            parts.append(f'<line class="cn" x1="{x:g}" y1="{wy(min(qs)):g}" x2="{x:g}" y2="{wy(max(qs)):g}"/>')

    # гейты, управляющие точки, измерения
    for op in ops:
        x = cx(op['col'])
        y = wy(op['target'])
        base, angle = _split_gate(op['name'])

        for c in op['ctrls']:
            cy = wy(c)
            if cube:
                parts.append(f'<rect class="cd" x="{x - 4.5:g}" y="{cy - 4.5:g}" width="9" height="9"/>')
            else:
                parts.append(f'<circle class="cd" cx="{x:g}" cy="{cy:g}" r="4.5"/>')

        if base == 'M':
            if cube:
                parts.append(f'<rect class="sh" x="{x - half + 3:g}" y="{y - half + 3:g}" width="{BOX}" height="{BOX}"/>')
            rx = 0 if cube else 7
            parts.append(f'<rect class="m" x="{x - half:g}" y="{y - half:g}" width="{BOX}" height="{BOX}" rx="{rx}"/>')
            parts.append(
                f'<path class="mp" d="M{x - 9:g} {y + 6:g}A9 9 0 0 1 {x + 9:g} {y + 6:g}M{x:g} {y + 6:g}L{x + 6:g} {y - 6:g}"/>'
            )
            continue

        if base == 'X' and op['ctrls'] and not cube:
            parts.append(f'<circle class="tx" cx="{x:g}" cy="{y:g}" r="12"/>')
            parts.append(f'<path class="tp" d="M{x - 7:g} {y:g}H{x + 7:g}M{x:g} {y - 7:g}V{y + 7:g}"/>')
            continue

        cls = 'gp' if angle else 'g'
        if cube:
            parts.append(f'<rect class="sh" x="{x - half + 3:g}" y="{y - half + 3:g}" width="{BOX}" height="{BOX}"/>')
        rx = 0 if cube else 7
        parts.append(f'<rect class="{cls}" x="{x - half:g}" y="{y - half:g}" width="{BOX}" height="{BOX}" rx="{rx}"/>')
        if angle:
            parts.append(f'<text class="t t2" x="{x:g}" y="{y - 2:g}">{escape(base)}</text>')
            parts.append(f'<text class="ang" x="{x:g}" y="{y + 11:g}">{escape(angle)}</text>')
        else:
            size = ' t2' if len(base) > 1 else ''
            parts.append(f'<text class="t{size}" x="{x:g}" y="{y + 5.5:g}">{escape(base)}</text>')

    light_vars = (
        '--bg:#F5ECE4;--fg:#292929;--muted:#585757;--wire:rgba(41,41,41,.28);'
        '--bar:#FACF5B;--cap:#CC8F0B'
    )
    dark_vars = (
        '--bg:#292929;--fg:#F5ECE4;--muted:#B8AFA8;--wire:rgba(245,236,228,.30);'
        '--bar:#FACF5B;--cap:#CC8F0B'
    )
    css = (_CSS.replace('__STYLE__', _STYLE_CSS[style])
               .replace('__LIGHT__', light_vars).replace('__DARK__', dark_vars)
               .replace('__H__', str(full_height)).replace('__W__', str(width))
               .replace('__LW__', str(LABEL_W)))
    js = _JS.replace('__W__', str(width))

    svg = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'
    )
    html = (
        f'<style>{css}</style>'
        f'<div class="w"><svg class="lb" width="{LABEL_W}" height="{height}" xmlns="http://www.w3.org/2000/svg">{"".join(labels)}</svg>'
        f'<div class="vp" id="vp"><div class="in" id="in">{svg}</div>'
        f'<button class="ar l" id="al">‹</button><button class="ar r" id="ar">›</button></div>'
        f'<div class="sb" id="sb"><i></i></div></div>'
        f'<script>{js}</script>'
    )

    raw = html.encode('utf-8')
    if len(raw) > MAX_RAW or len(zlib.compress(raw, 9)) > MAX_COMPRESSED:
        return None
    return html, full_height
