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

-- Create a function to generate some query activity
CREATE OR REPLACE FUNCTION generate_activity() RETURNS void AS $$
BEGIN
    -- Run some SELECT queries
    FOR i IN 1..5 LOOP
        PERFORM COUNT(*) FROM users;
        PERFORM * FROM users WHERE username LIKE 'a%';
        PERFORM * FROM users WHERE id > 3;
        PERFORM * FROM users ORDER BY username;
    END LOOP;
    
    -- Run some INSERT/UPDATE/DELETE queries
    INSERT INTO users (username, password) 
    VALUES ('temp_user', 'temp_pass');
    
    UPDATE users SET password = 'updated_pass' 
    WHERE username = 'temp_user';
    
    DELETE FROM users 
    WHERE username = 'temp_user';
END;
$$ LANGUAGE plpgsql;

-- Generate initial activity
SELECT generate_activity();
