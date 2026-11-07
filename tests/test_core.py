import tempfile, unittest
from lessontool.config import Settings
from lessontool.store import ProjectStore
from lessontool.pipeline import Pipeline
from lessontool.exporter import export

class OfflinePipeline(Pipeline):
    def research(self,title,objective):
        return [{'title':'Example documentation','url':'https://example.com/docs','snippet':'Example source','kind':'Website'}]

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.s=Settings(data_dir=self.tmp.name); self.store=ProjectStore(self.tmp.name); self.pipe=OfflinePipeline(self.store,self.s)
    def tearDown(self): self.tmp.cleanup()
    def test_create_and_persist(self):
        p=self.store.create('Test lesson','Explain the topic'); self.assertEqual(self.store.get(p['id'])['title'],'Test lesson')
    def test_pipeline_completes_offline(self):
        p=self.store.create('HTTP Requests','Explain GET and POST'); self.pipe.run_all(p['id'],blocking=True); p=self.store.get(p['id'])
        self.assertTrue(all(v['status']=='done' for v in p['steps'].values())); self.assertEqual(p['lesson']['duration_minutes'],45); self.assertIn('qc1',p['qc']); self.assertIn('qc2',p['qc'])
    def test_export_contains_reports_and_lesson(self):
        p=self.store.create('SQL joins','Explain joins'); self.pipe.run_all(p['id'],blocking=True); data,name,mime=export(self.store.get(p['id']))
        self.assertTrue(name.endswith('.zip')); self.assertEqual(mime,'application/zip'); self.assertGreater(len(data),100)
    def test_empty_input_rejected(self):
        try:
            from app import create_app
        except ModuleNotFoundError:
            self.skipTest('Install requirements.txt to run Flask route tests')
        c=create_app(self.s,self.pipe).test_client(); r=c.post('/api/projects',json={'title':'','objective':'x'}); self.assertEqual(r.status_code,400)

if __name__=='__main__': unittest.main()
