"""Load cleaned hospital records into PostgreSQL.

Run from the project root with: python -m src.loading
"""

import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from src.extraction import extract_data
from src.ingestion import PROJECT_ROOT


def loading_data(data=None, engine=None, if_exists="replace"):
    """Load the four tables and return their database row counts.

    The default replaces existing tables, matching the notebook. Pass an engine
    to use an existing connection instead of creating the configured database.
    """
    if if_exists not in ("fail", "replace", "append"):
        raise ValueError("if_exists must be fail, replace, or append")
    if data is None:
        data = extract_data()

    owns_engine = engine is None
    if owns_engine:
        load_dotenv(PROJECT_ROOT / ".env")
        db_name = os.getenv("DB_NAME")
        if not db_name:
            raise ValueError("Set DB_NAME in the project's .env file")

        connection = psycopg2.connect(
            dbname=os.getenv("DB_MAINTENANCE_DB") or "postgres",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
        )
        try:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                    )
        finally:
            connection.close()

        database_url = URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=db_name,
        )
        engine = create_engine(database_url)

    try:
        counts = {}
        with engine.begin() as connection:
            for name in ("patients", "doctors", "appointments", "billing"):
                data[name].to_sql(name, connection, if_exists=if_exists, index=False)
                result = pd.read_sql_query(
                    text(f'SELECT COUNT(*) AS row_count FROM "{name}"'), connection
                )
                counts[name] = int(result.loc[0, "row_count"])
        return counts
    finally:
        if owns_engine:
            engine.dispose()


if __name__ == "__main__":
    print(loading_data())
