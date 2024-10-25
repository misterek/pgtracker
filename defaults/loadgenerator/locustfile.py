import time
import random
import string
import json
import psycopg2
from locust import User, task, between

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_email():
    username = generate_random_string(8)
    domain = generate_random_string(6)
    return f"{username}@{domain}.com"

def generate_random_json():
    themes = ['dark', 'light', 'auto']
    return {
        'preferences': {
            'theme': random.choice(themes),
            'notifications': random.choice([True, False])
        }
    }

class DatabaseUser(User):
    abstract = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conn = None
        self.connect_to_db()

    def connect_to_db(self):
        try:
            self.conn = psycopg2.connect(
                dbname="test",
                user="postgres",
                password="password",
                host="monitordb",
                port="5432"
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            self.environment.runner.quit()

    def on_stop(self):
        if self.conn:
            self.conn.close()

class MonitorDBUser(DatabaseUser):
    wait_time = between(1, 3)

    @task
    def insert_user(self):
        if not self.conn:
            self.connect_to_db()

        try:
            cursor = self.conn.cursor()
            
            username = f"user_{generate_random_string(8)}"
            password = generate_random_string(12)
            email = generate_random_email()
            status = random.choice(['active', 'inactive'])
            login_count = random.randint(0, 100)
            data = json.dumps(generate_random_json())

            start_time = time.time()
            
            cursor.execute("""
                INSERT INTO users (username, password, email, status, login_count, data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, password, email, status, login_count, data))
            
            total_time = int((time.time() - start_time) * 1000)
            
            # Report to Locust
            self.environment.events.request.fire(
                request_type="SQL",
                name="Insert User",
                response_time=total_time,
                response_length=0,
                exception=None,
            )
            
            cursor.close()

        except Exception as e:
            self.environment.events.request.fire(
                request_type="SQL",
                name="Insert User",
                response_time=0,
                response_length=0,
                exception=e,
            )
            print(f"Error inserting user: {e}")
            # Attempt to reconnect if connection was lost
            if "connection" in str(e).lower():
                self.connect_to_db()
