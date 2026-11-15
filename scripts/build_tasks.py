#!/usr/bin/env python3
"""Deterministically package curated public drawings; never read external datasets.

Run with the project environment: python scripts/build_tasks.py
Curation lives in data/scenarios.json and data/sources.json. Only the public
catalogue and drawing previews are web assets. Gold is confined to tests/ and
oracle solutions, neither of which belongs to the agent image build context.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('vector', 'clean', 'scan')
SCAN_SEED = 20261114

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')

def read_json(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def render_inputs(source, index):
    path = ROOT / source['asset']
    if sha(path) != source['asset_sha256']:
        raise ValueError('Curated asset hash mismatch: '+source['id'])
    document = pymupdf.open(path)
    if len(document) != 1 or document[0].rotation:
        raise ValueError('Curated assets must be normalized single-page drawings')
    page = document[0]
    scale = 4096 / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csGRAY, alpha=False)
    clean = Image.frombytes('L', (pix.width,pix.height), pix.samples)
    clean_path = ROOT/'data/assets'/f"{source['id']}-clean.png"
    scan_path = ROOT/'data/assets'/f"{source['id']}-scan.png"
    clean.save(clean_path, compress_level=9)
    faded = ImageEnhance.Contrast(clean.filter(ImageFilter.GaussianBlur(.55))).enhance(.72)
    # One image, one RNG and one CPU job; preserve dimensions exactly.
    rng = np.random.default_rng(SCAN_SEED+index)
    arr = np.asarray(faded, dtype=np.float32)
    for row in range(arr.shape[0]):
        arr[row] += rng.normal(0,2.0,arr.shape[1]).astype(np.float32)
    noisy = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    stream=io.BytesIO(); noisy.save(stream,format='JPEG',quality=68)
    stream.seek(0)
    with Image.open(stream) as compressed:
        compressed.convert('L').save(scan_path,compress_level=9)
    vector_page={'width':page.rect.width,'height':page.rect.height,'space':'pdf_pt'}
    raster_page={'width':pix.width,'height':pix.height,'space':'image_px'}
    return {'vector':(path,vector_page),'clean':(clean_path,raster_page),'scan':(scan_path,raster_page)}, {'seed':SCAN_SEED+index,'synthetic':True,'width':pix.width,'height':pix.height,'clean_sha256':sha(clean_path),'scan_sha256':sha(scan_path),'transform':'grayscale raster; Gaussian blur0.55; contrast0.72; Gaussian noise sd2; JPEG quality68; no geometric transform'}

def task_config(scenario,condition,source):
    # Harbor 0.26.0 / TaskConfig schema1.4. JSON strings are valid TOML strings.
    quote=lambda v:json.dumps(v,ensure_ascii=False)
    return f'''schema_version = "1.4"
artifacts = [{{source = "/workspace/answer.json"}}]

[task]
name = "blueprint-takeoff/{scenario['id']}-{condition}"
version = "1.0.0"
description = {quote(scenario['title'])}

[metadata]
family = {quote(scenario['family'])}
condition = {quote(condition)}
difficulty = {quote('hard' if condition=='scan' else scenario['difficulty'])}
scenario_id = {quote(scenario['id'])}
split = {quote(scenario['split'])}
source_id = {quote(source['id'])}
source_url = {quote(source['url'])}
license = {quote(source['license'])}
trap = {str(scenario['trap']).lower()}
synthetic_scan = {str(condition=='scan').lower()}

[agent]
timeout_sec = 600

[environment]
build_timeout_sec = 900
cpus = 1
memory_mb = 2048
storage_mb = 4096
network_mode = "public"

[verifier]
timeout_sec = 60
environment_mode = "separate"

[verifier.environment]
build_timeout_sec = 600
cpus = 1
memory_mb = 256
storage_mb = 512
network_mode = "no-network"
'''

def build_task(scenario,condition,source,inputs,transform):
    task_id=f"{scenario['id']}-{condition}"
    task=ROOT/'tasks'/task_id
    for name in ('environment','tests','solution'):(task/name).mkdir(parents=True,exist_ok=True)
    asset,page=inputs[condition]
    filename='drawing.pdf' if condition=='vector' else 'drawing.png'
    shutil.copyfile(asset,task/'environment'/filename)
    preview=inputs['clean' if condition=='vector' else condition][0]
    shutil.copyfile(preview,ROOT/'data/previews'/f'{task_id}.png')
    evidence=[]
    vector_page=inputs['vector'][1]
    for original in scenario['evidence']:
        box=dict(original)
        if condition!='vector':
            factors=[page['width']/vector_page['width'],page['height']/vector_page['height']]*2
            box['bbox']=[round(a*b,4) for a,b in zip(original['bbox'],factors)]
            box['space']='image_px'
        evidence.append(box)
    gold={k:scenario[k] for k in ('value','unit','alt_values','family')}
    gold.update(pages=[page],evidence=evidence,scenario_id=scenario['id'],provenance=scenario['provenance'],source_asset_sha256=source['asset_sha256'],input_sha256=sha(asset),condition=condition)
    if condition=='scan':gold['scan_transform']=transform
    write_json(task/'tests/gold.json',gold)
    oracle={'value':gold['value'],'unit':gold['unit'],'confidence':1.0,'evidence':evidence,'assumptions':[scenario['conventions']]}
    (task/'solution/solve.sh').write_text("#!/bin/sh\nset -eu\nmkdir -p /workspace\ncat > /workspace/answer.json <<'BLUEPRINT_ORACLE_JSON'\n"+json.dumps(oracle,ensure_ascii=False)+'\nBLUEPRINT_ORACLE_JSON\n')
    instructions=f'''You are a quantity surveyor. The drawing is at /workspace/{filename}.

Question: {scenario['question']}

Conventions: {scenario['conventions']} Areas use the inner wall face unless gross area is requested. A double door is one door set. Use the drawing's graphic scale or dimension strings.

Write /workspace/answer.json as a JSON object with exactly the following required fields:
- value: a finite number (an integer for counts), or null to abstain.
- unit: m, mm, cm, ft, in, m2, mm2, cm2, ft2, in2, or count.
- confidence: a number from 0 to 1.
- evidence: a list of at most 32 distinct boxes, each {{"page":0,"bbox":[x0,y0,x1,y1],"space":"{page['space']}","note":"what this identifies"}}.
- assumptions: a list of strings describing your measurement conventions.

Coordinates start at the top-left. Page 0 is {page['width']} wide by {page['height']} high in {page['space']}. Boxes must have positive size and stay inside the page; a box covering more than 90% of the page is invalid. For PDF input, use PDF-point coordinates, converting any raster inspection coordinates back to the canonical page space. Missing or malformed submissions score zero.

The reward combines quantity accuracy (75%), relevant drawing evidence (15%, gated by quantity accuracy), and calibrated confidence (10%). Quantities receive full value credit within 2%; exact counts receive full credit. An explicit, valid abstention can earn calibration credit. Supply evidence around the relevant room, openings, equipment or dimensions.
'''
    (task/'instruction.md').write_text(instructions)
    (task/'task.toml').write_text(task_config(scenario,condition,source))
    (task/'environment/Dockerfile').write_text(f'''FROM python:3.12-slim
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr curl ca-certificates git nodejs npm && rm -rf /var/lib/apt/lists/*
RUN npm install -g opencode-ai@1.19.5 && opencode --version
RUN pip install --no-cache-dir PyMuPDF==1.26.6 Pillow==12.0.0 numpy==2.2.6 shapely==2.1.2 opencv-python-headless==4.12.0.88
WORKDIR /workspace
COPY {filename} /workspace/{filename}
''')
    # Standalone verifier context contains trusted scorer and gold, never the agent context.
    package=task/'tests/blueprint_gym';package.mkdir(exist_ok=True)
    for name in ('__init__.py','scoring.py','verify.py'):
        shutil.copyfile(ROOT/'blueprint_gym'/name,package/name)
    (task/'tests/verify.py').write_text('from blueprint_gym.verify import main\nif __name__ == "__main__":\n    raise SystemExit(main())\n')
    (task/'tests/Dockerfile').write_text('FROM python:3.12-slim\nWORKDIR /workspace\nCOPY . /tests/\n')
    (task/'tests/test.sh').write_text('#!/bin/sh\nset -eu\npython /tests/verify.py --gold /tests/gold.json --answer /workspace/answer.json --output-dir /logs/verifier\n')
    (task/'solution/solve.sh').chmod(0o755);(task/'tests/test.sh').chmod(0o755)
    return {**{k:scenario[k] for k in ('title','question','family','split','trap')},'id':task_id,'scenario_id':scenario['id'],'condition':condition,'difficulty':'hard' if condition=='scan' else scenario['difficulty'],'pages':[page],'preview_url':f'/api/tasks/{task_id}/image','source':{k:source[k] for k in ('id','title','url','license','license_url')},'drawing_filename':filename}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',help='Build one scenario ID for smoke testing; default builds all')
    args=parser.parse_args()
    sources=read_json(ROOT/'data/sources.json');scenarios=read_json(ROOT/'data/scenarios.json')
    (ROOT/'data/previews').mkdir(parents=True,exist_ok=True)
    catalogue=[]
    for index,source in enumerate(sources):
        selected=[s for s in scenarios if s['source_id']==source['id'] and (not args.only or s['id']==args.only)]
        if not selected:continue
        inputs,transform=render_inputs(source,index)
        source['generated_inputs']=transform
        for scenario in selected:
            for condition in CONDITIONS:
                catalogue.append(build_task(scenario,condition,source,inputs,transform))
                print(f"Built {scenario['id']}-{condition}",flush=True)
    if not args.only:
        write_json(ROOT/'data/catalog.json',sorted(catalogue,key=lambda r:r['id']))
        write_json(ROOT/'data/sources.json',sources)
    return 0

if __name__=='__main__':raise SystemExit(main())
