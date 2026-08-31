-- Eigene Tests für LetsMeet V2

-- Mengenprüfungen
SELECT count(*) AS users FROM migration_users;
SELECT count(*) AS interests FROM migration_user_interests;
SELECT count(*) AS hobbies FROM migration_user_hobbies;
SELECT count(*) AS likes FROM migration_likes;
SELECT count(*) AS messages FROM migration_messages;

-- Leere oder doppelte E-Mail-Adressen
SELECT count(*) AS empty_emails
FROM migration_users
WHERE email IS NULL OR email = '';

SELECT lower(email), count(*)
FROM migration_users
GROUP BY lower(email)
HAVING count(*) > 1;

-- Doppelte Interessen
SELECT email, interest_code, count(*)
FROM migration_user_interests
GROUP BY email, interest_code
HAVING count(*) > 1;

-- Doppelte Hobbys derselben Quelle
SELECT email, hobby_name, source, count(*)
FROM migration_user_hobbies
GROUP BY email, hobby_name, source
HAVING count(*) > 1;

-- Prioritäten außerhalb des vereinbarten Bereichs
SELECT count(*) AS invalid_priorities
FROM migration_user_hobbies
WHERE priority < -100 OR priority > 100;

-- Falsche Herkunft
SELECT count(*) AS invalid_sources
FROM migration_user_hobbies
WHERE source <> 'excel';

-- Likes mit unbekannten Personen
SELECT count(*) AS invalid_like_references
FROM migration_likes AS l
LEFT JOIN migration_users AS liker
    ON liker.email = l.liker_email
LEFT JOIN migration_users AS liked
    ON liked.email = l.liked_email
WHERE liker.email IS NULL OR liked.email IS NULL;

-- Nachrichten mit unbekannten Personen
SELECT count(*) AS invalid_message_references
FROM migration_messages AS m
LEFT JOIN migration_users AS sender
    ON sender.email = m.sender_email
LEFT JOIN migration_users AS receiver
    ON receiver.email = m.receiver_email
WHERE sender.email IS NULL OR receiver.email IS NULL;

-- Kundinnenentscheidung: MongoDB hat Vorrang
SELECT email, first_name, last_name, phone
FROM migration_users
WHERE email IN (
    'julia.nagel@d-ohnline.ork',
    'katharina.prommer@autluuk.kom',
    'birgit.voss@gmaiil.ork'
);

-- Spalten und Typen aller Pflicht-Views
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name LIKE 'migration_%'
ORDER BY table_name, ordinal_position;