import alembic.config, alembic.script

cfg = alembic.config.Config("migrations/alembic.ini")
script = alembic.script.ScriptDirectory.from_config(cfg)
print("Heads:", script.get_heads())
