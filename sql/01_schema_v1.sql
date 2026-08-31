-- Akt 1: PostgreSQL-Zielstruktur für LetsMeet

DROP VIEW IF EXISTS migration_users;
DROP TABLE IF EXISTS users_v1;

CREATE TABLE users_v1 (
    email        text PRIMARY KEY,
    first_name   text NOT NULL,
    last_name    text NOT NULL,
    birth_date   date NOT NULL,
    postal_code  text NOT NULL,
    city         text NOT NULL
);

CREATE VIEW migration_users AS
SELECT
    email,
    first_name,
    last_name,
    birth_date,
    postal_code,
    city
FROM users_v1;