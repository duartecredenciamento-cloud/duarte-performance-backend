"""Testes unitários das regras operacionais e isolamento de dados."""
import os
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("LOCAL_DB_PATH", "./test-data/test.sqlite3")
os.environ.setdefault("ALLOW_SCHEMA_CREATE", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-not-for-production-32chars")

import unittest
from unittest.mock import MagicMock
import main

class DomainRulesTests(unittest.TestCase):
    def test_status_partial_requires_reason(self):
        user=MagicMock(role="Operador", nome="Ana", username="ana")
        db=MagicMock()
        response=MagicMock()
        response.status_code=201
        response.json.return_value={"status":"Realizado Parcial"}
        db.add.return_value=None
        db.commit.return_value=None
        db.refresh.return_value=None
        db.query.return_value.filter.return_value.first.return_value=None
        with self.assertRaises(main.HTTPException) as ctx:
            main.criar_registro(main.RegistroCreate(cliente_nome="Cliente",status="Realizado Parcial",justificativa="",operador_nome="Ana"),db,user)
        self.assertEqual(ctx.exception.status_code,422)

    def test_worker_cannot_create_not_informed(self):
        user=MagicMock(role="Operador", nome="Ana", username="ana")
        with self.assertRaises(main.HTTPException) as ctx:
            main.criar_registro(main.RegistroCreate(cliente_nome="Cliente",status="Não Informado",justificativa="Auto"),MagicMock(),user)
        self.assertEqual(ctx.exception.status_code,422)

    def test_worker_cannot_launch_for_another_person(self):
        user=MagicMock(role="Operador", nome="Ana", username="ana")
        with self.assertRaises(main.HTTPException) as ctx:
            main.criar_registro(main.RegistroCreate(cliente_nome="Cliente",status="Realizado Total",operador_nome="Bruna"),MagicMock(),user)
        self.assertEqual(ctx.exception.status_code,403)

    def test_viewer_not_allowed_to_change_schedule(self):
        user=MagicMock(role="Visualizador", nome="Bia", username="bia")
        with self.assertRaises(main.HTTPException) as ctx:
            main.criar_cronograma(main.CronogramaCreate(operador="X"),MagicMock(),user)
        self.assertEqual(ctx.exception.status_code,403)

if __name__ == '__main__':
    unittest.main()
