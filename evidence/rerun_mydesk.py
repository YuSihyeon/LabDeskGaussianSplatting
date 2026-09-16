"""Read-only historical 3DGS inputs; rerender and optional 200-step PLY warm start.

Requires the historical graphdeco repository and its CUDA rasterizer environment.
Absolute input locations are supplied at runtime and kept in source-map.json only.
No historical input/configuration is written. Metrics are TRAINING-VIEW metrics.
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, json, math, random, time
from pathlib import Path
from types import SimpleNamespace

ap = argparse.ArgumentParser()
ap.add_argument('--repo', required=True)
ap.add_argument('--dataset', required=True)
ap.add_argument('--model', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--width', type=int, default=480)
ap.add_argument('--steps', type=int, default=200)
ap.add_argument('--interpolation', type=int, default=8)
a = ap.parse_args()
sys.path.insert(0, a.repo)
import numpy as np
import torch
from PIL import Image
import imageio.v2 as imageio
from scipy.spatial.transform import Rotation, Slerp
from scene.gaussian_model import GaussianModel
from scene.cameras import Camera, MiniCam
from gaussian_renderer import render
from utils.graphics_utils import getWorld2View2, getProjectionMatrix, focal2fov
from utils.loss_utils import ssim, l1_loss

out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
random.seed(0); np.random.seed(0); torch.manual_seed(0)
torch.set_num_threads(4)
started = time.time()
metadata = json.loads((Path(a.model)/'cameras.json').read_text())
metadata = sorted(metadata, key=lambda c:c['img_name'])
pipe = SimpleNamespace(convert_SHs_python=False, compute_cov3D_python=False,
                       debug=False, antialiasing=False)
bg = torch.zeros(3, dtype=torch.float32, device='cuda')

def dump(name, value):
    (out/name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

def digest(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

def array(img):
    return np.uint8(np.clip(img.detach().permute(1,2,0).cpu().numpy(),0,1)*255+0.5)

def writer(p, fps=24):
    return imageio.get_writer(str(p), fps=fps, codec='libx264', quality=8,
                             macro_block_size=2, ffmpeg_log_level='error')

cams = []
for c in metadata:
    with Image.open(Path(a.dataset)/'images'/c['img_name']) as im:
        height = round(im.height*a.width/im.width)
        if height % 2: height += 1
        R = np.array(c['rotation'])
        C = np.array(c['position'])
        cams.append(Camera((a.width,height), c['id'], R, -R.T@C,
                           focal2fov(c['fx'],c['width']),focal2fov(c['fy'],c['height']),
                           None, im.copy(), None, c['img_name'], c['id'], data_device='cpu'))
print('ENV', torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), flush=True)
print('CAMERAS', len(cams), 'RESOLUTION', cams[0].image_width, cams[0].image_height, flush=True)
provenance = []
for rel in ['cameras.json','cfg_args','point_cloud/iteration_7000/point_cloud.ply',
            'point_cloud/iteration_30000/point_cloud.ply']:
    p = Path(a.model)/rel
    provenance.append({'root':'historical_model','relative_path':rel,'bytes':p.stat().st_size,'sha256':digest(p)})
for p in sorted((Path(a.dataset)/'sparse'/'0').glob('*')):
    if p.is_file(): provenance.append({'root':'historical_dataset','relative_path':p.relative_to(a.dataset).as_posix(),
                                      'bytes':p.stat().st_size,'sha256':digest(p)})
for c in metadata:
    p = Path(a.dataset)/'images'/c['img_name']
    provenance.append({'root':'historical_dataset','relative_path':'images/'+p.name,'bytes':p.stat().st_size,'sha256':digest(p)})
dump('input-provenance.json', provenance)
dump('run-config.json', {'seed':0,'width':a.width,'height':cams[0].image_height,'steps':a.steps,
                        'interpolation_per_segment':a.interpolation,'video_fps':24,
                        'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),
                        'camera_count':len(cams),'eval_split':'all existing training views; no held-out test',
                        'method':'actual graphdeco CUDA splat rasterization; SH3; black background; antialiasing off',
                        'refinement':'PLY warm start, fresh Adam, fixed Gaussian count; no densification/pruning/exposure',
                        'historical_optimizer_state_restored':False})

def evaluate(model, label):
    rows=[]
    dest=out/label/'frames'; dest.mkdir(parents=True, exist_ok=True)
    with torch.no_grad(), writer(out/label/'training-views.mp4', fps=2) as w:
        for i, cam in enumerate(cams):
            pred = render(cam,model,pipe,bg)['render']
            gt = cam.original_image.cuda()
            mse = torch.mean((pred-gt)**2).item()
            row={'image':cam.image_name,'psnr_db':-10*math.log10(max(mse,1e-12)),
                 'ssim':ssim(pred[None],gt[None]).item(),'l1':l1_loss(pred,gt).item()}
            rows.append(row)
            rgb = array(pred)
            Image.fromarray(rgb).save(dest/f'{i:04}.png')
            w.append_data(rgb)
    with open(out/label/'per-view-metrics.csv','w',newline='',encoding='utf-8') as f:
        dw=csv.DictWriter(f,fieldnames=rows[0]); dw.writeheader(); dw.writerows(rows)
    summary={k:float(np.mean([r[k] for r in rows])) for k in ['psnr_db','ssim','l1']}
    summary.update({'view_count':len(rows),'gaussians':int(model.get_xyz.shape[0]),'evaluation':'training views only'})
    dump(label+'/summary.json',summary)
    print(label, json.dumps(summary), flush=True)
    return summary

results={}
for iteration in [7000,30000]:
    model=GaussianModel(3)
    model.load_ply(str(Path(a.model)/'point_cloud'/f'iteration_{iteration}'/'point_cloud.ply'))
    results[f'iteration_{iteration}']=evaluate(model,f'iteration_{iteration}')
    if iteration==7000:
        del model
        torch.cuda.empty_cache()

print('INTERPOLATED PATH',flush=True)
pathdir=out/'iteration_30000'/'interpolated'; pathdir.mkdir(exist_ok=True)
pathmanifest=[]
with torch.no_grad(), writer(out/'iteration_30000'/'camera-path.mp4') as w:
    idx=0
    for j in range(len(cams)-1):
        left,right=metadata[j:j+2]
        slerp=Slerp([0,1],Rotation.from_matrix([left['rotation'],right['rotation']]))
        for t in np.linspace(0,1,a.interpolation,endpoint=False):
            R=slerp(t).as_matrix()
            C=(1-t)*np.array(left['position'])+t*np.array(right['position'])
            wm=torch.tensor(getWorld2View2(R,-R.T@C)).T.cuda()
            pm=cams[j].projection_matrix
            cam=MiniCam(cams[j].image_width,cams[j].image_height,cams[j].FoVy,cams[j].FoVx,
                        0.01,100.0,wm,wm@pm)
            rgb=array(render(cam,model,pipe,bg)['render'])
            w.append_data(rgb)
            if idx%24==0: Image.fromarray(rgb).save(pathdir/f'{idx:04}.png')
            pathmanifest.append({'frame':idx,'left':left['img_name'],'right':right['img_name'],'fraction':float(t)})
            idx+=1
dump('camera-path.json',pathmanifest)
print('PATH FRAMES',idx,flush=True)

if a.steps:
    # This is a new, bounded refinement experiment, not optimizer-state continuation.
    rates={'_xyz':1e-5,'_features_dc':2.5e-4,'_features_rest':1.25e-5,
           '_opacity':2.5e-3,'_scaling':5e-4,'_rotation':1e-4}
    optimizer=torch.optim.Adam([{'params':[getattr(model,k)],'lr':v,'name':k} for k,v in rates.items()],eps=1e-15)
    dump('refinement-learning-rates.json',rates)
    history=[]; trainstart=time.time(); queue=[]
    for step in range(a.steps):
        if not queue:
            queue=list(range(len(cams))); random.shuffle(queue)
        cam=cams[queue.pop()]
        pred=render(cam,model,pipe,bg)['render']; gt=cam.original_image.cuda()
        l1=l1_loss(pred,gt); score=ssim(pred[None],gt[None]); loss=0.8*l1+0.2*(1-score)
        loss.backward(); optimizer.step(); optimizer.zero_grad(set_to_none=True)
        history.append({'step':step+1,'image':cam.image_name,'loss':loss.item(),'l1':l1.item(),'ssim':score.item()})
        if (step+1)%20==0: print('REFINE',step+1,'loss',loss.item(),flush=True)
    refout=out/'refined_200'; refout.mkdir(exist_ok=True)
    with open(refout/'training-loss.csv','w',newline='',encoding='utf-8') as f:
        dw=csv.DictWriter(f,fieldnames=history[0]);dw.writeheader();dw.writerows(history)
    model.save_ply(str(refout/'point_cloud.ply'))
    dump('refined_200/refinement-timing.json',{'steps':a.steps,'seconds':time.time()-trainstart,
                                             'gaussians_before':results['iteration_30000']['gaussians'],
                                             'gaussians_after':int(model.get_xyz.shape[0])})
    results['refined_200']=evaluate(model,'refined_200')
    torch.save({'step':a.steps,'seed':0,'optimizer':optimizer.state_dict()},refout/'optimizer-state.pt')

# A labeled comparison is encoded from actual rendered views, never from input-video frames.
import cv2
with writer(out/'comparison-7000-30000-refined.mp4',fps=2) as w:
    labels=['iteration_7000','iteration_30000']+(['refined_200'] if a.steps else [])
    for i in range(len(cams)):
        panels=[]
        for label in labels:
            rgb=np.array(Image.open(out/label/'frames'/f'{i:04}.png'))
            top=np.zeros((42,rgb.shape[1],3),dtype=np.uint8)
            cv2.putText(top,label,(12,27),cv2.FONT_HERSHEY_SIMPLEX,0.65,(255,255,255),1,cv2.LINE_AA)
            panels.append(np.concatenate([top,rgb],axis=0))
        w.append_data(np.concatenate(panels,axis=1))
results['total_wall_seconds']=time.time()-started
results['cuda_max_memory_allocated_bytes']=torch.cuda.max_memory_allocated()
dump('metrics-summary.json',results)
print('COMPLETE',json.dumps(results),flush=True)
