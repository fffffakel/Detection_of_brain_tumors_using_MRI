CREATE DATABASE IF NOT EXISTS BrainTutor;
CREATE USER BT_admin WITH PASSWORD '9234740892bt';
ALTER ROLE BT_admin SET client_encoding TO 'utf8';
ALTER ROLE BT_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE BT_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE BrainTutor TO BT_admin;

\connect BrainTutor

CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT CHECK (age >= 0),
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    doctor_name TEXT NOT NULL,
    doctor_diagnosis TEXT NOT NULL,
    neural_diagnosis TEXT NOT NULL,
    server_path TEXT NOT NULL
);