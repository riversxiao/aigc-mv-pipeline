"""Runtime-local release only after exact Drive API verification of the batch."""
import argparse,hashlib,json,time,urllib.parse,urllib.request,uuid
from pathlib import Path


def api(path, data=None, content_type=None):
    token_request=urllib.request.Request('http://127.0.0.1:8012/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
    token=json.loads(urllib.request.urlopen(token_request,timeout=5).read())['access_token']
    headers={'Authorization':'Bearer '+token}
    if content_type:headers['Content-Type']=content_type
    request=urllib.request.Request('https://www.googleapis.com/'+path,data=data,headers=headers)
    return json.loads(urllib.request.urlopen(request,timeout=15).read())


def children(parent):
    rows=[];page=None
    while True:
        params={'q':f"trashed=false and '{parent}' in parents",'pageSize':1000,'fields':'nextPageToken,files(id,name,size,md5Checksum,mimeType)'}
        if page:params['pageToken']=page
        result=api('drive/v3/files?'+urllib.parse.urlencode(params));rows+=result.get('files',[])
        page=result.get('nextPageToken')
        if not page:return rows


def release(bundle, output, parent, allow_partial=False):
    manifest=json.loads((bundle/'manifest.json').read_text())
    if not (output/'state.json').exists() and allow_partial:
        (output/'state.json').write_text(json.dumps({'jobs':{}}))
    state=json.loads((output/'state.json').read_text())
    expected=[]
    pending=[]
    completed=0
    for job in manifest['jobs']:
        record=state['jobs'].get(job['job_id'],{})
        if record.get('status')!='complete':
            if not allow_partial:raise RuntimeError('Cannot release an incomplete batch as complete')
            pending.append(job['job_id']);continue
        completed+=1
        expected+=record['files']
    expected += [{'file':p.name,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in [output/'state.json',output/'pipeline_status.json']]
    for item in expected:
        path=output/item['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Local result changed')
        item['md5']=hashlib.md5(path.read_bytes()).hexdigest()
    deadline=time.monotonic()+120
    while True:
        folders=[r for r in children(parent) if r['name']=='results']
        rows=children(folders[0]['id']) if len(folders)==1 else []
        by_name={r['name']:r for r in rows}
        if all(int(by_name.get(f['file'],{}).get('size',0))==f['size'] and by_name.get(f['file'],{}).get('md5Checksum')==f['md5'] for f in expected):break
        if time.monotonic()>=deadline:raise TimeoutError('Drive persistence not yet verified; watchdog remains armed')
        time.sleep(3)
    receipt={'status':'partial_results_verified_release_requested' if pending else 'all_results_verified_release_requested',
             'completed_jobs':completed,'pending_jobs':pending,
             'verified_files':expected,'release_requested_at':time.time(),'runtime_local_only':True}
    raw=json.dumps(receipt,indent=2).encode();boundary='h3_'+uuid.uuid4().hex
    meta=json.dumps({'name':'cloud_release.json','parents':[parent]}).encode()
    body=(f'--{boundary}\r\nContent-Type: application/json\r\n\r\n'.encode()+meta+
          f'\r\n--{boundary}\r\nContent-Type: application/json\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
    result=api('upload/drive/v3/files?uploadType=multipart&fields=id,size,md5Checksum',body,'multipart/related; boundary='+boundary)
    if int(result['size'])!=len(raw) or result['md5Checksum']!=hashlib.md5(raw).hexdigest():raise RuntimeError('Release receipt upload was not verified')
    print('DRIVE_VERIFIED_RELEASING_OWN_RUNTIME',flush=True)
    from google.colab import runtime
    runtime.unassign()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--parent',required=True);parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args();release(args.bundle,args.out,args.parent,args.allow_partial)
