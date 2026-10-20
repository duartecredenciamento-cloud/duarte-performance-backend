from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
import models

load_dotenv()
config=context.config
if config.config_file_name: fileConfig(config.config_file_name)
url=os.getenv('DATABASE_URL','').strip()
if not url: raise RuntimeError('DATABASE_URL deve apontar ao banco alvo explicitamente.')
if url.startswith('postgres://'): url=url.replace('postgres://','postgresql://',1)
config.set_main_option('sqlalchemy.url',url.replace('%','%%'))
target_metadata=models.Base.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option('sqlalchemy.url'),target_metadata=target_metadata,literal_binds=True,compare_type=True)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    connectable=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
        with context.begin_transaction(): context.run_migrations()

if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
