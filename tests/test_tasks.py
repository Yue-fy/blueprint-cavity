"""Catalogue integrity tests; no solver or withheld-dataset imports."""
import collections
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())

class TaskCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.catalog = read(ROOT / 'data/catalog.json')
        self.scenarios = read(ROOT / 'data/scenarios.json')
        self.sources = read(ROOT / 'data/sources.json')

    def test_mix_and_grouped_split(self):
        self.assertEqual(len(self.catalog), 36)
        by_scenario = collections.defaultdict(list)
        for row in self.catalog: by_scenario[row['scenario_id']].append(row)
        self.assertEqual(len(by_scenario), 12)
        for rows in by_scenario.values():
            self.assertEqual({r['condition'] for r in rows}, {'vector','clean','scan'})
            self.assertEqual(len({r['split'] for r in rows}), 1)
        self.assertEqual({r['family'] for r in self.catalog}, {'area','skirting','openings','slab','piping'})
        self.assertIn(sum(r['split']=='holdout' for r in self.catalog), range(9,13))
        self.assertIn(sum(r['trap'] for r in self.catalog), range(3,6))
        for family in {r['family'] for r in self.catalog}:
            counts=collections.Counter(r['condition'] for r in self.catalog if r['family']==family)
            self.assertEqual(len(set(counts.values())),1)

    def test_no_gold_in_public_catalog_or_build_context(self):
        expected={'id','scenario_id','title','question','family','condition','difficulty','split','trap','pages','preview_url','source','drawing_filename'}
        for row in self.catalog:
            self.assertEqual(set(row),expected)
            task=ROOT/'tasks'/row['id']
            self.assertTrue((task/'tests/gold.json').is_file())
            self.assertEqual({p.name for p in (task/'environment').iterdir()}, {'Dockerfile',row['drawing_filename']})
            for name in ['instruction.md','task.toml','solution/solve.sh','tests/test.sh','tests/verify.py']:
                self.assertTrue((task/name).is_file(), name)
            self.assertNotIn('gold', (task/'environment/Dockerfile').read_text().lower())
            self.assertTrue((ROOT/'data/previews'/f"{row['id']}.png").is_file())

    def test_provenance_and_hashes(self):
        for source in self.sources:
            self.assertTrue(source['url'].startswith('https://'))
            self.assertTrue(source['license_url'].startswith('https://'))
            self.assertTrue(source['license_verification']['checked_on'])
            asset=ROOT/source['asset']
            self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),source['asset_sha256'])
            self.assertEqual(len(source['original_sha256']),64)
        for s in self.scenarios:
            self.assertTrue(s['provenance']['reference_id'])
            self.assertTrue(s['provenance']['gold_author'])
            self.assertTrue(s['provenance']['evidence_author'])

    def test_bounded_evidence_and_gold(self):
        for row in self.catalog:
            gold=read(ROOT/'tasks'/row['id']/'tests/gold.json')
            self.assertEqual(gold['pages'], row['pages'])
            self.assertTrue(gold['evidence'])
            for box in gold['evidence']:
                page=gold['pages'][box['page']]
                x0,y0,x1,y1=box['bbox']
                self.assertTrue(0<=x0<x1<=page['width'])
                self.assertTrue(0<=y0<y1<=page['height'])
                self.assertEqual(box['space'],page['space'])

    def test_harbor_schema_and_separate_verifier(self):
        from harbor.models.task.config import TaskConfig
        for row in self.catalog:
            task=ROOT/'tasks'/row['id']
            config=TaskConfig.model_validate_toml((task/'task.toml').read_text())
            self.assertEqual(config.schema_version,'1.4')
            self.assertEqual(config.verifier.environment_mode.value,'separate')
            self.assertEqual(config.verifier.environment.network_mode.value,'no-network')
            self.assertEqual(config.artifacts[0].source,'/workspace/answer.json')
            self.assertTrue((task/'tests/Dockerfile').is_file())
            for name in ('scoring.py','verify.py'):
                self.assertEqual((ROOT/'blueprint_gym'/name).read_bytes(),(task/'tests/blueprint_gym'/name).read_bytes())

    def test_pdf_metadata_and_input_geometry(self):
        import pymupdf
        from PIL import Image
        for source in self.sources:
            with pymupdf.open(ROOT/source['asset']) as pdf:
                self.assertEqual(len(pdf),1)
                self.assertEqual(pdf[0].rotation,0)
                for key in ('title','author','subject','keywords','creator','producer'):
                    self.assertFalse(pdf.metadata.get(key))
                self.assertFalse(pdf.get_xml_metadata())
                self.assertEqual(pdf.embfile_count(),0)
                self.assertFalse(list(pdf[0].annots() or []))
            clean=ROOT/'data/assets'/f"{source['id']}-clean.png"
            scan=ROOT/'data/assets'/f"{source['id']}-scan.png"
            self.assertEqual(hashlib.sha256(clean.read_bytes()).hexdigest(),source['generated_inputs']['clean_sha256'])
            self.assertEqual(hashlib.sha256(scan.read_bytes()).hexdigest(),source['generated_inputs']['scan_sha256'])
            with Image.open(clean) as a,Image.open(scan) as b:
                self.assertEqual(a.size,b.size)
                self.assertEqual(max(a.size),4096)
                self.assertFalse(a.info)
                self.assertFalse(b.info)
        for row in self.catalog:
            gold=read(ROOT/'tasks'/row['id']/'tests/gold.json')
            drawing=ROOT/'tasks'/row['id']/'environment'/row['drawing_filename']
            self.assertEqual(hashlib.sha256(drawing.read_bytes()).hexdigest(),gold['input_sha256'])

    def test_exact_cv_and_fp_evidence_not_substring_matches(self):
        import pymupdf
        page=pymupdf.open(ROOT/'data/assets/usace-piping.pdf')[0]
        words=page.get_text('words')
        for scenario in self.scenarios:
            if scenario['id'] not in ('bp-10','bp-11'): continue
            prefix='CV' if scenario['id']=='bp-10' else 'FP'
            self.assertEqual(len(scenario['evidence']),5)
            for n,element in enumerate(scenario['evidence'],1):
                matching=[w for w in words if w[4]==f'{prefix}-{n}']
                self.assertEqual(len(matching),1)
                x0,y0,x1,y1=matching[0][:4];a,b,c,d=element['bbox']
                self.assertTrue(a<=(x0+x1)/2<=c and b<=(y0+y1)/2<=d)

    def test_trap_and_measured_room_accuracy(self):
        from blueprint_gym.scoring import score_answer
        for row in self.catalog:
            if not row['trap']: continue
            gold=read(ROOT/'tasks'/row['id']/'tests/gold.json')
            wrong={'value':10000,'unit':'m2','confidence':1,'evidence':gold['evidence'],'assumptions':[]}
            self.assertLessEqual(score_answer(wrong,gold)['reward'],.1)
        for scenario in self.scenarios[:2]:
            x0,y0,x1,y1=scenario['evidence'][0]['bbox']
            derived=(x1-x0)*(y1-y0)*(.0254/72*200)**2
            self.assertLess(abs(derived/scenario['value']-1),.02)

    def test_oracle_noop_all_tasks(self):
        from blueprint_gym.scoring import score_answer as score
        for row in self.catalog:
            gold=read(ROOT/'tasks'/row['id']/'tests/gold.json')
            script=(ROOT/'tasks'/row['id']/'solution/solve.sh').read_text()
            answer=json.loads(script.split("<<'BLUEPRINT_ORACLE_JSON'\n",1)[1].split('\nBLUEPRINT_ORACLE_JSON',1)[0])
            self.assertEqual(score(answer,gold)['reward'],1.0,row['id'])
            self.assertEqual(score(None,gold)['reward'],0.0,row['id'])

if __name__=='__main__': unittest.main()
