# Genera catalogo-secretos-sensuales.pdf desde la lista P de index.html. Ejecutar de nuevo cuando cambien productos o precios.
import re,json,os,datetime,io
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak,Image as RLI
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
P=json.loads(re.search(r'const P=(\[\[.*?\]\]);',open('index.html',encoding='utf8').read(),re.S).group(1))
ROSE,DARK,GOLD=colors.HexColor('#b0295a'),colors.HexColor('#7d1840'),colors.HexColor('#f4d9a8')
V=json.loads(re.search(r'const V=(\{[^\n]*\});',open('index.html',encoding='utf8').read()).group(1))
W,H=A4;money=lambda n:'$'+f'{n:,}'.replace(',','.')
sn=ParagraphStyle('n',fontName='Helvetica-Bold',fontSize=8.5,leading=10.5,alignment=TA_CENTER,textColor=colors.HexColor('#3b1b29'))
sp=ParagraphStyle('p',fontName='Helvetica-Bold',fontSize=11,leading=13,alignment=TA_CENTER,textColor=ROSE)
sh=ParagraphStyle('h',fontName='Helvetica-Bold',fontSize=15,textColor=colors.white,leading=18)
def img(i):
    im=Image.open(f'img/p{i}.jpg').convert('RGB');im.thumbnail((330,330));c=Image.new('RGB',(330,330),'white');c.paste(im,((330-im.width)//2,(330-im.height)//2))
    b=io.BytesIO();c.save(b,'JPEG',quality=70);b.seek(0);return RLI(b,width=44*mm,height=44*mm)
def deco(c,d):
    if d.page==1:
        c.setFillColor(colors.HexColor('#1f1d22'));c.rect(0,0,W,H,fill=1,stroke=0)
        c.drawImage('logo.jpg',W/2-60*mm,H/2-30*mm,120*mm,120*mm);c.setFillColor(GOLD);c.setFont('Helvetica-Bold',26);c.drawCentredString(W/2,H/2-45*mm,'Catálogo de productos')
        c.setFont('Helvetica',12);c.drawCentredString(W/2,H/2-56*mm,f'Actualizado: {datetime.date.today():%d/%m/%Y}  ·  WhatsApp 322 464 9334');c.drawCentredString(W/2,H/2-64*mm,'Solo para mayores de 18 años')
    else:
        c.setFillColor(DARK);c.rect(0,0,W,11*mm,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica',7.5)
        c.drawString(12*mm,4*mm,'Secretos Sensuales · Boutique Íntima · WhatsApp 322 464 9334 · Precios sujetos a cambio · Solo mayores de 18 años');c.drawRightString(W-12*mm,4*mm,f'Pág. {d.page}')
doc=BaseDocTemplate('catalogo-secretos-sensuales.pdf',pagesize=A4,title='Catálogo Secretos Sensuales - Boutique Íntima',author='Boutique Íntima')
doc.addPageTemplates(PageTemplate(frames=[Frame(12*mm,14*mm,W-24*mm,H-26*mm,id='f')],onPage=deco))
S=[PageBreak()];cats=[]
for p in P:
    if p[2] not in cats:cats.append(p[2])
for c in cats:
    items=[p for p in P if p[2]==c];hd=(Table([[Paragraph(c,sh)]],colWidths=[W-24*mm],style=[('BACKGROUND',(0,0),(-1,-1),ROSE),('LEFTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),6)]),Spacer(1,3*mm))
    for k in range(0,len(items),4):
        row=[]
        for p in items[k:k+4]:
            pr='Agotado' if p[5] else (('Desde ' if str(p[0]) in V else '')+money(p[3]) if p[3] else 'Consultar precio')
            row.append([img(p[0]),Spacer(1,1.5*mm),Paragraph(p[1].replace('&','&amp;'),sn),Spacer(1,1*mm),Paragraph(pr,sp)])
        row+=[''] * (4-len(row))
        T=(Table([row],colWidths=[(W-24*mm)/4]*4,style=[('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.3,colors.HexColor('#f0d5e0')),('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#f0d5e0')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        S.append(KeepTogether(list(hd)+[T]) if k==0 else T)
    S.append(Spacer(1,6*mm))
doc.build(S);print(len(P),'productos,',len(cats),'categorías')
