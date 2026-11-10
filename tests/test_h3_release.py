"""Cloud release must fail closed when preserved outputs are incomplete."""
import hashlib,json
import pytest
from aigc_mv import h3_cloud_release as release


def test_incomplete_batch_never_attempts_cloud_release(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';out=tmp_path/'results';bundle.mkdir();out.mkdir()
    (bundle/'manifest.json').write_text(json.dumps({'jobs':[{'job_id':'one'}]}))
    (out/'state.json').write_text(json.dumps({'jobs':{'one':{'status':'queued'}}}))
    calls=[];monkeypatch.setattr(release,'api',lambda *a,**k:calls.append(a))
    with pytest.raises(RuntimeError,match='incomplete'):
        release.release(bundle,out,'task-parent')
    assert calls==[]


def test_cloud_md5_mismatch_prevents_release_even_when_size_matches(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';out=tmp_path/'results';bundle.mkdir();out.mkdir()
    raw=b'important clip';(out/'raw.mp4').write_bytes(raw)
    record={'status':'complete','files':[{'file':'raw.mp4','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}
    (bundle/'manifest.json').write_text(json.dumps({'jobs':[{'job_id':'one'}]}))
    (out/'state.json').write_text(json.dumps({'jobs':{'one':record}}));(out/'pipeline_status.json').write_text('{"status":"complete"}')
    rows=[{'name':p.name,'size':str(p.stat().st_size),'md5Checksum':hashlib.md5(p.read_bytes()).hexdigest()} for p in out.iterdir()]
    next(r for r in rows if r['name']=='raw.mp4')['md5Checksum']='wrong-md5'
    monkeypatch.setattr(release,'children',lambda parent:[{'name':'results','id':'result-folder'}] if parent=='task-parent' else rows)
    ticks=iter([0,121]);monkeypatch.setattr(release.time,'monotonic',lambda:next(ticks))
    calls=[];monkeypatch.setattr(release,'api',lambda *a,**k:calls.append(a))
    with pytest.raises(TimeoutError,match='persistence'):
        release.release(bundle,out,'task-parent')
    assert calls==[]


def test_failed_batch_releases_only_after_preserving_partial_results(tmp_path,monkeypatch):
    import sys
    from types import ModuleType,SimpleNamespace as NS
    bundle=tmp_path/'bundle';out=tmp_path/'results';bundle.mkdir();out.mkdir()
    raw=b'completed before failure';(out/'raw.mp4').write_bytes(raw)
    record={'status':'complete','files':[{'file':'raw.mp4','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}
    (bundle/'manifest.json').write_text(json.dumps({'jobs':[{'job_id':'one'},{'job_id':'two'}]}))
    (out/'state.json').write_text(json.dumps({'jobs':{'one':record,'two':{'status':'failed'}}}))
    (out/'pipeline_status.json').write_text('{"status":"failed"}')
    rows=[{'name':p.name,'size':str(p.stat().st_size),'md5Checksum':hashlib.md5(p.read_bytes()).hexdigest()} for p in out.iterdir()]
    monkeypatch.setattr(release,'children',lambda parent:[{'name':'results','id':'result-folder'}] if parent=='task-parent' else rows)
    receipts=[]
    def upload(path,data=None,content_type=None):
        raw=data.split(b'Content-Type: application/json\r\n\r\n')[2].split(b'\r\n--',1)[0]
        receipts.append(json.loads(raw))
        return {'id':'receipt','size':str(len(raw)),'md5Checksum':hashlib.md5(raw).hexdigest()}
    monkeypatch.setattr(release,'api',upload)
    stopped=[];google=ModuleType('google');colab=ModuleType('google.colab');colab.runtime=NS(unassign=lambda:stopped.append(True))
    monkeypatch.setitem(sys.modules,'google',google);monkeypatch.setitem(sys.modules,'google.colab',colab)
    release.release(bundle,out,'task-parent',allow_partial=True)
    assert stopped==[True] and len(receipts)==1
    assert receipts[0]['completed_jobs']==1 and receipts[0]['pending_jobs']==['two']
    assert receipts[0]['status']=='partial_results_verified_release_requested'
    assert (out/'raw.mp4').read_bytes()==raw
