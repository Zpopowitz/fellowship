import sys,os,json,hashlib,datetime,subprocess
ROOT=r'C:\Users\dalvesbarretoneto1\Desktop\Claude\Sessions\boston_data'
LOG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'dl_log.jsonl')
def dl(folder,url,name):
    d=os.path.join(ROOT,folder);os.makedirs(d,exist_ok=True)
    p=os.path.join(d,name)
    rec=dict(folder=folder,file=name,url=url,date=datetime.date.today().isoformat())
    r=subprocess.run(['curl','-sS','-L','-m','1800','-o',p,'-w','%{http_code}',url],capture_output=True,text=True)
    rec['http']=r.stdout.strip();rec['stderr']=r.stderr.strip()
    if r.returncode==0 and rec['http']=='200' and os.path.exists(p):
        h=hashlib.sha256(open(p,'rb').read()).hexdigest()
        rec.update(size=os.path.getsize(p),sha256=h,status='ok')
    else:
        rec.update(status='FAILED',error=f"curl rc={r.returncode} http={rec['http']} {rec['stderr']}")
        if os.path.exists(p): os.remove(p)
    open(LOG,'a').write(json.dumps(rec)+'\n');print(rec['status'],folder,name,rec.get('size'),rec.get('error',''))
if __name__=='__main__':
    for line in open(sys.argv[1]):
        line=line.strip()
        if line: dl(*line.split('|'))
