-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create users table with more columns for variable queries
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    status VARCHAR(20),
    login_count INTEGER DEFAULT 0,
    data JSONB
);

-- Create a large lookup table for joins
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    activity_type VARCHAR(50),
    activity_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, password, email, status, data) VALUES 
('alice', 'alice123', 'alice@example.com', 'active', '{"preferences": {"theme": "dark", "notifications": true}}'),
('bob', 'bob123', 'bob@example.com', 'active', '{"preferences": {"theme": "light", "notifications": false}}'),
('charlie', 'charlie123', 'charlie@example.com', 'inactive', '{"preferences": {"theme": "auto", "notifications": true}}'),
('david', 'david123', 'david@example.com', 'active', '{"preferences": {"theme": "dark", "notifications": false}}'),
('eve', 'eve123', 'eve@example.com', 'active', '{"preferences": {"theme": "light", "notifications": true}}'),
('frank', 'frank123', 'frank@example.com', 'inactive', '{"preferences": {"theme": "auto", "notifications": false}}');

-- Function to generate random string
CREATE OR REPLACE FUNCTION random_string(length INTEGER) RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::INTEGER, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to generate random activity data
CREATE OR REPLACE FUNCTION generate_activity_data() RETURNS void AS $$
DECLARE
    batch_size INTEGER;
    activity_types TEXT[] := ARRAY['login', 'logout', 'update_profile', 'change_password', 'view_page'];
    i INTEGER;
BEGIN
    -- Insert random activities
    batch_size := floor(random() * 50 + 10)::INTEGER;  -- 10 to 60 activities
    FOR i IN 1..batch_size LOOP
        INSERT INTO user_activities (user_id, activity_type, activity_data, created_at)
        VALUES (
            floor(random() * 6 + 1)::INTEGER,  -- random user_id 1-6
            activity_types[floor(random() * array_length(activity_types, 1) + 1)::INTEGER],
            jsonb_build_object(
                'ip_address', concat(
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT
                ),
                'user_agent', 'Mozilla/' || floor(random() * 5 + 1)::TEXT || '.0',
                'duration_ms', floor(random() * 5000)::INTEGER
            ),
            NOW() - (random() * interval '1 hour')
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create a function to generate varying query activity
CREATE OR REPLACE FUNCTION generate_activity() RETURNS void AS $$
DECLARE
    iterations INTEGER;
    sleep_interval DECIMAL;
    batch_size INTEGER;
    complex_query TEXT;
    random_status TEXT;
    random_theme TEXT;
    user_stats RECORD;
BEGIN
    -- Generate new activity data
    IF random() < 0.3 THEN  -- 30% chance to generate new activities
        PERFORM generate_activity_data();
    END IF;

    -- Random number of iterations (between 2 and 8)
    iterations := floor(random() * 7 + 2)::INTEGER;
    
    -- Run varying SELECT queries
    FOR i IN 1..iterations LOOP
        -- Random sleep between queries (0.1 to 1 seconds)
        sleep_interval := (random() * 0.9 + 0.1);
        PERFORM pg_sleep(sleep_interval);
        
        -- Mix of different queries with varying complexity
        CASE floor(random() * 8)::INTEGER
            WHEN 0 THEN
                -- Simple count with random condition
                PERFORM COUNT(*) FROM users 
                WHERE login_count >= floor(random() * 10)::INTEGER;
            
            WHEN 1 THEN
                -- Complex join with aggregation
                FOR user_stats IN
                    WITH user_stats AS (
                        SELECT 
                            u.id,
                            COUNT(ua.id) as activity_count,
                            MAX(ua.created_at) as last_activity
                        FROM users u
                        LEFT JOIN user_activities ua ON u.id = ua.user_id
                        GROUP BY u.id
                    )
                    SELECT * FROM user_stats
                    WHERE activity_count > floor(random() * 5)::INTEGER
                LOOP
                    -- Just iterate through results
                    NULL;
                END LOOP;
            
            WHEN 2 THEN
                -- JSON query with random theme
                SELECT CASE floor(random() * 3)::INTEGER
                    WHEN 0 THEN 'dark'
                    WHEN 1 THEN 'light'
                    ELSE 'auto'
                END INTO random_theme;
                
                PERFORM * FROM users 
                WHERE data->'preferences'->>'theme' = random_theme;
            
            WHEN 3 THEN
                -- Window function with random ordering
                FOR user_stats IN
                    SELECT * FROM (
                        SELECT 
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY status 
                                ORDER BY CASE floor(random() * 3)::INTEGER
                                    WHEN 0 THEN username
                                    WHEN 1 THEN created_at::TEXT
                                    ELSE id::TEXT
                                END
                            ) as rn
                        FROM users
                    ) sub
                    WHERE rn <= floor(random() * 3 + 1)::INTEGER
                LOOP
                    -- Just iterate through results
                    NULL;
                END LOOP;
            
            WHEN 4 THEN
                -- Activity analysis with time window
                FOR user_stats IN
                    SELECT 
                        user_id,
                        activity_type,
                        COUNT(*) as activity_count
                    FROM user_activities
                    WHERE created_at > NOW() - (random() * interval '1 hour')
                    GROUP BY user_id, activity_type
                    HAVING COUNT(*) > floor(random() * 3)::INTEGER
                LOOP
                    -- Just iterate through results
                    NULL;
                END LOOP;
            
            WHEN 5 THEN
                -- Complex subquery with multiple conditions
                PERFORM * FROM users u
                WHERE EXISTS (
                    SELECT 1 FROM user_activities ua
                    WHERE ua.user_id = u.id
                    AND ua.activity_type = ANY(
                        ARRAY['login', 'update_profile']::VARCHAR[]
                    )
                    AND (ua.activity_data->>'duration_ms')::INTEGER > 
                        floor(random() * 1000 + 500)::INTEGER
                );
            
            WHEN 6 THEN
                -- Random status update
                SELECT CASE floor(random() * 3)::INTEGER
                    WHEN 0 THEN 'active'
                    WHEN 1 THEN 'inactive'
                    ELSE 'suspended'
                END INTO random_status;
                
                UPDATE users 
                SET status = random_status,
                    last_login = CASE 
                        WHEN random() > 0.5 THEN NOW()
                        ELSE last_login
                    END
                WHERE random() > 0.7;
            
            ELSE
                -- Cleanup old activities with random threshold
                DELETE FROM user_activities
                WHERE id IN (
                    SELECT id FROM user_activities
                    ORDER BY created_at ASC
                    LIMIT floor(random() * 10)::INTEGER
                );
        END CASE;
    END LOOP;

    -- Random batch of user updates
    batch_size := floor(random() * 3 + 1)::INTEGER;
    FOR i IN 1..batch_size LOOP
        INSERT INTO users (
            username, 
            password, 
            email, 
            status,
            login_count,
            data
        ) VALUES (
            'temp_' || random_string(8),
            random_string(12),
            'temp_' || random_string(8) || '@example.com',
            CASE floor(random() * 3)::INTEGER
                WHEN 0 THEN 'active'
                WHEN 1 THEN 'inactive'
                ELSE 'suspended'
            END,
            floor(random() * 100)::INTEGER,
            jsonb_build_object(
                'preferences', jsonb_build_object(
                    'theme', CASE floor(random() * 3)::INTEGER
                        WHEN 0 THEN 'dark'
                        WHEN 1 THEN 'light'
                        ELSE 'auto'
                    END,
                    'notifications', random() > 0.5
                ),
                'last_ip', concat(
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT, '.',
                    floor(random() * 256)::TEXT
                )
            )
        );
    END LOOP;

    -- Cleanup with varying conditions
    DELETE FROM users 
    WHERE username LIKE 'temp_%'
    AND (
        random() > 0.7 
        OR login_count > floor(random() * 50 + 50)::INTEGER
        OR status = 'suspended'
    );
END;
$$ LANGUAGE plpgsql;

-- Generate initial activity
SELECT generate_activity();
