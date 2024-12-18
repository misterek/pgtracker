import asyncio
import asyncpg
import time
import sys
import io
import csv
import boto3

class PostgresQueryScheduler:
    def __init__(self, dsn):
        """
        Initialize the query scheduler with the given DSN (database connection string).
        """
        self.dsn = dsn
        self.connection = None
        self.semaphore = asyncio.Semaphore(1)  # Ensures only one query runs at a time

    async def connect(self):
        """Establish a connection to PostgreSQL."""
        if not self.connection:
            self.connection = await asyncpg.connect(self.dsn)

    async def close(self):
        """Close the PostgreSQL connection."""
        if self.connection:
            await self.connection.close()

    async def run_query(self, query, filename):
        """
        Run a single query using the shared connection.
        Ensures that queries do not overlap by acquiring a semaphore.
        """
        async with self.semaphore:  # Ensures one query at a time
            print(f"Running query: {query}")
            start = time.time()
            async with self.connection.transaction():
                result = await self.connection.fetch(query)

            scrape_date = ""
            if result:
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_ALL)
                writer.writerow(result[0].keys())

                for row in result:
                    writer.writerow(row)

                    scrapedate = row[-1].strftime('%Y-%m-%d_%H_%M_%S')

                # Move the cursor to the start
                output.seek(0)

                s3_client = boto3.client(
                    's3',
                    endpoint_url="http://localstack:4566",  # Use custom URL if provided
                )
                s3_client.put_object(
                    Bucket="pgtracker",
                    Key=f"{filename}-{scrapedate}.csv",
                    Body=output.getvalue().encode('utf-8')
                )
            print(f"Query completed in {time.time() - start:.2f} seconds", file=sys.stderr)

    async def schedule_query(self, query, interval, filename):
        """
        Schedule a query to run at a specific interval.
        If reset_query is provided, execute it after the main query.
        """
        while True:
            await self.run_query(query, filename)
            await asyncio.sleep(interval)

    async def main(self, queries):
        """
        Start the scheduler for each query with its respective interval and filename.
        """
        await self.connect()  # Ensure connection is established

        # Create and schedule all query tasks
        tasks = []
        for query_info in queries:
            query, interval, filename = query_info
            tasks.append(self.schedule_query(query, interval, filename))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

# Example usage
if __name__ == "__main__":
    # Database connection string (replace with actual values)
    print("Sleeping")
    # I don't know why this sleep is required right now (probably something dumb with docker), 
    # But don't want to take the time to figure it out now.
    time.sleep(20)
    DATABASE_DSN = "postgresql://postgres:password@monitordb:5432/test?sslmode=disable"

    # Define queries, their intervals (in seconds), and filenames
    queries = [
        ("SELECT *, now() FROM pg_stat_activity;", 30, "pg_stat_activity"),
        ("""
        SELECT 
            *,
            now()
        FROM pg_stat_statements;
        """, 5, "pg_stat_statements"),
        ("SELECT version(), now(); ", 300, "version"),
        ("""
        SELECT oid, relname AS table_name, relnamespace::regnamespace AS schema_name, now()
FROM pg_class
WHERE relkind = 'r'  -- 'r' means regular table
  AND relnamespace::regnamespace NOT IN ('pg_catalog', 'information_schema');
  """, 5, "tables"),
  (
    """
    SELECT 
    i.oid AS index_oid,       -- OID of the index
    i.relname AS index_name,  -- Name of the index
    t.oid AS table_oid,       -- OID of the table the index belongs to
    s.nspname AS schema_name, -- Schema name
    pg_get_indexdef(i.oid) AS index_definition, -- SQL definition of the index
    now()
FROM 
    pg_class i
JOIN 
    pg_index ix ON i.oid = ix.indexrelid
JOIN 
    pg_class t ON ix.indrelid = t.oid
JOIN 
    pg_namespace s ON t.relnamespace = s.oid
WHERE 
    s.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY 
    s.nspname, i.relname;"""
  , 5, "index")

    ]

    print(DATABASE_DSN)
    # Initialize and run the scheduler
    scheduler = PostgresQueryScheduler(DATABASE_DSN)
    
    try:
        asyncio.run(scheduler.main(queries))
    except KeyboardInterrupt:
        print("Shutting down...")
        asyncio.run(scheduler.close())
