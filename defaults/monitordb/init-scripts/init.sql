-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL
);

-- Insert sample data
INSERT INTO users (username, password) VALUES 
('alice', 'alice123'),
('bob', 'bob123'),
('charlie', 'charlie123'),
('david', 'david123'),
('eve', 'eve123'),
('frank', 'frank123');
