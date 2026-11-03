CREATE SCHEMA IF NOT EXISTS NEOW;

CREATE TABLE users (
    id_user         SERIAL PRIMARY KEY,
    email           VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255),
    role_user       VARCHAR(20),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token           VARCHAR(255),
    is_banned       BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE neo (
    id_neo                SERIAL PRIMARY KEY,
    nasa_id               VARCHAR(15) NOT NULL,
    name_neo              VARCHAR(50) NOT NULL,
    diameter_min_m        FLOAT,
    diameter_max_m        FLOAT,
    absolute_magnitude    FLOAT,
    is_hazardous          BOOLEAN,
    is_custom             BOOLEAN,
    created_by_user_id    INT REFERENCES users(id_user)
);

CREATE TABLE close_approach (
    id_close_approach       SERIAL PRIMARY KEY,
    id_neo                  INT REFERENCES neo(id_neo),
    orbiting_body           VARCHAR(30),
    approach_date           DATE,
    miss_distance_km        FLOAT,
    relative_velocity_kmh   FLOAT);


CREATE TABLE login_history (
    id_login    SERIAL PRIMARY KEY,
    id_user     INT REFERENCES users(id_user),
    login_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert (
    id_alert          SERIAL PRIMARY KEY,
    id_user           INT REFERENCES users(id_user),
    id_neo            INT REFERENCES neo(id_neo) NULL,
    threshold_km      FLOAT,
    threshold_size    FLOAT,
    is_active         BOOLEAN,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE favorite (
    id_favorite SERIAL PRIMARY KEY,
    id_user     INT REFERENCES users(id_user),
    id_neo      INT REFERENCES neo(id_neo),
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE distance_history (
    id_distance_history SERIAL PRIMARY KEY,
    id_favorite         INT REFERENCES favorite(id_favorite),
    recorded_at         DATE,
    distance_km         FLOAT
);