"""Testes de rotas com FastAPI TestClient e banco temporário isolado."""
import os, tempfile, unittest
from pathlib import Path

class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ['APP_ENV']='development'
        os.environ['LOCAL_DB_PATH']=str(Path(cls.temp.name)/'smoke.sqlite3')
        os.environ['ALLOW_SCHEMA_CREATE']='true'
        os.environ['SECRET_KEY']='smoke-test-secret-that-is-longer-than-32'
        import importlib, sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        import main
        from fastapi.testclient import TestClient
        cls.main=main
        cls.client=TestClient(main.app)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_ui_and_health(self):
        self.assertEqual(self.client.get('/').status_code,200)
        health=self.client.get('/healthz')
        self.assertEqual(health.status_code,200)
        self.assertEqual(health.json()['database'],'connected')

    def test_protected_views_reject_anonymous(self):
        self.assertEqual(self.client.get('/registros/').status_code,401)
        self.assertEqual(self.client.get('/cronograma/').status_code,401)
        self.assertEqual(self.client.get('/usuarios/').status_code,401)

    def test_status_rules(self):
        user=type('User',(),{'role':'Operador','nome':'Ana','username':'ana'})()
        with self.assertRaises(self.main.HTTPException) as ctx:
            self.main.criar_registro(self.main.RegistroCreate(cliente_nome='Cliente',status='Não Realizado',justificativa=''),None,user)
        self.assertEqual(ctx.exception.status_code,422)

if __name__=='__main__': unittest.main()
