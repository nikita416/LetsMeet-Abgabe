from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from sqlalchemy import create_engine, text

from import_v2 import DATABASE_URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = (
    PROJECT_ROOT
    / "material"
    / "letsmeet-transfer-v3.zip"
)

EXPECTED_ARCHIVE_SHA256 = (
    "5370a041066db2c8d76bba1ab95e79b33"
    "be984a2d92d73b5ad409a02d8bd1385"
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(value):
    if value is None:
        return None

    return unicodedata.normalize(
        "NFC",
        value.strip(),
    )


def repair_mojibake(value):
    value = normalize(value)

    try:
        repaired = value.encode(
            "iso-8859-1"
        ).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value

    return normalize(repaired)


def parse_birth_date(value):
    value = normalize(value)

    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(
                value,
                date_format,
            ).date()
        except ValueError:
            pass

    raise ValueError(
        f"Ungültiges Geburtsdatum: {value!r}"
    )


def add_rejection(
    connection,
    source,
    source_ref,
    reason,
):
    connection.execute(
        text(
            """
            INSERT INTO rejections (
                source,
                source_ref,
                reason
            )
            VALUES (
                :source,
                :source_ref,
                :reason
            )
            ON CONFLICT (source, source_ref)
            DO UPDATE SET reason = EXCLUDED.reason
            """
        ),
        {
            "source": source,
            "source_ref": source_ref,
            "reason": reason,
        },
    )


def find_user_email(connection, email):
    return connection.execute(
        text(
            """
            SELECT email
            FROM users_v2
            WHERE lower(email) = lower(:email)
            """
        ),
        {"email": email},
    ).scalar_one_or_none()


def process_profile(
    connection,
    source,
    source_ref,
    element,
):
    values = {
        key: normalize(element.get(key))
        for key in (
            "email",
            "first_name",
            "last_name",
            "birth_date",
            "postal_code",
            "city",
            "phone",
            "gender",
        )
    }

    if source == "encoding-mojibake.xml":
        values["first_name"] = repair_mojibake(
            values["first_name"]
        )
        values["last_name"] = repair_mojibake(
            values["last_name"]
        )
        values["city"] = repair_mojibake(
            values["city"]
        )

    missing = [
        key
        for key, value in values.items()
        if value in (None, "")
    ]

    if missing:
        raise ValueError(
            "Fehlende Profilfelder: "
            + ", ".join(missing)
        )

    forbidden_values = {
        "",
        "-",
        "n/a",
        "na",
        "null",
        "none",
        "unknown",
        "unbekannt",
    }

    invalid_fields = [
        key
        for key, value in values.items()
        if value is not None
        and value.casefold() in forbidden_values
    ]

    if invalid_fields:
        raise ValueError(
            "Nicht zulässiger wörtlicher Fehlwert in: "
            + ", ".join(invalid_fields)
        )

    values["birth_date"] = parse_birth_date(
        values["birth_date"]
    )

    # Im Änderungspaket ist keine Straße enthalten.
    values["street"] = ""

    connection.execute(
        text(
            """
            INSERT INTO users_v2 (
                email,
                first_name,
                last_name,
                birth_date,
                street,
                postal_code,
                city,
                phone,
                gender
            )
            VALUES (
                :email,
                :first_name,
                :last_name,
                :birth_date,
                :street,
                :postal_code,
                :city,
                :phone,
                :gender
            )
            ON CONFLICT (email)
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                birth_date = EXCLUDED.birth_date,
                street = EXCLUDED.street,
                postal_code = EXCLUDED.postal_code,
                city = EXCLUDED.city,
                phone = EXCLUDED.phone,
                gender = EXCLUDED.gender
            """
        ),
        values,
    )


def process_hobby(
    connection,
    source_ref,
    element,
    seen_hobby_pairs,
):
    raw_email = normalize(element.get("email"))
    hobby_name = normalize(element.get("name"))
    raw_priority = normalize(element.get("priority"))

    if not raw_email or not hobby_name:
        raise ValueError(
            "E-Mail-Adresse oder Hobbyname fehlt"
        )

    canonical_email = find_user_email(
        connection,
        raw_email,
    )

    if canonical_email is None:
        raise ValueError(
            f"Unbekannte Person: {raw_email}"
        )

    priority = None

    if raw_priority is not None:
        try:
            priority = int(raw_priority)
        except ValueError as error:
            raise ValueError(
                f"Ungültige Priorität: {raw_priority!r}"
            ) from error

        if priority < -100 or priority > 100:
            raise ValueError(
                f"Priorität außerhalb -100 bis 100: "
                f"{priority}"
            )

    pair = (
        canonical_email.lower(),
        hobby_name,
    )

    if pair in seen_hobby_pairs:
        raise ValueError(
            "Doppelte Hobbyzuordnung innerhalb "
            "des Änderungspakets"
        )

    seen_hobby_pairs.add(pair)

    existing = connection.execute(
        text(
            """
            SELECT priority, source
            FROM user_hobbies
            WHERE email = :email
              AND hobby_name = :hobby_name
            """
        ),
        {
            "email": canonical_email,
            "hobby_name": hobby_name,
        },
    ).mappings().one_or_none()

    if existing is not None:
        # Derselbe XML-Datensatz wurde bereits bei einem
        # früheren Lauf erfolgreich verarbeitet.
        if (
            existing["source"] == "xml"
            and existing["priority"] == priority
        ):
            return

        raise ValueError(
            "Hobbyzuordnung ist bereits vorhanden"
        )

    connection.execute(
        text(
            """
            INSERT INTO hobbies (hobby_name)
            VALUES (:hobby_name)
            ON CONFLICT (hobby_name) DO NOTHING
            """
        ),
        {"hobby_name": hobby_name},
    )

    connection.execute(
        text(
            """
            INSERT INTO user_hobbies (
                email,
                hobby_name,
                priority,
                source
            )
            VALUES (
                :email,
                :hobby_name,
                :priority,
                'xml'
            )
            """
        ),
        {
            "email": canonical_email,
            "hobby_name": hobby_name,
            "priority": priority,
        },
    )


def process_like(
    connection,
    element,
):
    raw_email = normalize(element.get("email"))
    raw_target = normalize(
        element.get("target_email")
    )

    if not raw_email or not raw_target:
        raise ValueError(
            "Like enthält keine vollständigen Personenangaben"
        )

    liker_email = find_user_email(
        connection,
        raw_email,
    )
    liked_email = find_user_email(
        connection,
        raw_target,
    )

    if liker_email is None:
        raise ValueError(
            f"Unbekannte Ausgangsperson: {raw_email}"
        )

    if liked_email is None:
        raise ValueError(
            f"Unbekannte Zielperson: {raw_target}"
        )

    raise ValueError(
        "Like enthält weder Status noch Zeitpunkt"
    )


def process_xml_file(
    connection,
    source,
    data,
    source_refs,
):
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, UnicodeDecodeError) as error:
        for source_ref in source_refs:
            add_rejection(
                connection,
                source,
                source_ref,
                "XML kann gemäß deklarierter "
                "UTF-8-Kodierung nicht gelesen werden",
            )
        return

    counters = defaultdict(int)
    seen_hobby_pairs = set()

    for element in root.findall("./records/*"):
        record_type = element.tag
        counters[record_type] += 1

        source_ref = (
            f"/transferpack/records/"
            f"{record_type}[{counters[record_type]}]"
        )

        try:
            if record_type == "profile":
                process_profile(
                    connection,
                    source,
                    source_ref,
                    element,
                )
            elif record_type == "hobby":
                process_hobby(
                    connection,
                    source_ref,
                    element,
                    seen_hobby_pairs,
                )
            elif record_type == "like":
                process_like(
                    connection,
                    element,
                )
            else:
                raise ValueError(
                    f"Unbekannter Datensatztyp: "
                    f"{record_type}"
                )
        except (ValueError, TypeError) as error:
            add_rejection(
                connection,
                source,
                source_ref,
                str(error),
            )


def validate_archive():
    archive_data = ARCHIVE_PATH.read_bytes()
    archive_hash = sha256(archive_data)

    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            "Falsche SHA-256-Prüfsumme des Archivs: "
            f"{archive_hash}"
        )

    archive = zipfile.ZipFile(ARCHIVE_PATH)

    manifest = json.loads(
        archive.read("manifest.json").decode("utf-8")
    )

    if manifest["physical_record_count"] != 8:
        raise ValueError(
            "Manifest erwartet nicht genau 8 Datensätze"
        )

    for file_info in manifest["files"]:
        file_name = file_info["name"]
        data = archive.read(file_name)

        if sha256(data) != file_info["sha256"]:
            raise ValueError(
                f"Falsche Prüfsumme für {file_name}"
            )

    return archive, manifest


def main():
    archive, manifest = validate_archive()
    engine = create_engine(DATABASE_URL)

    refs_by_source = defaultdict(list)

    for item in manifest["source_refs"]:
        refs_by_source[item["source"]].append(
            item["source_ref"]
        )

    xml_files = [
        file_info["name"]
        for file_info in manifest["files"]
        if file_info["name"].endswith(".xml")
    ]

    with engine.begin() as connection:
        for source in xml_files:
            process_xml_file(
                connection,
                source,
                archive.read(source),
                refs_by_source[source],
            )

    archive.close()

    with engine.connect() as connection:
        counts = connection.execute(
            text(
                """
                SELECT
                    (SELECT count(*) FROM migration_users)
                        AS users,
                    (SELECT count(*)
                     FROM migration_user_hobbies)
                        AS hobbies,
                    (SELECT count(*)
                     FROM migration_likes)
                        AS likes,
                    (SELECT count(*)
                     FROM migration_rejections)
                        AS rejections
                """
            )
        ).mappings().one()

    print("V3-Änderungspaket erfolgreich verarbeitet")
    print("Personen:", counts["users"])
    print("Hobbyzuordnungen:", counts["hobbies"])
    print("Likes:", counts["likes"])
    print("Ablehnungen:", counts["rejections"])


if __name__ == "__main__":
    main()