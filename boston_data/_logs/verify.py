import csv,json,os,sys,zipfile,io,struct
csv.field_size_limit(1<<30)
R=r'C:\Users\dalvesbarretoneto1\Desktop\Claude\Sessions\boston_data'
out={}
for fo in sorted(os.listdir(R)):
    d=os.path.join(R,fo)
    if not os.path.isdir(d) or fo.startswith('.'): continue
    for f in sorted(os.listdir(d)):
        p=os.path.join(d,f);info={'size':os.path.getsize(p)}
        try:
            if f.endswith('.csv'):
                with open(p,newline='',encoding='utf-8-sig',errors='replace') as fh:
                    r=csv.reader(fh);h=next(r);n=sum(1 for _ in r)
                info.update(kind='csv',cols=h,rows=n)
            elif f.endswith('.geojson'):
                j=json.load(open(p,encoding='utf-8'));ft=j['features']
                keys=list(ft[0]['properties'].keys()) if ft else []
                info.update(kind='geojson',rows=len(ft),cols=keys,geom=ft[0]['geometry']['type'] if ft and ft[0].get('geometry') else None)
            elif f.endswith('.zip'):
                z=zipfile.ZipFile(p);info['kind']='zip';info['members']=[(i.filename,i.file_size) for i in z.infolist()]
                for i in z.infolist():
                    if i.filename.lower().endswith('.dbf'):
                        b=z.read(i);n,hl,rl=struct.unpack('<xxxxIHH',b[:12]);q=32;fl=[]
                        while b[q]!=0x0D: fl.append(b[q:q+11].split(b'\0')[0].decode());q+=32
                        info.update(rows=n,cols=fl)
                    if i.filename.lower().endswith('.geojson') or i.filename.lower().endswith('.json'):
                        j=json.loads(z.read(i));ft=j['features'];info.update(rows=len(ft),cols=list(ft[0]['properties'].keys()))
            else: info['kind']='other'
        except Exception as e: info['error']=repr(e)
        out[f'{fo}/{f}']=info
json.dump(out,open('verify.json','w'),indent=1)
for k,v in out.items():
    print(k,v.get('kind'),'size',v['size'],'rows',v.get('rows'),'ERR' if 'error' in v else '')
    if v.get('cols'): print('   cols:',v['cols'])
    if v.get('members'): print('   members:',v['members'])
    if 'error' in v: print('   ',v['error'])
