# Genera WebP, una página por producto, datos estructurados y sitemap a partir de la lista P de index.html.
import re,json,unicodedata,os,glob
from html import escape as E
from PIL import Image
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
DOM=(os.environ.get('SITIO') or 'https://TU-USUARIO.github.io/boutique-intima').rstrip('/')
s=open('index.html',encoding='utf8').read()
P=json.loads(re.search(r'const P=(\[\[.*?\]\]);',s,re.S).group(1))
def slug(n):
    n=unicodedata.normalize('NFD',n.lower());n=''.join(c for c in n if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','-',n).strip('-')
import csv
D={}
if os.path.exists('datos/productos.csv'):
    for r in csv.DictReader(open('datos/productos.csv',encoding='utf-8-sig')):
        try:D[int(r['id'])]=(r.get('descripcion') or '').strip()
        except Exception:pass
VV=json.loads(re.search(r'const V=(\{[^\n]*\});',s).group(1))
money=lambda n:'$'+f'{n:,}'.replace(',','.')
for f in glob.glob('img/p*.jpg'):
    Image.open(f).convert('RGB').save(f[:-4]+'.webp','WEBP',quality=72,method=6)
T=open('herramientas/plantilla.html',encoding='utf8').read()
for f in glob.glob('producto/*.html'): os.remove(f)
urls=[]
for p in P:
    i,n,c,pr,_,so=p;u=f'producto/{i}-{slug(n)}.html';urls.append(u)
    same=[q for q in P if q[2]==c and q[0]!=i];k=sum(1 for q in same if q[0]<i);rel=(same[k:]+same[:k])[:4]
    relh=''.join(f'<a class="rc" href="{q[0]}-{slug(q[1])}.html"><picture><source srcset="../img/p{q[0]}.webp" type="image/webp"><img src="../img/p{q[0]}.jpg" alt="{E(q[1])}" width="160" height="160" loading="lazy"></picture><span>{E(q[1])}</span><b>{money(q[3]) if q[3] else "Consultar precio"}</b></a>' for q in rel)
    ld={"@context":"https://schema.org","@type":"Product","name":n,"category":c,"image":f"{DOM}/img/p{i}.jpg","brand":{"@type":"Brand","name":"Boutique Íntima"}}
    if pr: ld["offers"]={"@type":"Offer","priceCurrency":"COP","price":pr,"availability":"https://schema.org/"+("OutOfStock" if so else "InStock"),"url":f"{DOM}/{u}"}
    dsc=D.get(i,'');vv=VV.get(str(i));varh=''
    if vv:varh=(f'<p class="c">Ref. {E(vv["r"])}</p>' if vv['r'] else '')+'<table class="vt"><tr><th>Color</th><th>Talla</th><th>Precio</th><th></th></tr>'+''.join(f'<tr><td>{E(x[0])}</td><td>{E(x[1])}</td><td>{money(x[3]) if x[3] else "Por confirmar"}</td><td>{"Agotado" if x[2]==0 else "Disponible"}</td></tr>' for x in vv['v'])+'</table>'
    desc=dsc[:155] if dsc else f'{n}: {c.lower()} en Boutique Íntima'+(f' por {money(pr)} COP' if pr else '')+'. Pídelo por WhatsApp. Solo mayores de 18 años.'
    if vv and not dsc:desc=n+(f" (Ref. {vv['r']})" if vv['r'] else '')+f": {c.lower()} en Boutique Íntima. Tallas: "+', '.join(sorted({x[1] for x in vv['v']}))+'. Pídela por WhatsApp. Solo mayores de 18 años.'
    h=T
    for a,b in {'@@TITLE@@':E(n),'@@DESC@@':E(desc),'@@URL@@':f'{DOM}/{u}','@@ID@@':str(i),'@@NAME@@':E(n),'@@CAT@@':E(c),
        '@@PRICE@@':('Desde ' if vv and pr else '')+(money(pr) if pr else 'Consultar precio'),'@@JSON@@':json.dumps(ld,ensure_ascii=False).replace('</','<\\/'),'@@REL@@':relh,'@@TXT@@':(f'<p>{E(dsc)}</p>' if dsc else '')+varh,'@@IMG2@@':(f'<div class="im" style="margin-top:14px"><picture><source srcset="../img/p{i}b.webp" type="image/webp"><img src="../img/p{i}b.jpg" alt="{E(n)} (otra vista)" width="640" height="640" loading="lazy"></picture></div>' if os.path.exists(f'img/p{i}b.jpg') else ''),'@@REL_T@@':'Productos relacionados' if rel else '',
        '@@ACT@@':('<p class="so">😔 Agotado por ahora</p>' if so else ((f'<a class="b" href="../index.html?resenas={i}">Elegir talla y color</a>' if vv else f'<a class="b" href="../index.html?add={i}">Lo deseo</a>') if pr else ''))+('' if so else '<a class="b o" id="wa" target="_blank" rel="noopener" href="https://wa.me/573224649334">'+('Pedir por WhatsApp' if pr else 'Consultar precio por WhatsApp')+'</a>')}.items(): h=h.replace(a,b)
    open(u,'w',encoding='utf8').write(h)
open('sitemap.xml','w',encoding='utf8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{DOM}/{x}</loc></url>' for x in ['','legal.html']+urls)+'</urlset>\n')
print(len(urls),'páginas')
