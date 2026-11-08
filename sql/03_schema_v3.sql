-- Akt 3: PostgreSQL-Zielstruktur
DROP VIEW IF EXISTS migration_rejections;
DROP VIEW IF EXISTS migration_messages;
DROP VIEW IF EXISTS migration_likes;
DROP VIEW IF EXISTS migration_user_hobbies;
DROP VIEW IF EXISTS migration_user_interests;
DROP VIEW IF EXISTS migration_users;

DROP TABLE IF EXISTS rejections CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS likes CASCADE;
DROP TABLE IF EXISTS friendships CASCADE;
DROP TABLE IF EXISTS user_sought_hobbies CASCADE;
DROP TABLE IF EXISTS photos CASCADE;
DROP TABLE IF EXISTS user_hobbies CASCADE;
DROP TABLE IF EXISTS hobbies CASCADE;
DROP TABLE IF EXISTS user_interests CASCADE;
DROP TABLE IF EXISTS users_v2 CASCADE;

CREATE TABLE users_v2 (
    email        text PRIMARY KEY,
    first_name   text NOT NULL,
    last_name    text NOT NULL,
    birth_date   date NOT NULL,
    street       text NOT NULL,
    postal_code  text NOT NULL,
    city         text NOT NULL,
    phone        text NOT NULL,
    gender       text NOT NULL
);

CREATE TABLE hobbies (
    hobby_name text PRIMARY KEY
);

CREATE TABLE user_interests (
    email          text NOT NULL
                   REFERENCES users_v2(email),
    interest_code  text NOT NULL,
    PRIMARY KEY (email, interest_code)
);

CREATE TABLE user_hobbies (
    email       text NOT NULL
                REFERENCES users_v2(email),
    hobby_name  text NOT NULL
                REFERENCES hobbies(hobby_name),
    priority    integer
                CHECK (
                    priority IS NULL
                    OR priority BETWEEN -100 AND 100
                ),
    source      text NOT NULL
                CHECK (source IN ('excel', 'xml')),
    PRIMARY KEY (email, hobby_name)
);

CREATE TABLE photos (
    photo_id    bigserial PRIMARY KEY,
    email       text NOT NULL
                REFERENCES users_v2(email),
    dateiname   text NOT NULL,
    profilbild  boolean NOT NULL DEFAULT false
);

CREATE TABLE user_sought_hobbies (
    email        text NOT NULL
                 REFERENCES users_v2(email),
    hobby_name   text NOT NULL
                 REFERENCES hobbies(hobby_name),
    praeferenz   integer NOT NULL
                 CHECK (praeferenz BETWEEN -100 AND 100),
    PRIMARY KEY (email, hobby_name)
);

CREATE TABLE friendships (
    person_a_email  text NOT NULL
                    REFERENCES users_v2(email),
    person_b_email  text NOT NULL
                    REFERENCES users_v2(email),
    PRIMARY KEY (person_a_email, person_b_email),
    CHECK (person_a_email <> person_b_email)
);

CREATE TABLE likes (
    liker_email  text NOT NULL
                 REFERENCES users_v2(email),
    liked_email  text NOT NULL
                 REFERENCES users_v2(email),
    status       text NOT NULL,
    liked_at     timestamp NOT NULL,
    PRIMARY KEY (liker_email, liked_email)
);

CREATE TABLE messages (
    message_id       bigserial PRIMARY KEY,
    sender_email     text NOT NULL
                     REFERENCES users_v2(email),
    receiver_email   text NOT NULL
                     REFERENCES users_v2(email),
    body             text NOT NULL,
    sent_at          timestamp NOT NULL,
    conversation_id  integer NOT NULL
);

CREATE TABLE rejections (
    source      text NOT NULL,
    source_ref  text NOT NULL,
    reason      text NOT NULL
                CHECK (btrim(reason) <> ''),
    PRIMARY KEY (source, source_ref)
);

CREATE VIEW migration_users AS
SELECT
    email,
    first_name,
    last_name,
    birth_date,
    postal_code,
    city,
    phone,
    gender
FROM users_v2;

CREATE VIEW migration_user_interests AS
SELECT
    email,
    interest_code
FROM user_interests;

CREATE VIEW migration_user_hobbies AS
SELECT
    email,
    hobby_name,
    priority,
    source
FROM user_hobbies;

CREATE VIEW migration_likes AS
SELECT
    liker_email,
    liked_email,
    status,
    liked_at
FROM likes;

CREATE VIEW migration_messages AS
SELECT
    sender_email,
    receiver_email,
    body,
    sent_at,
    conversation_id
FROM messages;

CREATE VIEW migration_rejections AS
SELECT
    source,
    source_ref,
    reason
FROM rejections;