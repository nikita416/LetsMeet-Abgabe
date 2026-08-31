from datetime import datetime
from pathlib import Path
import re

import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "Lets Meet DB Dump.xlsx"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "02_schema_v2.sql"

DATABASE_URL = (
    "postgresql+pg8000://user:secret@127.0.0.1:5432/"
    "lf8_lets_meet_db"
)

MONGO_URL = "mongodb://127.0.0.1:27017/"
MONGO_DATABASE = "LetsMeet"
MONGO_COLLECTION = "users"

def parse_timestamp(value):
    """Liest die in MongoDB vorkommenden Zeitformate."""

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    try:
        return datetime.strptime(
            value,
            "%d.%m.%Y %H:%M:%S",
        )
    except ValueError as error:
        raise ValueError(
            f"Unbekanntes Zeitformat: {value!r}"
        ) from error

def read_sources():
    excel = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Tabelle1",
        dtype=str,
        keep_default_na=False,
    )

    mongo_client = MongoClient(MONGO_URL)
    mongo_users = list(
        mongo_client[MONGO_DATABASE][MONGO_COLLECTION].find()
    )

    return excel, mongo_users


def build_email_mapping(excel, mongo_users):
    excel_email_by_lower = {
        email.lower(): email
        for email in excel["E-Mail"]
    }
    mongo_by_lower = {
        document["_id"].lower(): document
        for document in mongo_users
    }

    if len(excel_email_by_lower) != len(excel):
        raise ValueError(
            "Excel enthält E-Mail-Duplikate ohne Beachtung "
            "der Groß-/Kleinschreibung"
        )

    if len(mongo_by_lower) != len(mongo_users):
        raise ValueError(
            "MongoDB enthält E-Mail-Duplikate ohne Beachtung "
            "der Groß-/Kleinschreibung"
        )

    if set(excel_email_by_lower) != set(mongo_by_lower):
        raise ValueError(
            "Excel und MongoDB enthalten unterschiedliche Personen"
        )

    return excel_email_by_lower, mongo_by_lower


def transform_users(excel, mongo_by_lower):
    addresses = excel["Straße Nr, PLZ Ort"].str.split(
        ", ",
        n=2,
        expand=True,
        regex=False,
    )
    addresses.columns = ["street", "postal_code", "city"]

    birth_dates = pd.to_datetime(
        excel["Geburtsdatum"],
        format="%d.%m.%Y",
        errors="raise",
    ).dt.date

    records = []

    for index, row in excel.iterrows():
        excel_email = row["E-Mail"]
        mongo = mongo_by_lower[excel_email.lower()]

        # Kundinnenentscheidung: MongoDB hat bei Konflikten Vorrang.
        mongo_name = mongo["name"]
        name_parts = mongo_name.split(", ", 1)

        if len(name_parts) != 2:
            raise ValueError(
                f"MongoDB-Name kann nicht getrennt werden: "
                f"{mongo_name!r}"
            )

        last_name, first_name = name_parts

        records.append({
            "email": excel_email,
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": birth_dates.iloc[index],
            "street": addresses.iloc[index]["street"],
            "postal_code": addresses.iloc[index]["postal_code"],
            "city": addresses.iloc[index]["city"],
            "phone": mongo.get("phone", ""),
            "gender": row["Geschlecht (m/w/nonbinary)"],
        })

    return records


def transform_interests(excel):
    records = []

    for _, row in excel.iterrows():
        for interest_code in row["Interessiert an"]:
            records.append({
                "email": row["E-Mail"],
                "interest_code": interest_code,
            })

    return records


def transform_hobbies(excel):
    hobby_column = excel.columns[3]
    records = []

    for row_number, row in excel.iterrows():
        raw_hobbies = row[hobby_column]

        if raw_hobbies == "":
            continue

        for part in raw_hobbies.split("; "):
            if part == "":
                continue

            match = re.fullmatch(r"(.+) %(-?\d+)%", part)

            if match is None:
                raise ValueError(
                    f"Ungültiges Hobby in Excel-Zeile "
                    f"{row_number + 2}: {part!r}"
                )

            records.append({
                "email": row["E-Mail"],
                "hobby_name": match.group(1),
                "priority": int(match.group(2)),
                "source": "excel",
            })

    return records


def transform_likes(
    mongo_users,
    excel_email_by_lower,
):
    records = []

    for document in mongo_users:
        liker_email = excel_email_by_lower[
            document["_id"].lower()
        ]

        for like in document.get("likes", []):
            liked_email = excel_email_by_lower[
                like["liked_email"].lower()
            ]

            records.append({
                "liker_email": liker_email,
                "liked_email": liked_email,
                "status": like["status"],
                "liked_at": parse_timestamp(
    like["timestamp"]
),
            })

    return records


def transform_messages(
    mongo_users,
    excel_email_by_lower,
):
    records = []

    for document in mongo_users:
        sender_email = excel_email_by_lower[
            document["_id"].lower()
        ]

        for message in document.get("messages", []):
            receiver_email = excel_email_by_lower[
                message["receiver_email"].lower()
            ]

            records.append({
                "sender_email": sender_email,
                "receiver_email": receiver_email,
                "body": message["message"],
                "sent_at": parse_timestamp(
                message["timestamp"]
                ),
                "conversation_id": int(
                    message["conversation_id"]
                ),
            })

    return records


def validate(
    users,
    interests,
    hobbies,
    likes,
    messages,
):
    expected_counts = {
        "users": (len(users), 1576),
        "interests": (len(interests), 1609),
        "hobbies": (len(hobbies), 4828),
        "likes": (len(likes), 500),
        "messages": (len(messages), 300),
    }

    for name, (actual, expected) in expected_counts.items():
        if actual != expected:
            raise ValueError(
                f"{name}: erwartet {expected}, gefunden {actual}"
            )

    user_emails = [record["email"] for record in users]

    if len(user_emails) != len(set(user_emails)):
        raise ValueError("Doppelte E-Mail-Adresse in users")

    interest_keys = {
        (record["email"], record["interest_code"])
        for record in interests
    }

    if len(interest_keys) != len(interests):
        raise ValueError("Doppelte Interessen-Zuordnung")

    hobby_keys = {
        (
            record["email"],
            record["hobby_name"],
            record["source"],
        )
        for record in hobbies
    }

    if len(hobby_keys) != len(hobbies):
        raise ValueError("Doppelte Hobby-Zuordnung")

    like_keys = {
        (record["liker_email"], record["liked_email"])
        for record in likes
    }

    if len(like_keys) != len(likes):
        raise ValueError("Doppelte Like-Zuordnung")


def rebuild_schema(engine):
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    statements = [
        statement.strip()
        for statement in schema_sql.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def insert_records(engine, table_name, records):
    if not records:
        return

    columns = list(records[0].keys())
    column_sql = ", ".join(columns)
    value_sql = ", ".join(
        f":{column}" for column in columns
    )

    statement = text(
        f"INSERT INTO {table_name} "
        f"({column_sql}) VALUES ({value_sql})"
    )

    with engine.begin() as connection:
        connection.execute(statement, records)


def main():
    excel, mongo_users = read_sources()

    excel_email_by_lower, mongo_by_lower = (
        build_email_mapping(excel, mongo_users)
    )

    users = transform_users(excel, mongo_by_lower)
    interests = transform_interests(excel)
    hobbies = transform_hobbies(excel)
    likes = transform_likes(
        mongo_users,
        excel_email_by_lower,
    )
    messages = transform_messages(
        mongo_users,
        excel_email_by_lower,
    )

    validate(
        users,
        interests,
        hobbies,
        likes,
        messages,
    )

    hobby_names = [
        {"hobby_name": hobby_name}
        for hobby_name in sorted({
            record["hobby_name"]
            for record in hobbies
        })
    ]

    engine = create_engine(DATABASE_URL)

    rebuild_schema(engine)

    insert_records(engine, "users_v2", users)
    insert_records(engine, "hobbies", hobby_names)
    insert_records(engine, "user_interests", interests)
    insert_records(engine, "user_hobbies", hobbies)
    insert_records(engine, "likes", likes)
    insert_records(engine, "messages", messages)

    print("V2-Import erfolgreich")
    print("Personen:", len(users))
    print("Interessen:", len(interests))
    print("Hobby-Zuordnungen:", len(hobbies))
    print("Likes:", len(likes))
    print("Nachrichten:", len(messages))


if __name__ == "__main__":
    main()