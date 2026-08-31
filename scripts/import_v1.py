from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# Пути определяются относительно проекта
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "Lets Meet DB Dump.xlsx"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_schema_v1.sql"

DATABASE_URL = (
    "postgresql+pg8000://user:secret@127.0.0.1:5432/"
    "lf8_lets_meet_db"
)


def read_and_transform_excel():
    """Читает Excel и формирует данные для migration_users."""

    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Tabelle1",
        dtype=str,
        keep_default_na=False,
    )

    names = df["Nachname, Vorname"].str.split(
        ", ",
        n=1,
        expand=True,
        regex=False,
    )
    names.columns = ["last_name", "first_name"]

    addresses = df["Straße Nr, PLZ Ort"].str.split(
        ", ",
        n=2,
        expand=True,
        regex=False,
    )
    addresses.columns = ["street", "postal_code", "city"]

    birth_dates = pd.to_datetime(
        df["Geburtsdatum"],
        format="%d.%m.%Y",
        errors="raise",
    ).dt.date

    users = pd.DataFrame({
        "email": df["E-Mail"],
        "first_name": names["first_name"],
        "last_name": names["last_name"],
        "birth_date": birth_dates,
        "postal_code": addresses["postal_code"],
        "city": addresses["city"],
    })

    return users


def validate(users):
    """Проверяет основные условия контракта V1."""

    if len(users) != 1576:
        raise ValueError(
            f"Erwartet: 1576 Zeilen, gefunden: {len(users)}"
        )

    if (users["email"] == "").any():
        raise ValueError("Leere E-Mail-Adresse gefunden")

    if users["email"].duplicated().any():
        raise ValueError("Doppelte E-Mail-Adresse gefunden")

    if users["birth_date"].isna().any():
        raise ValueError("Ungültiges Geburtsdatum gefunden")

    required_columns = [
        "email",
        "first_name",
        "last_name",
        "birth_date",
        "postal_code",
        "city",
    ]

    if users[required_columns].isna().any().any():
        raise ValueError("NULL-Wert in einer Pflichtspalte gefunden")


def rebuild_database(engine):
    """Создаёт таблицу и View заново из SQL-файла."""

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    statements = [
        statement.strip()
        for statement in schema_sql.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def import_users(engine, users):
    """Вставляет подготовленные данные параметризованным запросом."""

    insert_sql = text("""
        INSERT INTO users_v1 (
            email,
            first_name,
            last_name,
            birth_date,
            postal_code,
            city
        )
        VALUES (
            :email,
            :first_name,
            :last_name,
            :birth_date,
            :postal_code,
            :city
        )
    """)

    records = users.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(insert_sql, records)


def main():
    users = read_and_transform_excel()
    validate(users)

    engine = create_engine(DATABASE_URL)

    rebuild_database(engine)
    import_users(engine, users)

    with engine.begin() as connection:
        imported_count = connection.execute(
            text("SELECT count(*) FROM migration_users")
        ).scalar()

    print("Import erfolgreich")
    print("Importierte Personen:", imported_count)


if __name__ == "__main__":
    main()