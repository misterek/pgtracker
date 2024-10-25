import boto3
import json
import time
import os
import sys
import psycopg2
import csv
import io
import re
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
    # Fields that should be converted to integers/bigints
    int_fields = ['datid', 'pid', 'usesysid', 'client_port']
    bigint_fields = ['queryid', 'calls', 'rows']
    float_fields = ['total_time']
    
    for field in int_fields:
        if field in record and (record[field] == '' or record[field] == 'None' or record[field] is None):
            record[field] = None
        elif field in record and record[field] is not None:
            try:
                record[field] = int(record[field])
            except (ValueError, TypeError):
                record[field] = None
                
    for field in bigint_fields:
        if field in record and (record[field] == '' or record[field] == 'None' or record[field] is None):
            record[field] = None
        elif field in record and record[field] is not None:
            try:
                record[field] = int(record[field])
            except (ValueError, TypeError):
                record[field] = None
                
    for field in float_fields:
        if field in record and (record[field] == '' or record[field] == 'None' or record[field] is None):
            record[field] = None
        elif field in record and record[field] is not None:
            try:
                record[field] = float(record[field])
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

def insert_pg_stat_statements(conn, data):
    try:
        with conn.cursor() as cur:
            table_name = "pss"
            columns = ', '.join(data.keys())
            values_placeholders = ', '.join([f'%({key})s' for key in data.keys()])

            query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({values_placeholders});
            """

            cur.execute(query, data)
            conn.commit()
    
    except Exception as e:
        conn.rollback()
        raise e

def insert_version_info(conn, data):
    sys.stderr.write(f"{data}")
    data = data[0]

    try:
        with conn.cursor() as cur:
            # Check if version info already exists
            cur.execute("SELECT COUNT(*) FROM db_info")
            
            sys.stderr.write(f"A\n")

            count = cur.fetchone()[0]
            sys.stderr.write(f"B\n")

            if count == 0:
                # Insert new version info if table is empty
                full_version = data['version']
                version = full_version.split()[1]
                sys.stderr.write(f"C\n")
                cur.execute("""
                    INSERT INTO db_info (full_version, version)
                    VALUES (%s, %s)
                """, (full_version, version))
                sys.stderr.write(f"D\n")

            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def insert_tables_info(conn, data):
    try:
        with conn.cursor() as cur:

            
            # Insert new table data
            for record in data:
                cur.execute("""
                    INSERT INTO tables (name, oid, schema)
                    VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
                """, (record['table_name'], record['oid'], record['schema_name']))
            
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
            for s3_record in body['Records']:
                if s3_record['eventName'].startswith('ObjectCreated:'):
                    bucket = s3_record['s3']['bucket']['name']
                    file_key = s3_record['s3']['object']['key']
                    
                    sys.stderr.write(f"Downloading file: {file_key} from bucket: {bucket}\n")
                    
                    # Download file into memory from S3
                    response = s3.get_object(Bucket=bucket, Key=file_key)
                    file_content = response['Body'].read().decode('utf-8')
                    
                    sys.stderr.write(f"Successfully downloaded file into memory\n")
                    
                    conn = get_db_connection()
                    try:
                        if 'version' in file_key:
                            insert_version_info(conn, process_csv_to_dict(file_content))
                        elif 'tables' in file_key:
                            insert_tables_info(conn, process_csv_to_dict(file_content))
                        else:
                            # Handle CSV files (activity and statements)
                            data_list = process_csv_to_dict(file_content)
                            timestamp_fields = ['backend_start', 'xact_start', 'query_start', 'state_change']
                            
                            for record in data_list:
                                # Convert empty strings and 'None' to None for all fields
                                for field_name, value in record.items():
                                    if value == 'None' or value == '':
                                        record[field_name] = None
                                
                                # Convert numeric fields
                                record = convert_empty_to_null(record)
                                
                                # Handle timestamps based on file type
                                if 'pg_stat_activity' in file_key:
                                    for field in timestamp_fields:
                                        if record.get(field):
                                            record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                                    record['sample_time'] = datetime.fromisoformat(record.pop('now').replace('Z', '+00:00'))
                                    insert_pg_stat_activity(conn, record)
                                elif 'pg_stat_statements' in file_key:
                                    record['sample_time'] = datetime.fromisoformat(record.pop('now').replace('Z', '+00:00'))
                                    insert_pg_stat_statements(conn, record)
                                
                        sys.stderr.write(f"Successfully processed {file_key} data\n")
                    except Exception as e:
                        sys.stderr.write(f"Error processing data: {str(e)}\n")
                        raise e
                    finally:
                        conn.close()
                    
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
