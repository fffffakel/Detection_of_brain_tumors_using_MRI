   -- Инициализация базы данных (PostgreSQL)
   CREATE DATABASE IF NOT EXISTS YOUR_DB_NAME;
   CREATE USER YOUR_DB_USER WITH PASSWORD 'YOUR_DB_PASSWORD';
   ALTER ROLE YOUR_DB_USER SET client_encoding TO 'utf8';
   ALTER ROLE YOUR_DB_USER SET default_transaction_isolation TO 'read committed';
   ALTER ROLE YOUR_DB_USER SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE YOUR_DB_NAME TO YOUR_DB_USER;

   \connect YOUR_DB_NAME

   CREATE TABLE IF NOT EXISTS patients (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       age INT CHECK (age >= 0),
       gender VARCHAR(10) CHECK (gender IN ('male','female','other')),
       doctor_name TEXT NOT NULL,
       doctor_diagnosis TEXT NOT NULL,
       neural_diagnosis TEXT NOT NULL,
       server_path TEXT NOT NULL
   );