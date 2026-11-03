INSERT INTO users (id_user, email, password_hash, role_user, token, is_banned) VALUES
    (1, 'alice@test.com', 'password1', 'user', 'token_alice', FALSE),
    (2, 'bob@test.com', 'password2', 'user', 'token_bob', FALSE),
    (3, 'admin@test.com', 'password3', 'admin', 'token_admin', FALSE),
    (4, 'banned@test.com', 'password4', 'user', 'token_banned', TRUE),
    (5, 'empty@test.com', 'password5', 'user', 'token_empty', FALSE);

INSERT INTO neo (id_neo, nasa_id, name_neo, diameter_min_m, diameter_max_m, absolute_magnitude, is_hazardous, is_custom, created_by_user_id) VALUES
    (1, '2000433', 'Eros', 10.0, 20.0, 22.5, FALSE, FALSE, NULL),
    (2, '2099942', 'Apophis', 300.0, 400.0, 19.7, TRUE, FALSE, NULL),
    (3, '2101955', 'Bennu', 480.0, 520.0, 20.2, TRUE, FALSE, NULL),
    (4, 'CUSTOM1', 'Custom Alice', 5.0, 8.0, 25.0, FALSE, TRUE, 1),
    (5, 'CUSTOM2', 'Custom Bob', 15.0, 25.0, 23.0, FALSE, TRUE, 2),
    (6, '2000001', 'Orphan', 50.0, 60.0, 21.0, FALSE, FALSE, NULL);

INSERT INTO close_approach (id_close_approach, id_neo, orbiting_body, approach_date, miss_distance_km, relative_velocity_kmh) VALUES
    (1, 1, 'Earth', '2026-01-15', 1000000.0, 40000.0),
    (2, 1, 'Mars', '2026-03-10', 2500000.0, 35000.0),
    (3, 2, 'Earth', '2026-04-13', 31000.0, 60000.0),
    (4, 3, 'Earth', '2026-09-25', 750000.0, 28000.0);

INSERT INTO login_history (id_login, id_user, login_at) VALUES
    (1, 1, '2026-10-01 08:00:00'),
    (2, 1, '2026-10-02 09:30:00'),
    (3, 2, '2026-10-02 10:00:00'),
    (4, 3, '2026-10-03 07:45:00');

INSERT INTO alert (id_alert, id_user, id_neo, threshold_km, threshold_size, is_active) VALUES
    (1, 1, 1, 1000000.0, 10.0, TRUE),
    (2, 1, NULL, 500000.0, 100.0, TRUE),
    (3, 2, 2, 100000.0, 50.0, FALSE);

INSERT INTO favorite (id_favorite, id_user, id_neo) VALUES
    (1, 1, 1),
    (2, 1, 2),
    (3, 2, 3);

INSERT INTO distance_history (id_distance_history, id_favorite, recorded_at, distance_km) VALUES
    (1, 1, '2026-01-01', 1200000.0),
    (2, 1, '2026-01-08', 1100000.0),
    (3, 2, '2026-04-01', 80000.0);

SELECT setval(pg_get_serial_sequence('users', 'id_user'), MAX(id_user)) FROM users;
SELECT setval(pg_get_serial_sequence('neo', 'id_neo'), MAX(id_neo)) FROM neo;
SELECT setval(pg_get_serial_sequence('close_approach', 'id_close_approach'), MAX(id_close_approach)) FROM close_approach;
SELECT setval(pg_get_serial_sequence('login_history', 'id_login'), MAX(id_login)) FROM login_history;
SELECT setval(pg_get_serial_sequence('alert', 'id_alert'), MAX(id_alert)) FROM alert;
SELECT setval(pg_get_serial_sequence('favorite', 'id_favorite'), MAX(id_favorite)) FROM favorite;
SELECT setval(pg_get_serial_sequence('distance_history', 'id_distance_history'), MAX(id_distance_history)) FROM distance_history;