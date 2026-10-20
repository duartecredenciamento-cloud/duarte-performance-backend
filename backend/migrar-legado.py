"""Audita e copia um SQLite legado para SQLite alvo vazio; não migra senhas/tabelas automaticamente.
Use somente em cópias de homologação depois de aprovar o mapeamento."""
import argparse, hashlib, json, shutil, sqlite3
from pathlib import Path

def inspect(path):
    c=sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro',uri=True)
    result={}
    for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        result[table]={'rows':c.execute(f' SELECT COUNT(*) FROM "{table}"').fetchone()[0], 'columns':[r[1] for r in c.execute(f'PRAGMA table_info("{table}")')]}
    c.close();return result

def main():
    p=argparse.ArgumentParser(description='Cria uma cópia de auditoria de SQLite; não realiza transformação de esquema.')
    p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--manifest',required=True)
    a=p.parse_args();src=Path(a.source);dst=Path(a.output)
    if not src.is_file() or src.stat().st_size==0:raise SystemExit('Fonte não existe ou está vazia.')
    if dst.exists():raise SystemExit('Destino já existe; não será sobrescrito.')
    shutil.copy2(src,dst)
    with dst.open('rb') as f: checksum=hashlib.sha256(f.read()).hexdigest()
    record={'source':str(src),'copy':str(dst),'sha256_copy':checksum,'tables':inspect(dst)}
    Path(a.manifest).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
