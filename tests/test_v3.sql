-- Eigene Prüfungen für LetsMeet V3

-- Mengen aller sechs Vertrags-Views
SELECT count(*) AS users
FROM migration_users;

SELECT count(*) AS interests
FROM migration_user_interests;

SELECT count(*) AS hobbies
FROM migration_user_hobbies;

SELECT count(*) AS likes
FROM migration_likes;

SELECT count(*) AS messages
FROM migration_messages;

SELECT count(*) AS rejections
FROM migration_rejections;


-- Verteilung der Hobbyquellen
SELECT
    source,
    count(*) AS assignments,
    count(priority) AS priorities_not_null
FROM migration_user_hobbies
GROUP BY source
ORDER BY source;


-- XML-Hobbys müssen priority = NULL besitzen
SELECT count(*) AS invalid_xml_priorities
FROM migration_user_hobbies
WHERE source = 'xml'
  AND priority IS NOT NULL;


-- Excel-Hobbys müssen eine gültige Priorität besitzen
SELECT count(*) AS invalid_excel_priorities
FROM migration_user_hobbies
WHERE source = 'excel'
  AND (
      priority IS NULL
      OR priority < -100
      OR priority > 100
  );


-- Fachlich gleiche Hobbyzuordnungen nur einmal
SELECT
    email,
    hobby_name,
    count(*)
FROM migration_user_hobbies
GROUP BY email, hobby_name
HAVING count(*) > 1;


-- Übernommene Profile aus dem Änderungspaket
SELECT
    email,
    first_name,
    last_name,
    birth_date,
    postal_code,
    city,
    phone,
    gender
FROM migration_users
WHERE email IN (
    'transfer.p2@letsmeet.invalid',
    'transfer.mojibake@letsmeet.invalid'
)
ORDER BY email;


-- Angenommene neue Hobbyzuordnung
SELECT
    email,
    hobby_name,
    priority,
    source
FROM migration_user_hobbies
WHERE email = 'acar.nehir@ge-em-ix.kom'
  AND hobby_name =
      'Abends seinem Partner Ereignisse des Tages erzählen';


-- Bereits aus Excel vorhandene Zuordnung
SELECT
    email,
    hobby_name,
    priority,
    source
FROM migration_user_hobbies
WHERE email = 'abdel.sabah@1mal1.te'
  AND hobby_name = 'E-Mails schreiben';


-- Alle Ablehnungen
SELECT
    source,
    source_ref,
    reason
FROM migration_rejections
ORDER BY source, source_ref;


-- Leere Ablehnungsgründe
SELECT count(*) AS empty_rejection_reasons
FROM migration_rejections
WHERE reason IS NULL
   OR btrim(reason) = '';


-- Eindeutigkeit der Ablehnungen
SELECT
    source,
    source_ref,
    count(*)
FROM migration_rejections
GROUP BY source, source_ref
HAVING count(*) > 1;


-- Pflicht-Views und Spaltentypen
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name LIKE 'migration_%'
ORDER BY table_name, ordinal_position;