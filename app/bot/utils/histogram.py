import json
import zlib
import math
from html import escape

# Максимум столбцов в виджете (показываются самые частые состояния)
MAX_BARS = 16
BAR_AREA_HEIGHT = 210   # высота области графика, px
EST_PLOT_WIDTH = 250    # консервативная оценка ширины области столбцов (узкий пузырь), px
CHAR_PX = 7.5           # консервативная ширина символа подписи (monospace 11px), px
LABEL_H = 13            # высота строки подписи, px


def format_counts_ascii(counts: dict[str, int]) -> str:
    """ASCII-гистограмма: |000⟩ █████░░░░░ 46.0% (46)"""
    total_shots = sum(counts.values())
    counts_lines = []

    # Находим максимальную длину ключа (состояния) для ровного отступа
    max_state_len = max(len(str(state)) for state in counts.keys())

    for state, count in sorted(counts.items()):
        # Считаем процент выпадения
        percent = (count / total_shots) * 100

        # Вычисляем количество закрашенных блоков из 10
        filled_blocks_int = int(percent / 10)
        filled_blocks = round(percent / 10)

        # Если исход выпадал, но процент слишком мал (<10%), рисуем хотя бы 1 блок
        if count > 0 and filled_blocks == 0:
            filled_blocks = 1

        bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
        state_padded = str(state).ljust(max_state_len)

        # Выравнивание процентов вправо (4 символа, 1 знак после запятой)
        counts_lines.append(f"|{state_padded}⟩ {bar} {percent:>4.1f}% ({count})")

    return "\n".join(counts_lines)


def _label_class(label_w: float, bar_w: float, bar_h: float) -> str:
    """
    Класс подписи состояния, подобранный на сервере по консервативным размерам.
    Гарантирует, что подписи не наезжают друг на друга, даже если скрипт в клиенте
    не отработает; если скрипт работает, он уточняет выбор по реальным размерам.
    """
    if label_w + 6 <= bar_w and LABEL_H + 8 <= bar_h:
        return 'st'                       # горизонтально внутри столбца
    if 11 <= bar_w and label_w + 10 <= bar_h:   # 11px — толщина вертикальной строки
        return 'st v'                     # вертикально вдоль столбца
    if label_w <= bar_w + 4:
        return 'st out'                   # горизонтально над столбцом
    return 'st out v'                     # вертикально над столбцом


def _fmt_percent(value: float) -> str:
    return f"{value:.0f}%" if value >= 10 or value == 0 else f"{value:.1f}%"


_BAR_STYLES = {
    'cap': 'border-top:3px solid var(--cap)',
    'flat': 'border:0',
    'outline': 'border:1px solid var(--cap);border-bottom:0',
}

_CSS = '''
:root{__LIGHT__}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){__DARK__}}
:root[data-theme=dark]{__DARK__}
*{box-sizing:border-box}
body{margin:0}
.w{position:relative;background:var(--bg);color:var(--fg);border-radius:12px;padding:16px 12px 16px 8px;height:__H__px;font:12px/1 system-ui,sans-serif;overflow:hidden}
.g{display:grid;grid-template-columns:34px 1fr;grid-template-rows:__BAR__px;column-gap:6px;height:__BAR__px;transition:filter .2s,opacity .2s}
.g.blur{filter:blur(4px);opacity:.45}
.y{position:relative;height:__BAR__px;color:var(--muted);font-size:10px}
.y span{position:absolute;right:0;transform:translateY(50%)}
.p{position:relative;height:__BAR__px;border-bottom:1px solid var(--muted)}
.p i{position:absolute;left:0;right:0;height:1px;background:var(--grid)}
.bars{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;gap:__GAP__px;padding:0 __PAD__px}
.col{position:relative;flex:1;min-width:0;cursor:pointer}
.bar{position:absolute;left:0;right:0;bottom:0;min-height:2px;background:var(--bar);border-radius:4px 4px 0 0;__BARSTYLE__}
.bar b{position:absolute;bottom:100%;left:-6px;right:-6px;margin-bottom:3px;text-align:center;font-weight:600;font-size:11px;color:var(--fg)}
.st{position:absolute;left:50%;bottom:6px;transform:translateX(-50%);font:11px/11px ui-monospace,monospace;white-space:nowrap;color:#292929}
.st.v{top:100%;bottom:auto;margin-top:-6px;margin-left:-5.5px;transform-origin:0 0;transform:rotate(-90deg)}
.st.out{bottom:100%;margin-bottom:5px;color:var(--fg)}
.pv .st.out{margin-bottom:20px}
.st.out.v,.pv .st.out.v{top:0;bottom:auto;margin-top:-8px;margin-bottom:0}
.pv .st.out.v{margin-top:-23px}
.ov{position:absolute;top:0;left:0;right:0;bottom:0;display:none;align-items:center;justify-content:center;padding:12px;cursor:pointer}
.ov.on{display:flex}
.card{background:var(--card);color:var(--fg);border-radius:10px;border:1px solid var(--muted);padding:12px 16px;max-width:100%;line-height:1.5;font-size:13px}
.card .k{font:600 16px/1.3 ui-monospace,monospace;margin-bottom:4px}
.card .q{color:var(--muted);font:11px/1.4 ui-monospace,monospace;margin-top:4px;word-break:break-all}
'''

_JS = '''
(function(){
var W=window.TelegramWidget;
try{var sc=W&&W.colorScheme;if(sc==='dark'||sc==='light')document.documentElement.setAttribute('data-theme',sc);}catch(e){}
var T=__TEXTS__,TOTAL=__TOTAL__;
var g=document.getElementById('g'),ov=document.getElementById('ov');
var cols=document.querySelectorAll('.col');
function openCard(col){
  var s=col.getAttribute('data-s'),c=+col.getAttribute('data-c');
  var q=s.split('').map(function(b,i){return 'q'+i+' = '+b;}).join(', ');
  ov.innerHTML='<div class="card"><div class="k">|'+s+'\\u27e9</div>'+
    '<div>'+T.count+': <b>'+c+'</b> '+T.of+' '+TOTAL+'</div>'+
    '<div>'+T.share+': <b>'+(c/TOTAL*100).toFixed(1)+'%</b></div>'+
    '<div class="q">'+T.qubits+': '+q+'</div></div>';
  g.classList.add('blur');ov.classList.add('on');
}
function closeCard(){g.classList.remove('blur');ov.classList.remove('on');}
cols.forEach(function(col){col.addEventListener('click',function(){openCard(col);});});
ov.addEventListener('click',closeCard);
})();
'''


def _build_fixed(
    items: list[tuple[str, int]],
    total: int,
    t: dict[str, str],
    bar_style: str,
    hidden: int,
) -> tuple[str, int, int]:
    """
    Виджет для небольшого числа состояний: столбцы делят ширину поровну.

    Подпись состояния рисуется прямо на столбце: горизонтально, если помещается по ширине;
    иначе вертикально вдоль столбца; если не помещается и так — над столбцом
    (класс подписи подбирается на сервере по осторожным оценкам размеров).
    """
    percents = [(state, count, count / total * 100) for state, count in items]
    max_percent = max(p for _, _, p in percents)

    # Ось Y: «круглый» шаг, не более 6 делений (46% -> 0..50 с шагом 10)
    step = next(s for s in (1, 2, 5, 10, 20, 25, 50, 100) if math.ceil(max_percent / s) <= 6)
    axis_max = max(step, math.ceil(max_percent / step) * step)
    ticks = list(range(0, axis_max + 1, step))

    n = len(percents)
    show_values = n <= 8
    gap = 4 if n > 8 else 8
    pad = 2 if n > 8 else 6
    height = 16 + BAR_AREA_HEIGHT + 16

    y_ticks = ''.join(
        f'<span style="bottom:{tick / axis_max * 100:.2f}%">{tick}%</span>' for tick in ticks
    )
    grid = ''.join(
        f'<i style="bottom:{tick / axis_max * 100:.2f}%"></i>' for tick in ticks
    )

    cols = []
    for state, count, percent in percents:
        bar_h = percent / axis_max * 100
        value = f'<b>{_fmt_percent(percent)}</b>' if show_values else ''
        state_e = escape(state, quote=True)
        label_cls = _label_class(
            label_w=(len(state) + 2) * CHAR_PX,
            bar_w=(EST_PLOT_WIDTH - 2 * pad - (n - 1) * gap) / n,
            bar_h=percent / axis_max * BAR_AREA_HEIGHT - 3,
        )
        cols.append(
            f'<div class="col" data-s="{state_e}" data-c="{count}">'
            f'<div class="bar" style="height:{bar_h:.2f}%">{value}'
            f'<span class="{label_cls}">|{state_e}⟩</span></div></div>'
        )
    cols_html = ''.join(cols)

    dark_vars = (
        '--bg:#292929;--fg:#F5ECE4;--muted:#B8AFA8;'
        '--grid:rgba(245,236,228,.16);--bar:#FACF5B;--cap:#CC8F0B;--card:#3a3a3a'
    )
    light_vars = (
        '--bg:#F5ECE4;--fg:#292929;--muted:#585757;'
        '--grid:rgba(41,41,41,.14);--bar:#FACF5B;--cap:#CC8F0B;--card:#FFFFFF'
    )

    css = (_CSS.replace('__LIGHT__', light_vars).replace('__DARK__', dark_vars)
               .replace('__H__', str(height)).replace('__BAR__', str(BAR_AREA_HEIGHT)).replace('__GAP__', str(gap))
               .replace('__PAD__', str(pad))
               .replace('__BARSTYLE__', _BAR_STYLES.get(bar_style, _BAR_STYLES['flat'])))
    js = (_JS.replace('__TEXTS__', json.dumps(t, ensure_ascii=False))
             .replace('__TOTAL__', str(total)))

    pv = ' pv' if show_values else ''
    html = (
        f'<style>{css}</style>'
        f'<div class="w{pv}"><div class="g" id="g">'
        f'<div class="y">{y_ticks}</div>'
        f'<div class="p">{grid}<div class="bars">{cols_html}</div></div>'
        f'</div><div class="ov" id="ov"></div></div>'
        f'<script>{js}</script>'
    )
    return html, height, hidden


# ---------------------------------------------------------------------------
# Режим прокрутки: много состояний (например, 10 кубитов). Столбцы фиксированной
# ширины, график листается вбок пальцем или кнопками ‹ ›. Столбцы рисует скрипт
# из компактных данных, иначе HTML не уложился бы в лимиты Telegram.
# ---------------------------------------------------------------------------
SCROLL_COL_W = 20      # ширина столбца, px
SCROLL_GAP = 2         # зазор между столбцами, px
LABEL_W = 48           # ширина колонки с подписями шкалы процентов, px
MAX_RAW = 32768        # лимит Telegram: HTML до 32 КБ ...
MAX_COMPRESSED = 4096  # ... и до 4 КБ после сжатия zlib (уровень 9)

_SCROLL_CSS = '''
.w{display:flex;padding:0;overflow:hidden}
.lb{flex:none;display:block}
.lb text{fill:var(--muted);font:10px system-ui,sans-serif;text-anchor:end}
.vp{position:relative;flex:1;min-width:0;height:__BAR__px;margin:16px 12px 0 0;overflow:hidden;touch-action:pan-y;cursor:grab}
.in{position:relative;height:__BAR__px}
svg{display:block}
.w.blur .lb,.w.blur .vp{filter:blur(4px);opacity:.45}
.gl{stroke:var(--grid);stroke-width:1}
.ax{stroke:var(--muted);stroke-width:1}
.sbar{fill:var(--bar)}
.tin,.tout{font:11px ui-monospace,monospace}
.tin{fill:#292929}
.tout{fill:var(--fg)}
.ar{position:absolute;top:50%;width:28px;height:28px;margin-top:-14px;border:0;border-radius:14px;background:var(--bar);color:#292929;font:600 18px/26px system-ui,sans-serif;padding:0;text-align:center;display:none;cursor:pointer;z-index:2}
.ar.l{left:6px}
.ar.r{right:6px}
.ar.on{display:block}
.sb{position:absolute;left:54px;right:12px;bottom:6px;height:3px;border-radius:2px;background:var(--grid);display:none}
.sb.on{display:block}
.sb i{position:absolute;top:0;bottom:0;border-radius:2px;background:var(--bar)}
'''

_SCROLL_JS = '''
(function(){
var W=window.TelegramWidget;
try{var sc=W&&W.colorScheme;if(sc==='dark'||sc==='light')document.documentElement.setAttribute('data-theme',sc);}catch(e){}
var T=__TEXTS__,TOTAL=__TOTAL__,NB=__NB__,AX=__AX__,AH=__AH__,CW=__CW__,STEP=__STEP__,COLW=__COLW__,TK=__TICKS__;
var D='__DATA__'.split(';');
var g=document.getElementById('g'),ov=document.getElementById('ov'),vp=document.getElementById('vp'),inn=document.getElementById('in');
var L=document.getElementById('al'),R=document.getElementById('ar'),sb=document.getElementById('sb'),th=sb.firstChild;
var S=[],C=[],idx=0;
D.forEach(function(t){var p=t.split(',');idx+=parseInt(p[0],36);S.push(idx.toString(2).padStart(NB,'0'));C.push(parseInt(p[1],36));});
var N=S.length;
function col(i,x0){
  var pct=C[i]/TOTAL*100,bh=Math.max(2,pct/AX*AH),top=AH-bh,r=Math.min(4,bh),x1=x0+COLW,cx=x0+COLW/2;
  var out='<g data-i="'+i+'"><rect x="'+x0+'" y="0" width="'+COLW+'" height="'+AH+'" fill="transparent"/>'+
    '<path class="sbar" d="M'+x0+' '+AH+'V'+(top+r)+'Q'+x0+' '+top+' '+(x0+r)+' '+top+'H'+(x1-r)+'Q'+x1+' '+top+' '+x1+' '+(top+r)+'V'+AH+'Z"/>';
  var inside=((NB+2)*7.5+10<=bh-3);
  var ty=inside?(AH-6):(top-5);
  out+='<text class="'+(inside?'tin':'tout')+'" transform="rotate(-90 '+(cx+4)+' '+ty+')" x="'+(cx+4)+'" y="'+ty+'">|'+S[i]+'\\u27e9</text></g>';
  return out;
}
function openCard(i){
  var s=S[i],c=C[i];
  var q=s.split('').map(function(b,k){return 'q'+k+' = '+b;}).join(', ');
  ov.innerHTML='<div class="card"><div class="k">|'+s+'\\u27e9</div>'+
    '<div>'+T.count+': <b>'+c+'</b> '+T.of+' '+TOTAL+'</div>'+
    '<div>'+T.share+': <b>'+(c/TOTAL*100).toFixed(1)+'%</b></div>'+
    '<div class="q">'+T.qubits+': '+q+'</div></div>';
  g.classList.add('blur');ov.classList.add('on');
}
function closeCard(){g.classList.remove('blur');ov.classList.remove('on');}
ov.addEventListener('click',closeCard);
var x=0,max=0,sx=0,so=0,dr=false,moved=false,rf=-1,rl=-1,raf=0,fin=0;
var cg=null,rv=0;
function line(cls,y,w){return '<line class="'+cls+'" x1="0" y1="'+(y-.5)+'" x2="'+w+'" y2="'+(y-.5)+'"/>';}
function render(){
  var vw=vp.clientWidth||300,first=Math.max(0,Math.floor(x/STEP)),last=Math.min(N-1,Math.ceil((x+vw)/STEP));
  if(first!==rf||last!==rl||vw!==rv||!cg){
    var h=[];
    TK.forEach(function(t){if(t>0)h.push(line('gl',AH-t/AX*AH,vw));});
    h.push('<g class="cg">');
    for(var i=first;i<=last;i++)h.push(col(i,(i-first)*STEP));
    h.push('</g>');
    h.push(line('ax',AH,vw));
    inn.style.width=vw+'px';
    inn.innerHTML='<svg width="'+vw+'" height="'+AH+'" viewBox="0 0 '+vw+' '+AH+'" xmlns="http://www.w3.org/2000/svg">'+h.join('')+'</svg>';
    cg=inn.querySelector('.cg');rf=first;rl=last;rv=vw;
  }
  cg.setAttribute('transform','translate('+(first*STEP-x)+' 0)');
}
function upd(){
  render();
  L.className='ar l'+(max>0&&x>1?' on':'');
  R.className='ar r'+(max>0&&x<max-1?' on':'');
  sb.className='sb'+(max>0?' on':'');
  if(max>0){var tw=sb.clientWidth,w=Math.max(24,tw*vp.clientWidth/CW);th.style.width=w+'px';th.style.left=((tw-w)*x/max)+'px';}
}
function lay(){max=Math.max(0,CW-vp.clientWidth);if(x>max)x=max;upd();}
var pend=false;
function go(v){x=Math.min(max,Math.max(0,v));if(!pend){pend=true;requestAnimationFrame(function(){pend=false;upd();});}}
function anim(to){
  to=Math.min(max,Math.max(0,to));var from=x,t0=null;
  if(raf)cancelAnimationFrame(raf);
  function f(t){if(t0===null)t0=t;var p=Math.min(1,(t-t0)/250);p=1-Math.pow(1-p,3);x=from+(to-from)*p;upd();if(p<1)raf=requestAnimationFrame(f);else raf=0;}
  raf=requestAnimationFrame(f);
  clearTimeout(fin);fin=setTimeout(function(){x=to;upd();},320);
}
L.addEventListener('click',function(e){e.stopPropagation();anim(x-vp.clientWidth*0.7);});
R.addEventListener('click',function(e){e.stopPropagation();anim(x+vp.clientWidth*0.7);});
vp.addEventListener('pointerdown',function(e){if(raf){cancelAnimationFrame(raf);raf=0;}clearTimeout(fin);dr=true;moved=false;sx=e.clientX;so=x;});
vp.addEventListener('pointermove',function(e){
  if(!dr)return;var d=e.clientX-sx;
  if(!moved&&Math.abs(d)>4){moved=true;try{vp.setPointerCapture(e.pointerId);}catch(_){}}
  if(moved)go(so-d);
});
function end(){if(!dr)return;dr=false;setTimeout(function(){moved=false;},0);}
vp.addEventListener('pointerup',end);vp.addEventListener('pointercancel',end);
inn.addEventListener('click',function(e){if(moved)return;var c=e.target.closest('[data-i]');if(c)openCard(+c.getAttribute('data-i'));});
window.addEventListener('resize',lay);
lay();setTimeout(lay,150);setTimeout(lay,600);
})();
'''


def _to36(value: int) -> str:
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    if value == 0:
        return '0'
    out = ''
    while value:
        value, rem = divmod(value, 36)
        out = digits[rem] + out
    return out


def _fits_limits(html: str) -> bool:
    raw = html.encode('utf-8')
    return len(raw) <= MAX_RAW and len(zlib.compress(raw, 9)) <= MAX_COMPRESSED


def _build_scroll(
    items: list[tuple[str, int]],
    total: int,
    t: dict[str, str],
    bar_style: str,
) -> tuple[str, int]:
    """Виджет с прокруткой: items — [(состояние, число раз)] по возрастанию состояния."""
    max_percent = max(c for _, c in items) / total * 100
    step = next(s for s in (1, 2, 5, 10, 20, 25, 50, 100) if math.ceil(max_percent / s) <= 6)
    axis_max = max(step, math.ceil(max_percent / step) * step)
    ticks = list(range(0, axis_max + 1, step))

    n = len(items)
    content_w = n * SCROLL_COL_W + (n - 1) * SCROLL_GAP
    height = 16 + BAR_AREA_HEIGHT + 16 + 10   # +10 — индикатор прокрутки

    # Подписи шкалы процентов — отдельный SVG слева (как подписи кубитов в схеме)
    y_ticks = ''.join(
        f'<text x="{LABEL_W - 6}" y="{16 + BAR_AREA_HEIGHT * (1 - tick / axis_max) + 3.5:.1f}">{tick}%</text>'
        for tick in ticks
    )
    # Состояния по возрастанию: передаём разницу номеров соседних состояний (она мала,
    # данные хорошо сжимаются) и число раз, всё в системе счисления с основанием 36.
    chunks = []
    prev = 0
    for state, count in items:
        idx = int(state, 2)
        chunks.append(f'{_to36(idx - prev)},{_to36(count)}')
        prev = idx
    data = ';'.join(chunks)

    dark_vars = (
        '--bg:#292929;--fg:#F5ECE4;--muted:#B8AFA8;'
        '--grid:rgba(245,236,228,.16);--bar:#FACF5B;--cap:#CC8F0B;--card:#3a3a3a'
    )
    light_vars = (
        '--bg:#F5ECE4;--fg:#292929;--muted:#585757;'
        '--grid:rgba(41,41,41,.14);--bar:#FACF5B;--cap:#CC8F0B;--card:#FFFFFF'
    )
    css = (_CSS + _SCROLL_CSS)
    css = (css.replace('__LIGHT__', light_vars).replace('__DARK__', dark_vars)
              .replace('__H__', str(height)).replace('__BAR__', str(BAR_AREA_HEIGHT))
              .replace('__GAP__', '0').replace('__PAD__', '0')
              .replace('__COLW__', str(SCROLL_COL_W)).replace('__CW__', str(content_w))
              .replace('__SGAP__', str(SCROLL_GAP))
              .replace('__BARSTYLE__', _BAR_STYLES.get(bar_style, _BAR_STYLES['flat'])))
    js = (_SCROLL_JS.replace('__TEXTS__', json.dumps(t, ensure_ascii=False))
                    .replace('__TOTAL__', str(total)).replace('__NB__', str(len(items[0][0])))
                    .replace('__AX__', str(axis_max)).replace('__AH__', str(BAR_AREA_HEIGHT))
                    .replace('__CW__', str(content_w)).replace('__STEP__', str(SCROLL_COL_W + SCROLL_GAP))
                    .replace('__COLW__', str(SCROLL_COL_W)).replace('__TICKS__', json.dumps(ticks))
                    .replace('__DATA__', data))

    html = (
        f'<style>{css}</style>'
        f'<div class="w" id="g"><svg class="lb" width="{LABEL_W}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">{y_ticks}</svg>'
        f'<div class="vp" id="vp"><div class="in" id="in"></div>'
        f'<button class="ar l" id="al">‹</button><button class="ar r" id="ar">›</button></div>'
        f'<div class="sb" id="sb"><i></i></div><div class="ov" id="ov"></div></div>'
        f'<script>{js}</script>'
    )
    return html, height


def build_histogram_widget(
    counts: dict[str, int],
    texts: dict[str, str] | None = None,
    bar_style: str = 'flat',
) -> tuple[str, int, int]:
    """
    Строит HTML-виджет с гистограммой в стиле AriQuantum.

    - Показываются только состояния, которые выпали хотя бы раз.
    - До MAX_BARS состояний столбцы делят ширину поровну; если состояний больше,
      включается режим прокрутки: показываются ВСЕ состояния, график листается вбок.
    - Нажатие на столбец размывает график и показывает карточку с подробностями.
    - Цвета из брендбука; светлая/тёмная тема определяется на стороне клиента
      (prefers-color-scheme и TelegramWidget.colorScheme), в Update тема не приходит.

    texts: подписи для карточки деталей (ключи count, of, share, qubits).
    bar_style: 'flat' (сплошной жёлтый, по умолчанию), 'cap' (тёмная верхняя кромка) или
               'outline' (обводка 1px тёмно-жёлтым).

    Returns:
        (html, height_px, hidden_states) — hidden_states > 0 только если даже в режиме
        прокрутки все состояния не влезли в лимиты Telegram и показаны самые частые.
    """
    texts = texts or {}
    t = {
        'count': texts.get('count', 'Count'),
        'of': texts.get('of', 'of'),
        'share': texts.get('share', 'Share'),
        'qubits': texts.get('qubits', 'Qubits'),
    }

    total = sum(counts.values())
    items = sorted(
        ((state, count) for state, count in counts.items() if count > 0),
        key=lambda x: x[0],
    )

    if len(items) <= MAX_BARS:
        return _build_fixed(items, total, t, bar_style, 0)

    # Режим прокрутки. Если все состояния не влезают в лимиты, оставляем самые частые.
    keep = len(items)
    while keep > MAX_BARS:
        chosen = items if keep == len(items) else sorted(
            sorted(items, key=lambda x: x[1], reverse=True)[:keep], key=lambda x: x[0]
        )
        html, height = _build_scroll(chosen, total, t, bar_style)
        if _fits_limits(html):
            return html, height, len(items) - keep
        keep = int(keep * 0.85)

    top = sorted(sorted(items, key=lambda x: x[1], reverse=True)[:MAX_BARS], key=lambda x: x[0])
    return _build_fixed(top, total, t, bar_style, len(items) - MAX_BARS)
