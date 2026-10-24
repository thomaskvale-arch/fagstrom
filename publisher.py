"""Local Fagstraum editor. Authentication stays in GitHub CLI's credential store."""
import base64
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import uuid
import webbrowser
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
import tkinter as tk
from tkinter import ttk, messagebox

REPO='thomaskvale-arch/fagstrom'
SITE='https://thomaskvale-arch.github.io/fagstrom/'
TOPICS={'ki':'KI i praksis','digitalisering':'Digitalisering','kompetanse':'Kompetanse'}
DRAFT=Path(os.environ.get('LOCALAPPDATA','.'))/'Fagstraum'/'utkast.json'

def validate(entry):
    if not entry['title'].strip():raise ValueError('Skriv ein tittel.')
    if not entry['summary'].strip():raise ValueError('Skriv ein kort omtale.')
    url=urlsplit(entry['url'])
    if url.scheme not in ('http','https') or not url.hostname or url.username or url.password:
        raise ValueError('Bruk ei full kjeldelenkje med https://, utan innloggingsopplysningar.')
    if not entry['topics'] or not set(entry['topics'])<=set(TOPICS):raise ValueError('Vel minst eitt tema.')

def api(method, payload=None):
    gh=shutil.which('gh') or r'C:\Program Files\GitHub CLI\gh.exe'
    args=[gh,'api','--method',method,f'repos/{REPO}/contents/entries.json']
    if payload is not None:args+=['--input','-']
    result=subprocess.run(args,input=json.dumps(payload) if payload is not None else None,
        encoding='utf-8',capture_output=True,timeout=60,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise RuntimeError('GitHub avviste førespurnaden. Kontroller innlogging og nett. Ved samtidige endringar: prøv igjen. Utkastet er bevart.')
    return json.loads(result.stdout)

def publish(entry, call=api):
    validate(entry)
    current=call('GET')
    entries=json.loads(base64.b64decode(current['content']).decode('utf-8'))
    for old in entries:
        if old['id']==entry['id']:
            if any(old.get(k)!=entry.get(k) for k in ('title','summary','url','topics')):
                raise ValueError('Dette utkastet er allereie publisert med anna innhald. Opne nettsida for kontroll; lag eit nytt funn om nødvendig.')
            return 'Innlegget finst allereie på GitHub. Ingen duplikat vart oppretta.'
    now=datetime.now(timezone.utc).replace(microsecond=0)
    latest=max((datetime.fromisoformat(e['published']) for e in entries),default=now-timedelta(seconds=1))
    if latest>=now:now=latest+timedelta(seconds=1)
    record=dict(entry,published=now.isoformat())
    entries.append(record)
    content=base64.b64encode((json.dumps(entries,ensure_ascii=False,indent=2)+'\n').encode('utf-8')).decode('ascii')
    call('PUT',dict(message='Publiser fagleg funn: '+entry['title'][:100],content=content,sha=current['sha'],branch='main'))
    return 'Innlegget er lagra på GitHub. Nettsida og RSS blir no bygde. Teams kjem ved neste RSS-sjekk.'

class Publisher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Fagstraum – nytt funn')
        self.geometry('780x680');self.minsize(620,560)
        self.busy=False;self.events=queue.Queue();self.entry_id=uuid.uuid4().hex
        panel=ttk.Frame(self,padding=22);panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='Eit nytt fagleg funn',font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(panel,text='Publiser ei eiga omtale og lenkje til kjelda. Innlegget blir offentleg.',wraplength=680).pack(anchor='w',pady=(6,18))
        self.title_value=tk.StringVar();self.url_value=tk.StringVar()
        self.inputs=[]
        for label,value in [('Tittel',self.title_value),('Kjeldelenkje (https://…)',self.url_value)]:
            ttk.Label(panel,text=label).pack(anchor='w')
            widget=ttk.Entry(panel,textvariable=value);widget.pack(fill='x',pady=(3,12));self.inputs.append(widget)
        ttk.Label(panel,text='Di korte omtale – kvifor er dette interessant?').pack(anchor='w')
        self.summary=tk.Text(panel,height=7,wrap='word',font=('Segoe UI',11),undo=True)
        self.summary.pack(fill='both',expand=True,pady=(4,12))
        ttk.Label(panel,text='Tema (innlegget kjem også i «Alt nytt»)').pack(anchor='w')
        topics=ttk.Frame(panel);topics.pack(fill='x',pady=8)
        self.topics={k:tk.BooleanVar() for k in TOPICS}
        for k,label in TOPICS.items():
            widget=ttk.Checkbutton(topics,text=label,variable=self.topics[k]);widget.pack(side='left',padx=(0,15));self.inputs.append(widget)
        bar=ttk.Frame(panel);bar.pack(fill='x',pady=12)
        self.save_button=ttk.Button(bar,text='Lagre utkast',command=self.save_draft);self.save_button.pack(side='left')
        self.publish_button=ttk.Button(bar,text='Sjå over og publiser …',command=self.preview);self.publish_button.pack(side='right')
        links=ttk.Frame(panel);links.pack(fill='x')
        ttk.Button(links,text='Opne nettsida',command=lambda:webbrowser.open(SITE)).pack(side='left')
        ttk.Button(links,text='Sjå publiseringsstatus',command=lambda:webbrowser.open('https://github.com/'+REPO+'/actions')).pack(side='left',padx=8)
        self.status=tk.StringVar(value='Utkast blir lagra lokalt. Berre «Publiser offentleg» sender innhaldet til GitHub.')
        ttk.Label(panel,textvariable=self.status,wraplength=700).pack(anchor='w',pady=12)
        if DRAFT.exists():
            try:
                d=json.loads(DRAFT.read_text(encoding='utf-8'));self.entry_id=d['id']
                self.title_value.set(d.get('title',''));self.url_value.set(d.get('url',''));self.summary.insert('1.0',d.get('summary',''))
                for k,v in self.topics.items():v.set(k in d.get('topics',[]))
                self.status.set('Tidlegare utkast er opna.')
            except (OSError,ValueError,KeyError):self.status.set('Kunne ikkje lese tidlegare utkast. Fila er bevart.')
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.after(200,self.poll)

    def entry(self):
        return dict(id=self.entry_id,title=self.title_value.get().strip(),url=self.url_value.get().strip(),
                    summary=self.summary.get('1.0','end').strip(),topics=[k for k,v in self.topics.items() if v.get()])

    def save_draft(self):
        try:
            DRAFT.parent.mkdir(parents=True,exist_ok=True)
            temporary=DRAFT.with_suffix('.tmp');temporary.write_text(json.dumps(self.entry(),ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temporary,DRAFT)
            self.status.set('Utkast lagra på denne maskina.')
            return True
        except OSError:
            messagebox.showerror('Utkast','Kunne ikkje lagre utkastet.',parent=self);return False

    def preview(self):
        entry=self.entry()
        try:validate(entry)
        except ValueError as e:messagebox.showinfo('Manglar informasjon',str(e),parent=self);return
        if not self.save_draft():return
        window=tk.Toplevel(self);window.title('Sjå over før publisering');window.geometry('660x500');window.transient(self);window.grab_set()
        text=tk.Text(window,wrap='word',font=('Segoe UI',11),padx=18,pady=18)
        text.pack(fill='both',expand=True)
        text.insert('1.0',entry['title']+'\n\n'+entry['summary']+'\n\n'+entry['url']+'\n\nTema: '+', '.join(TOPICS[k] for k in entry['topics'])+'\n\nDette blir offentleg og kan utløyse Teams-varsling.')
        text.configure(state='disabled')
        buttons=ttk.Frame(window,padding=12);buttons.pack(fill='x')
        ttk.Button(buttons,text='Tilbake',command=window.destroy).pack(side='left')
        def send():
            window.destroy();self.busy=True
            for widget in self.inputs+[self.save_button,self.publish_button]:widget.state(['disabled'])
            self.summary.configure(state='disabled');self.status.set('Sender til GitHub …')
            def work():
                try:self.events.put((True,publish(entry)))
                except Exception as error:self.events.put((False,str(error)+' Utkastet er bevart. Ved uviss sending kan du prøve igjen med same utkast.'))
            threading.Thread(target=work,daemon=True).start()
        ttk.Button(buttons,text='Publiser offentleg',command=send).pack(side='right')

    def poll(self):
        try:
            success,message=self.events.get_nowait();self.busy=False
            for widget in self.inputs+[self.save_button,self.publish_button]:widget.state(['!disabled'])
            self.summary.configure(state='normal')
            if success:
                self.entry_id=uuid.uuid4().hex;self.title_value.set('');self.url_value.set('');self.summary.delete('1.0','end')
                for value in self.topics.values():value.set(False)
                self.save_draft()
            self.status.set(message)
        except queue.Empty:pass
        self.after(200,self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('Publiserer','Vent til sendinga er ferdig før du lukkar.',parent=self);return
        if self.save_draft():self.destroy()

if __name__=='__main__':Publisher().mainloop()
