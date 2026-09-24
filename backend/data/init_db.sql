CREATE SCHEMA NEOW;

DROP TABLE IF EXISTS NEOW.users;

CREATE TABLE NEOW.users (
    id_user         SERIAL PRIMARY KEY,
    email           VARCHAR(50) NOT NULL,
    password_hash   VARCHAR(20),
    role_user       VARCHAR(20),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

DROP TABLE IF EXISTS NEOW.neo;

CREATE TABLE NEOW.neo (
	id_neo  SERIAL PRIMARY KEY,
	nasa_id  VARCHAR(15) NOT NULL,
	name_neo VARCHAR(50) NOT NULL,
	diameter_min_m FLOAT,
	diameter_max_m FLOAT,
	absolute_magnitude FLOAT,
	is_hazardous BOOLEAN,
	is_custom BOOLEAN,
	created_by_user_id INT REFERENCES users(id_user));

DROP TABLE IF EXISTS NEOW.login_history;

CREATE TABLE NEOW.login_history (
	id_login SERIAL PRIMARY KEY,
	id_user INT REFERENCES users(id_user),
	login_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	ip_address VARCHAR(20));

DROP TABLE IF EXISTS NEOW.alert;

CREATE TABLE NEOW.alert (
	id_alert SERIAL PRIMARY KEY,
	id_user INT REFERENCES users(id_user),
	id_neo INT REFERENCES neo(id_neo),
	min_size_m FLOAT,
	max_distance_km FLOAT,
	is_active BOOLEAN,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

DROP TABLE IF EXISTS NEOW.notification;

CREATE TABLE NEOW.notification (
	id_notification SERIAL PRIMARY KEY,
	id_user INT REFERENCES users(id_user),
	id_alert INT REFERENCES alert(id_alert),
	message TEXT,
	sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

DROP TABLE IF EXISTS NEOW.close_approach;

CREATE TABLE NEOW.close_approach (
	id_close_approach SERIAL PRIMARY KEY,
	id_neo INT REFERENCES neo(id_neo),
	approach_date DATE,
	miss_distance_km FLOAT,
	relative_velocity_kmh FLOAT);

DROP TABLE IF EXISTS NEOW.favorite;

CREATE TABLE NEOW.favorite (
	id_favorite SERIAL PRIMARY KEY,
	id_user INT REFERENCES users(id_user),
	id_neo INT REFERENCES neo(id_neo),
	added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

DROP TABLE IF EXISTS NEOW.distance_history;

CREATE TABLE NEOW.distance_history (
	id_distance_history SERIAL PRIMARY KEY,
	id_favorite INT REFERENCES favorite(id_favorite),
	recorded_at DATE,
	distance_km FLOAT);