# Cambia el WhatsApp en TODO el sitio. Uso:  python herramientas/cambiar_telefono.py 3001234567
import re,sys,os,glob,subprocess
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
n=re.sub(r'\D','',sys.argv[1] if len(sys.argv)>1 else '');n=n[-10:]
if len(n)!=10 or n[0]!='3':sys.exit('Escribe el celular de 10 dígitos que empieza por 3, por ejemplo 3001234567')
old=open('datos/telefono.txt').read().strip() if os.path.exists('datos/telefono.txt') else '3226469334'
fm=lambda x:f'{x[:3]} {x[3:6]} {x[6:]}'
files=['index.html','legal.html','404.html','herramientas/generar.py','herramientas/catalogo.py','herramientas/plantilla.html']
c=0
for f in files:
    if not os.path.exists(f):continue
    t=open(f,encoding='utf8').read();u=t.replace('57'+old,'57'+n).replace(fm(old),fm(n)).replace(old,n)
    if u!=t:open(f,'w',encoding='utf8').write(u);c+=1
open('datos/telefono.txt','w').write(n)
env={**os.environ}
for sc in ('generar.py','catalogo.py'):subprocess.run([sys.executable,'herramientas/'+sc],check=True,env=env)
left=[f for f in glob.glob('**/*.html',recursive=True)+glob.glob('herramientas/*.py') if old in open(f,encoding='utf8').read() and 'cambiar_telefono' not in f]
print(f'Listo: {old} -> {n} en {c} archivos.','Quedan con el número viejo:',left or 'ninguno')
