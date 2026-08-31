-- Eigene Prüfungen für Datenvertrag V1

-- Test 1: ожидается 1576 строк
SELECT
    count(*) AS imported_users
FROM migration_users;

-- Test 2: ожидается 0 пустых email
SELECT
    count(*) AS empty_emails
FROM migration_users
WHERE email IS NULL OR email = '';

-- Test 3: запрос не должен вернуть строк
SELECT
    email,
    count(*) AS occurrence_count
FROM migration_users
GROUP BY email
HAVING count(*) > 1;

-- Test 4: ожидается 0 незаполненных обязательных значений
SELECT
    count(*) AS incomplete_users
FROM migration_users
WHERE first_name IS NULL
   OR last_name IS NULL
   OR birth_date IS NULL
   OR postal_code IS NULL
   OR city IS NULL;

-- Test 5: проверка названий и типов столбцов
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'migration_users'
ORDER BY ordinal_position;

-- Test 6: пример города с запятой должен сохраниться полностью
SELECT
    email,
    city
FROM migration_users
WHERE city = 'Demmin, Hansestadt';

-- Test 7: количество строк View и исходной таблицы должно совпадать
SELECT
    (SELECT count(*) FROM users_v1) AS table_rows,
    (SELECT count(*) FROM migration_users) AS view_rows;