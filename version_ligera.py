# Crea index-ligero.html: la misma página SIN comentarios (carga un poco más rápido).
# Uso: python herramientas/version_ligera.py   -> luego sube index-ligero.html con el nombre index.html
import re,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
s=open('index.html',encoding='utf8').read()
s=re.sub(r'/\* .*? \*/','',s,flags=re.S);s=re.sub(r'<!-- ▼ .*? -->\n','',s);s=re.sub(r'\n\s*\n','\n',s)
open('index-ligero.html','w',encoding='utf8').write(s);print('Listo: index-ligero.html',len(s)//1024,'KB')
