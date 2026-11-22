# Sincroniza la tienda con Google Sheets (CSV publicado). Uso: SHEET_CSV_URL=<enlace> python herramientas/sincronizar.py
import shutil,csv,io,os,re,json,sys,subprocess,unicodedata,urllib.request
from html import escape as E
from PIL import Image,ImageOps,ImageChops
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
PH='https://TU-USUARIO.github.io/boutique-intima'
URL=os.environ.get('SHEET_CSV_URL','').strip();DOM=(os.environ.get('SITIO') or PH).rstrip('/')
def get(u):
    m=re.search(r'drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=)([\w-]+)',u)
    if m:u='https://drive.google.com/uc?export=download&id='+m.group(1)
    return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
def fail(m):print('ERROR:',m);sys.exit(1)
txt=get(URL).decode('utf-8-sig') if URL else open('datos/productos.csv',encoding='utf-8-sig').read()
if txt.lstrip()[:1]=='<':fail('La hoja no está publicada como CSV (Archivo > Compartir > Publicar en la web > CSV).')
na=lambda k:''.join(c for c in unicodedata.normalize('NFD',k.strip().lower()) if not unicodedata.combining(c))
rows=[{na(k):(v or '').strip() for k,v in r.items() if k} for r in csv.DictReader(io.StringIO(txt))]
if not rows or not {'id','nombre','categoria','precio'}<=set(rows[0]):fail('Faltan columnas. Se necesitan: id, nombre, categoria, precio (opcionales: agotado, foto, foto2, descripcion).')
out=[];ids=set();errs=[];new=[0]
PHB=Image.open('img/sin-foto.jpg').convert('RGB') if os.path.exists('img/sin-foto.jpg') else None
def isph(d):  # True si la foto actual es la imagen genérica "Foto próximamente" (se compara por píxeles, no por bytes)
    try:
        if PHB is None or not os.path.exists(d):return False
        im=Image.open(d).convert('RGB');return im.size==PHB.size and ImageChops.difference(PHB,im).getbbox() is None
    except Exception:return False
def photo(u,dest):
    if os.path.exists(dest) and not (u and isph(dest)):return True
    if not u:return False
    try:
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(get(u)))).convert('RGB');im.thumbnail((620,620),Image.LANCZOS)
        im.save(dest,'JPEG',quality=76,optimize=True,progressive=True);new[0]+=1;return True
    except Exception as e:print('AVISO: no se pudo descargar',u,e);return False
def price(v):
    v=re.sub(',','',v) if re.search(r'\d,\d{3}(?!\d)',v) else v.split(',')[0];return int(re.sub(r'\D','',v) or 0)
YES=('si','sí','s','1','true','x','agotado');G={}
for r in rows:
    if not r.get('id') and not r.get('nombre'):continue
    try:i=int(r['id'])
    except Exception:errs.append(f"id inválido: {r.get('id')!r}");continue
    has=bool(r.get('color') or r.get('talla'))
    if i in G:
        g=G[i]
        if not has or not g['v']:errs.append(f'id repetido: {i}');continue
        if (r['nombre'] and r['nombre']!=g['r']['nombre']) or (r['categoria'] and r['categoria']!=g['r']['categoria']):errs.append(f'id {i}: filas con nombre o categoría distintos');continue
        if any(v[0]==r.get('color','') and v[1]==r.get('talla','') for v in g['v']):errs.append(f"id {i}: variante repetida {r.get('color')} {r.get('talla')}");continue
    else:
        if not r['nombre'] or not r['categoria']:errs.append(f'id {i}: falta nombre o categoría');continue
        if re.search(r'[\'"<>&\\]',r['categoria']):errs.append(f'id {i}: la categoría no puede llevar comillas ni símbolos < > & \\');continue
        g=G[i]={'r':r,'v':[],'pr':0}
    u=r.get('und','')
    if has:g['v'].append([r.get('color',''),r.get('talla',''),int(u) if u.isdigit() else None,price(r['precio'])])
    else:g['pr']=price(r['precio'])
for i,g in G.items():
    r=g['r'];vs=g['v']
    if not photo(r.get('foto',''),f'img/p{i}.jpg'):
        if os.path.exists('img/sin-foto.jpg'):shutil.copy('img/sin-foto.jpg',f'img/p{i}.jpg')
        else:print(f'AVISO: id {i} omitido (sin foto)');continue
    photo(r.get('foto2',''),f'img/p{i}b.jpg')
    ag=1 if r.get('agotado','').lower() in YES else 0;pr=min([v[3] for v in vs if v[3]],default=0) if vs else g['pr']
    out.append([i,r['nombre'],r['categoria'],pr,0,1 if ag or (vs and all(v[2]==0 for v in vs)) else 0,r.get('descripcion',''),r.get('referencia',''),vs,ag])
if errs:fail('; '.join(errs))
if len(out)<5:fail('Quedaron menos de 5 productos válidos; no se cambia nada por seguridad.')
buf=io.StringIO();w=csv.writer(buf,lineterminator='\n');w.writerow(['id','nombre','categoria','precio','agotado','foto','foto2','descripcion','referencia','color','talla','und'])
for o in out:
    if o[8]:
        for v in o[8]:w.writerow([o[0],o[1],o[2],v[3],'SI' if o[9] else 'NO','','',o[6],o[7],v[0],v[1],'' if v[2] is None else v[2]])
    else:w.writerow([o[0],o[1],o[2],o[3],'SI' if o[9] else 'NO','','',o[6],o[7],'','',''])
snap=buf.getvalue();old=open('datos/productos.csv',encoding='utf-8-sig').read() if os.path.exists('datos/productos.csv') else ''
dom0=open('datos/sitio.txt').read().strip() if os.path.exists('datos/sitio.txt') else PH
if snap.replace('\r','')==old.replace('\r','') and not new[0] and dom0==DOM and not os.environ.get('FORZAR'):print('Sin cambios');sys.exit(0)
os.makedirs('datos',exist_ok=True);open('datos/productos.csv','w',encoding='utf-8',newline='').write(snap);open('datos/sitio.txt','w').write(DOM)
js=lambda o:json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
cats=[];[cats.append(o[2]) for o in out if o[2] not in cats]
nav='<nav><a href="#productos" onclick="setCat(\'\')">Todo</a>'+''.join(f'<a href="#productos" data-c="{E(c)}" onclick="setCat(this.dataset.c)">{E(c)}</a>' for c in cats)
s=open('index.html',encoding='utf8').read()
for a,b in [(r'const P=\[\[.*?\]\];','const P='+js([o[:6] for o in out])+';'),(r'const V=\{[^\n]*\};','const V='+js({str(o[0]):{'r':o[7],'v':o[8]} for o in out if o[8]})+';'),(r'const CATS=\[.*?\];','const CATS='+js(cats)+';'),(r'const B=new Set\(\[.*?\]\);','const B=new Set('+js(sorted(o[0] for o in out if os.path.exists(f'img/p{o[0]}b.jpg')))+');'),(r'<nav>.*?(?=<a href="#guia")',nav)]:
    s,n=re.subn(a,lambda m:b,s,count=1,flags=re.S)
    if not n:fail('No encontré en index.html: '+a[:30])
if dom0!=DOM:
    s=s.replace(dom0,DOM)
    for f in ('robots.txt','legal.html','404.html'):
        if os.path.exists(f):
            t=open(f,encoding='utf8').read().replace(dom0,DOM)
            if t.strip():open(f,'w',encoding='utf8').write(t)
open('index.html','w',encoding='utf8').write(s)
env={**os.environ,'SITIO':DOM}
for sc in ('generar.py','catalogo.py','qr.py'):subprocess.run([sys.executable,'herramientas/'+sc],check=True,env=env)
print('Tienda actualizada:',len(out),'productos')
