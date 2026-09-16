"""Offline read-only audit of the archived laboratory 3DGS files.

Usage: python inspect_historical.py --map source-map.json --out .
The private map holds machine-specific paths; generated statistics use source IDs.
"""
import argparse, collections, hashlib, json, sqlite3, struct
from pathlib import Path
import numpy as np
from PIL import Image
ap=argparse.ArgumentParser();ap.add_argument('--map',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(); sources=json.loads(Path(a.map).read_text(encoding='utf-8'))['sources'];out=Path(a.out)
out.mkdir(parents=True,exist_ok=True)
def dump(name,x): (out/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def src(id): return Path(sources[id]['path'])
def read(f,fmt): return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
def stats(x):
    x=np.array(x);return {'count':len(x),'min':float(x.min()),'mean':float(x.mean()),
                          'median':float(np.median(x)),'p95':float(np.quantile(x,.95)), 'max':float(x.max())}
def cameras(p):
    names={0:('SIMPLE_PINHOLE',3),1:('PINHOLE',4),2:('SIMPLE_RADIAL',4),3:('RADIAL',5),4:('OPENCV',8),5:('OPENCV_FISHEYE',8)}
    rows=[]
    with open(p,'rb') as f:
        for _ in range(read(f,'Q')[0]):
            id,kind,w,h=read(f,'iiQQ');name,n=names[kind]
            rows.append({'id':id,'model':name,'width':w,'height':h,'params':read(f,'d'*n)})
        assert not f.read(1)
    return rows
def images(p):
    rows=[]
    with open(p,'rb') as f:
        for _ in range(read(f,'Q')[0]):
            data=read(f,'idddddddi');name=bytearray()
            while (ch:=f.read(1))!=b'\0':
                if not ch: raise EOFError
                name.extend(ch)
            n=read(f,'Q')[0];points=np.frombuffer(f.read(24*n),dtype=[('x','<f8'),('y','<f8'),('id','<i8')])
            rows.append({'image_id':data[0],'camera_id':data[-1],'name':name.decode(),
                         'keypoints':n,'triangulated_observations':int(np.sum(points['id']>=0))})
        assert not f.read(1)
    return rows
def points(p):
    xyz=[];errors=[];tracks=[]
    with open(p,'rb') as f:
        for _ in range(read(f,'Q')[0]):
            data=read(f,'QdddBBBd');xyz.append(data[1:4]);errors.append(data[-1]);n=read(f,'Q')[0];tracks.append(n);f.seek(8*n,1)
        assert not f.read(1)
    return {'points':len(xyz),'reprojection_error_pixels':stats(errors),'track_length':stats(tracks),
            'xyz_min':np.min(xyz,axis=0).tolist(),'xyz_max':np.max(xyz,axis=0).tolist()}
def ply(p):
    header=[]
    with open(p,'rb') as f:
        while True:
            s=f.readline().decode('ascii').strip();header.append(s)
            if s=='end_header':break
        offset=f.tell()
    n=int(next(s.split()[-1] for s in header if s.startswith('element vertex ')))
    props=[s.split()[1:] for s in header if s.startswith('property ')]
    return {'bytes':p.stat().st_size,'header_bytes':offset,'vertices':n,'properties':props,
            'format':next(s for s in header if s.startswith('format '))}
base=src('desktop_mydesk');report={}
raw=sorted(p.name for p in (base/'frames').glob('*.png'))
gs=sorted(p.name for p in (base/'gs_dataset/images').glob('*.png'))
report['frames']={'raw_count':len(raw),'gs_count':len(gs),'excluded_from_gs':sorted(set(raw)-set(gs)),
                  'raw_sizes':dict(collections.Counter(str(Image.open(base/'frames'/p).size) for p in raw)),
                  'gs_sizes':dict(collections.Counter(str(Image.open(base/'gs_dataset/images'/p).size) for p in gs))}
for name,sub in [('distorted_sparse','colmap/sparse/0'),('undistorted_sparse','gs_dataset/sparse/0')]:
    p=base/sub
    report[name]={'cameras':cameras(p/'cameras.bin'),'images':images(p/'images.bin'),'point_statistics':points(p/'points3D.bin')}
report['registered_name_matches_gs_files']=sorted(r['name'] for r in report['undistorted_sparse']['images'])==gs
report['ply']={str(p.relative_to(base)):ply(p) for p in [base/'model/input.ply',base/'gs_dataset/sparse/0/points3D.ply',
                                                        base/'model/point_cloud/iteration_7000/point_cloud.ply',base/'model/point_cloud/iteration_30000/point_cloud.ply']}
with sqlite3.connect((base/'colmap/database.db').as_uri()+'?mode=ro',uri=True) as db:
    report['database']={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ['images','cameras','keypoints','descriptors','matches','two_view_geometries']}
    report['database']['keypoint_rows']=dict(db.execute('SELECT images.name,keypoints.rows FROM images JOIN keypoints USING(image_id)'))
    report['database']['verified_pairs_with_inliers']=db.execute('SELECT COUNT(*) FROM two_view_geometries WHERE rows>0').fetchone()[0]
report['dense_outputs']={p:len(list((base/'colmap/dense'/p).glob('*'))) for p in ['stereo/depth_maps','stereo/normal_maps','stereo/consistency_graphs']}
report['dense_fused_ply_exists']=(base/'colmap/dense/fused.ply').exists()
dump('historical-statistics.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ['distorted_sparse','undistorted_sparse','database']},ensure_ascii=False,indent=2))
print('SPARSE',json.dumps(report['undistorted_sparse']['point_statistics']))
print('CAMERAS',report['distorted_sparse']['cameras'],report['undistorted_sparse']['cameras'])
