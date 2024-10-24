import boto3
import json
import time
import os
import sys
import psycopg2
import csv
import io
from datetime import datetime

# Initialize AWS clients with localstack endpoint
endpoint_url = "http://localstack:4566"
sqs = boto3.client('sqs',
    endpoint_url=endpoint_url,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

s3 = boto3.client('s3',
    endpoint_url=endpoint_url,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

# Get queue URL
queue_url = f"{endpoint_url}/000000000000/pgtracker-queue"

def get_db_connection():
    return psycopg2.connect(
        dbname="pgtracker",
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        host=os.environ.get("POSTGRES_HOST", "pgtrackerdb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )

def convert_empty_to_null(record):
    # Fields that should be converted to integers
    int_fields = ['datid', 'pid', 'usesysid', 'client_port']
    
    for field in int_fields:
        if field in record and (record[field] == '' or record[field] == 'None' or record[field] is None):
            record[field] = None
        elif field in record and record[field] is not None:
            try:
                record[field] = int(record[field])
            except (ValueError, TypeError):
                record[field] = None
    return record

def insert_pg_stat_activity(conn, data):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO psa (
                    datid, datname, pid, usesysid, usename, application_name,
                    client_addr, client_hostname, client_port, backend_start, xact_start,
                    query_start, state_change, wait_event_type, wait_event, state,
                    backend_xid, backend_xmin, query, backend_type, sample_time
                ) VALUES (
                    %(datid)s, %(datname)s, %(pid)s, %(usesysid)s, %(usename)s, 
                    %(application_name)s, %(client_addr)s, %(client_hostname)s,
                    %(client_port)s, %(backend_start)s, %(xact_start)s, %(query_start)s,
                    %(state_change)s, %(wait_event_type)s, %(wait_event)s, %(state)s,
                    %(backend_xid)s, %(backend_xmin)s, %(query)s, %(backend_type)s,
                    %(sample_time)s
                )
            """, data)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def process_csv_to_dict(csv_content):
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)
    return list(reader)

def process_message(message):
    try:
        # Parse the message body
        body = json.loads(message['Body'])
        
        # Extract S3 event details
        if 'Records' in body:
            for record in body['Records']:
                if record['eventName'].startswith('ObjectCreated:'):
                    bucket = record['s3']['bucket']['name']
                    key = record['s3']['object']['key']
                    
                    sys.stderr.write(f"Downloading file: {key} from bucket: {bucket}\n")
                    
                    # Download file into memory from S3
                    response = s3.get_object(Bucket=bucket, Key=key)
                    file_content = response['Body'].read().decode('utf-8')
                    
                    sys.stderr.write(f"Successfully downloaded file into memory\n")
                    
                    # Process pg_stat_activity data
                    if key.startswith('pg_stat_activity'):
                        conn = get_db_connection()
                        try:
                            data_list = process_csv_to_dict(file_content)
                            # Convert timestamp strings to datetime objects
                            timestamp_fields = ['backend_start', 'xact_start', 'query_start', 'state_change']
                            for record in data_list:
                                # Convert empty strings and 'None' to None for all fields
                                for key, value in record.items():
                                    if value == 'None' or value == '':
                                        record[key] = None
                                
                                # Convert numeric fields
                                record = convert_empty_to_null(record)
                                
                                # Handle timestamps
                                for field in timestamp_fields:
                                    if record.get(field):
                                        record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                                # Use the last column (now()) as sample_time
                                record['sample_time'] = datetime.fromisoformat(record.pop('now').replace('Z', '+00:00'))
                                
                                insert_pg_stat_activity(conn, record)
                            sys.stderr.write(f"Successfully processed pg_stat_activity data\n")
                        except Exception as e:
                            sys.stderr.write(f"Error processing pg_stat_activity data: {str(e)}\n")
                            raise e
                        finally:
                            conn.close()
                    else:
                        # Process other file types as before
                        for line in file_content.splitlines():
                            sys.stderr.write(f"Line: {line}\n")
                    
        return True
    except Exception as e:
        sys.stderr.write(f"Error processing message: {str(e)}\n")
        return False

def main():
    sys.stderr.write("Starting SQS message processor...\n")
    
    while True:
        try:
            # Receive messages from SQS
            sys.stderr.write(f"{queue_url}")
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20  # Long polling
            )
            
            # Process messages if any
            if 'Messages' in response:
                for message in response['Messages']:
                    if process_message(message):
                        # Delete successfully processed message
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
            
        except Exception as e:
            sys.stderr.write(f"Error receiving messages: {str(e)}\n")
            time.sleep(5)  # Wait before retrying on error

if __name__ == "__main__":
    main()
