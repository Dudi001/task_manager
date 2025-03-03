import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context
from app.models import Base


config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_online():
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=Base.metadata,
                compare_type=True
            )

            await connection.run_sync(context.run_migrations)

    asyncio.run(do_run_migrations())


run_migrations_online()
