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

    def format_csv_value(self, value):
        """Format a single value for CSV."""
        if value is None:
            return '""'
        return f'"{str(value).replace(\'"\', \'\\"\')}"\n'

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
                lines = []
                
                # Get column names from the first row
                keys = result[0].keys()
                header = ','.join(f'"{key}"' for key in keys)
                lines.append(header + '\n')

                # Format each row
                for row in result:
                    values = [self.format_csv_value(row[key]).strip() for key in keys]
                    lines.append(','.join(values) + '\n')
                    scrapedate = row[-1].strftime('%Y-%m-%d_%H_%M_%S')

                # Join all lines
                output = ''.join(lines)

                s3_client = boto3.client(
                    's3',
                    endpoint_url="http://localstack:4566",  # Use custom URL if provided
                )
                s3_client.put_object(
                    Bucket="pgtracker",
                    Key=f"{filename}-{scrapedate}.csv",
                    Body=output.encode('utf-8')
                )
            print(f"Query completed in {time.time() - start:.2f} seconds", file=sys.stderr)

    async def schedule_query(self, query, interval, filename):
        """
        Schedule a query to run at a specific interval.
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
        tasks = [
            self.schedule_query(query, interval, filename)
            for query, interval, filename in queries
        ]

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
        ("SELECT *,now() FROM pg_stat_activity;", 30, "pg_stat_activity"),
    ]

    print(DATABASE_DSN)
    # Initialize and run the scheduler
    scheduler = PostgresQueryScheduler(DATABASE_DSN)
    
    try:
        asyncio.run(scheduler.main(queries))
    except KeyboardInterrupt:
        print("Shutting down...")
        asyncio.run(scheduler.close())
