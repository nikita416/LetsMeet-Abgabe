from pathlib import Path
import xml.etree.ElementTree as ET

from sqlalchemy import create_engine, text

from import_v2 import (
    DATABASE_URL,
    build_email_mapping,
    insert_records,
    read_sources,
    transform_hobbies,
    transform_interests,
    transform_likes,
    transform_messages,
    transform_users,
    validate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "03_schema_v3.sql"
XML_PATH = PROJECT_ROOT / "Lets_Meet_Hobbies.xml"


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


def transform_xml_hobbies(
    excel_hobbies,
    excel_email_by_lower,
):
    root = ET.parse(XML_PATH).getroot()

    known_pairs = {
        (
            record["email"].lower(),
            record["hobby_name"],
        )
        for record in excel_hobbies
    }

    xml_records = []

    for user_number, user in enumerate(
        root.findall("user"),
        start=1,
    ):
        raw_email = (user.findtext("email") or "").strip()
        email_lower = raw_email.lower()

        if email_lower not in excel_email_by_lower:
            raise ValueError(
                "Unbekannte XML-Person bei user"
                f"[{user_number}]: {raw_email!r}"
            )

        canonical_email = excel_email_by_lower[email_lower]

        for hobby_number, hobby in enumerate(
            user.findall("./hobbies/hobby"),
            start=1,
        ):
            hobby_name = (hobby.text or "").strip()

            if not hobby_name:
                raise ValueError(
                    "Leeres XML-Hobby bei "
                    f"user[{user_number}]/hobby[{hobby_number}]"
                )

            pair = (email_lower, hobby_name)

            # Fachlich gleiche Zuordnungen nur einmal.
            if pair in known_pairs:
                continue

            known_pairs.add(pair)

            xml_records.append({
                "email": canonical_email,
                "hobby_name": hobby_name,
                "priority": None,
                "source": "xml",
            })

    return xml_records


def main():
    excel, mongo_users = read_sources()

    excel_email_by_lower, mongo_by_lower = (
        build_email_mapping(excel, mongo_users)
    )

    users = transform_users(excel, mongo_by_lower)
    interests = transform_interests(excel)
    excel_hobbies = transform_hobbies(excel)
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
        excel_hobbies,
        likes,
        messages,
    )

    xml_hobbies = transform_xml_hobbies(
        excel_hobbies,
        excel_email_by_lower,
    )

    if len(xml_hobbies) != 300:
        raise ValueError(
            "Erwartet werden 300 neue XML-Hobbyzuordnungen, "
            f"gefunden wurden {len(xml_hobbies)}"
        )

    all_hobbies = excel_hobbies + xml_hobbies

    hobby_names = [
        {"hobby_name": hobby_name}
        for hobby_name in sorted({
            record["hobby_name"]
            for record in all_hobbies
        })
    ]

    engine = create_engine(DATABASE_URL)

    rebuild_schema(engine)

    insert_records(engine, "users_v2", users)
    insert_records(engine, "hobbies", hobby_names)
    insert_records(engine, "user_interests", interests)
    insert_records(engine, "user_hobbies", all_hobbies)
    insert_records(engine, "likes", likes)
    insert_records(engine, "messages", messages)

    print("V3-Basisimport erfolgreich")
    print("Personen:", len(users))
    print("Interessen:", len(interests))
    print("Excel-Hobbyzuordnungen:", len(excel_hobbies))
    print("XML-Hobbyzuordnungen:", len(xml_hobbies))
    print("Hobbyzuordnungen gesamt:", len(all_hobbies))
    print("Likes:", len(likes))
    print("Nachrichten:", len(messages))
    print("Ablehnungen:", 0)


if __name__ == "__main__":
    main()