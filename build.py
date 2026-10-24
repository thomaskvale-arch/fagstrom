import json, html, os
from pathlib import Path
from datetime import datetime, timezone
from email.utils import format_datetime
import xml.etree.ElementTree as ET

BASE=os.environ.get('SITE_URL','https://thomaskvale-arch.github.io/fagstrom').rstrip('/')
TOPICS={'ki':'KI i praksis','digitalisering':'Digitalisering','kompetanse':'Kompetanse'}
entries=json.loads(Path('entries.json').read_text(encoding='utf-8'))
ids=set();dates=set()
for e in entries:
    assert e['id'] and e['id'] not in ids,'ID må vere unik';ids.add(e['id'])
    e['_date']=datetime.fromisoformat(e['published'])
    assert e['_date'].tzinfo,'Tidspunkt må ha tidssone'
    assert e['_date'] not in dates,'Bruk ulike publiseringstidspunkt for RSS-varsling';dates.add(e['_date'])
    assert e['url'].startswith(('https://','http://'))
    assert e['title'].strip() and e['summary'].strip()
    assert e['topics'] and set(e['topics'])<=set(TOPICS)
entries.sort(key=lambda e:e['_date'],reverse=True)
out=Path('_site');out.mkdir(exist_ok=True)
(out/'feeds').mkdir(exist_ok=True)
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
for topic,name in {'all':'Alt nytt',**TOPICS}.items():
    rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
    for key,value in {'title':'Fagstraum – '+name,'link':BASE+'/','description':'Utvalde faglege funn, korte omtalar og lenkjer til originalkjeldene.','language':'nn'}.items():ET.SubElement(channel,key).text=value
    ET.SubElement(channel,'{http://www.w3.org/2005/Atom}link',href=BASE+'/feeds/'+topic+'.xml',rel='self',type='application/rss+xml')
    for e in entries:
        if topic!='all' and topic not in e['topics']:continue
        item=ET.SubElement(channel,'item')
        for key,value in {'title':e['title'],'link':e['url'],'description':e['summary'],'pubDate':format_datetime(e['_date'].astimezone(timezone.utc),usegmt=True)}.items():ET.SubElement(item,key).text=value
        ET.SubElement(item,'guid',isPermaLink='false').text='fagstrom:'+e['id']
        for t in e['topics']:ET.SubElement(item,'category').text=TOPICS[t]
    ET.ElementTree(rss).write(out/'feeds'/f'{topic}.xml',encoding='utf-8',xml_declaration=True)
esc=html.escape
cards=''.join(f'<article><p class="meta">{e["_date"]:%d.%m.%Y} · {esc(" / ".join(TOPICS[t] for t in e["topics"]))}</p><h2><a href="{esc(e["url"],quote=True)}">{esc(e["title"])}</a></h2><p>{esc(e["summary"])}</p><a class="source" href="{esc(e["url"],quote=True)}">Les originalkjelda ↗</a></article>' for e in entries)
links=''.join(f'<a class="feed" href="feeds/{key}.xml">{esc(name)} <span>RSS ↗</span></a>' for key,name in {'all':'Alt nytt',**TOPICS}.items())
page='''<!doctype html><html lang="nn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fagstraum – utvalde funn</title><link rel="alternate" type="application/rss+xml" title="Alt nytt" href="feeds/all.xml"><style>
*{box-sizing:border-box}body{margin:0;background:#f5f3ed;color:#183537;font:17px/1.65 system-ui,sans-serif}main{max-width:1040px;margin:auto;padding:56px 24px}header{border-bottom:1px solid #cad2cb;padding-bottom:32px}.eyebrow{font-size:13px;text-transform:uppercase;letter-spacing:.15em;color:#55716a}h1{font-size:clamp(40px,8vw,76px);line-height:1.1;letter-spacing:-.05em;margin:18px 0}header p{max-width:650px}a{color:#166c5c}h2{line-height:1.3;font-size:24px}h2 a{text-decoration:none}.feeds{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:32px 0}.feed{background:#fff;padding:18px;border:1px solid #d4dcd5;border-radius:10px;text-decoration:none;font-weight:600}.feed span{display:block;font-size:12px;color:#64746d;margin-top:8px}article{background:#fff;border:1px solid #d4dcd5;border-radius:12px;padding:24px;margin:18px 0}.meta,footer{font-size:13px;color:#5c706b}.source{font-size:14px}.empty{padding:36px;border:1px dashed #9bafa4;border-radius:12px}footer{margin-top:48px}a:focus-visible{outline:3px solid #bc702a;outline-offset:4px}</style></head><body><main><header><div class="eyebrow">Thomas si faglege leseliste</div><h1>Fagstraum.</h1><p>Utvalde funn om kunstig intelligens, digitalisering og læring. Korte omtalar, med lenkjer vidare til originalkjeldene.</p></header><nav class="feeds" aria-label="RSS-straumar">'''+links+'''</nav><h2>Siste funn</h2>'''+(cards or '<p class="empty">Straumen er klar. Ingen funn er publiserte enno.</p>')+'''<footer>Offentleg lenkjesamling · Følg eit tema med RSS, eller kopier RSS-adressa til varslingsløysinga di.</footer></main></body></html>'''
(out/'index.html').write_text(page,encoding='utf-8')
(out/'.nojekyll').touch()
print(f'Bygde nettside og fire RSS-straumar med {len(entries)} innlegg.')
