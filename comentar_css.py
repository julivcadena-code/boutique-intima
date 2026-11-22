# Numera y comenta línea por línea el CSS nuevo escrito entre /*RAW*/ y /*ENDRAW*/ en index.html.
# Cada regla debe empezar con un comentario  /* [CLARO|OSCURO|AMBOS] explicación */
import re,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
PRX={'background':'fondo (color, degradado o imagen)','background-image':'imagen o degradado de fondo','color':'color del texto','border':'borde','border-radius':'esquinas redondeadas','border-top':'borde superior','box-shadow':'sombra o resplandor','text-shadow':'sombra del texto','font':'tipo, tamaño y estilo de letra','font-size':'tamaño de letra','font-style':'cursiva o normal','letter-spacing':'espacio entre letras','text-transform':'mayúsculas/minúsculas','text-align':'alineación del texto','padding':'espacio interior','margin':'espacio exterior','width':'ancho','height':'alto','max-width':'ancho máximo','opacity':'transparencia','transition':'animación suave al cambiar','animation':'animación','transform':'mover, girar o agrandar','transform-origin':'punto de giro','transform-style':'profundidad 3D','translate':'desplazamiento','rotate':'giro','scale':'zoom','filter':'filtro','backdrop-filter':'desenfoque de cristal','-webkit-backdrop-filter':'desenfoque de cristal (Safari)','display':'cómo se muestra','position':'tipo de posición','top':'distancia desde arriba','bottom':'distancia desde abajo','left':'distancia desde la izquierda','right':'distancia desde la derecha','inset':'distancia a los 4 bordes','z-index':'capa (mayor = encima)','overflow':'recorte','pointer-events':'si recibe clics','stroke':'color de línea del ícono','stroke-width':'grosor de línea','stroke-linecap':'puntas de línea','stroke-linejoin':'uniones de línea','fill':'relleno','gap':'separación','align-items':'alineación vertical','justify-content':'alineación horizontal','content':'texto o decoración agregada','background-attachment':'fondo fijo','background-size':'tamaño del fondo','white-space':'cómo se parte el texto','line-height':'alto de línea','will-change':'aviso de animación','min-height':'alto mínimo','font-weight':'grosor de letra'}
def explain(d):
    p=d.split(':',1)[0].strip()
    return ('variable: '+p if p.startswith('--') else PRX.get(p,'propiedad "'+p+'"')).replace('*/','*')
def decls(b):
    out=[];cur='';dp=0;q=None
    for ch in b:
        if q:
            cur+=ch;q=None if ch==q else q;continue
        if ch in '"\'':q=ch;cur+=ch;continue
        dp+=(ch=='(')-(ch==')')
        if ch==';' and dp==0:out.append(cur);cur='';continue
        cur+=ch
    if cur.strip():out.append(cur)
    return [x.strip() for x in out if x.strip()]
def fmt(css,num,ind=''):
    out='';i=0
    while i<len(css):
        j=css.find('{',i)
        if j<0:break
        hdr=css[i:j];d=1;k=j+1
        while d:c=css[k];d+=(c=='{')-(c=='}');k+=1
        body=css[j+1:k-1];lead=re.findall(r'/\*.*?\*/',hdr,re.S);h=re.sub(r'/\*.*?\*/','',hdr,flags=re.S).strip()
        if lead:
            m=re.match(r'/\*\s*\[(.*?)\]\s*(.*?)\s*\*/',lead[0],re.S)
            if m and not ind:num[0]+=1;out+=f'{ind}/* #{num[0]} [{m.group(1)}] {m.group(2)} */\n'
        if '{' in body:out+=f'{ind}{h}{{\n'+fmt(body,num,ind+'  ')+f'{ind}}}\n'
        else:
            out+=f'{ind}{h}{{\n'+''.join(f'{ind}  {x};  /* {explain(x)} */\n' for x in decls(body))+f'{ind}}}\n'
        i=k
    return out
s=open('index.html',encoding='utf8').read()
m=re.search(r'/\*RAW\*/(.*?)/\*ENDRAW\*/',s,re.S)
if not m:print('No hay bloque /*RAW*/ pendiente');raise SystemExit
num=[max(int(x) for x in re.findall(r'/\* #(\d+) \[',s))]
s=s[:m.start()]+fmt(m.group(1),num)+s[m.end():]
open('index.html','w',encoding='utf8').write(s);print('reglas nuevas comentadas hasta #',num[0])
