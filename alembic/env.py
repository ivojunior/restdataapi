from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401  garante que os modelos sejam registrados no metadata
from app.config import settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tabelas mapeadas apenas para leitura, gerenciadas por sistemas externos (ex.: Protheus).
# O Alembic nunca deve gerar CREATE/ALTER/DROP para elas, mesmo em --autogenerate.
TABELAS_EXTERNAS = {
    "SE2070", "SA2070", "SB2070", "SB1000", "PA6000", "DAI070", "DAK070",
    "SA1070", "SE1070", "DA5070",
}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in TABELAS_EXTERNAS:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
