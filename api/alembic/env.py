"""
Alembic migration environment configuration.
"""
from logging.config import fileConfig
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import the models and Base
import sys
from pathlib import Path

# Add the api directory to the path so we can import app modules
api_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(api_dir))

from app.db import Base
from app.models import Transaction, Vendor, Rule, Report  # noqa: F401
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Execute the actual migrations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Convert sync URL to async if needed
    database_url = config.get_main_option("sqlalchemy.url")
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url and database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
