# pgtracker
Track the historical performance of a Postgres Database

## Summary
The primary goal of this is as a learning project.  I don't expect to invent any new magic here.

This project will give a history of some important tables that will allow you to see what and how your database was doing over time.

Think of having a snapshot of pg_stat_activity or pg_locks every 30 seconds. You can look back in time and view the activity or the locks of the database at any time.  I'll also track pg_stat_statements, for the asme reason.

Often, there is no central point of connectivity that can reach all of your databases. This project will handle that by using s3 as a mechanism to transfer the files. 


## Architecture

The current architecture plan has the following pieces:
* The Scraper.  This will be installed near the target database, and be responsible for running the queries, and uploading the results to s3
* S3. I'd imagine any S3 compatible storage would be ok.
* The Aggregator.  This will get all the files from S3 and put the results in the data stores.  There may end up being some logic here.
* The Data Store.  I'm not 100% sure what this will be.  It will likely need to support database-like things (like copies of pg_activity), but also some time series information.  Ironically, this may not be postgres Possibilities:
  * Postgres/VictoriaMetrics
  * Postgres/Timescale
  * Clickhouse
* Visualization
 * Right now I'd expect this to just be Grafana connecting to the data sources, and a set of dashboards.  


## Other Potential Projects

As mentioned, I'm not inventing any magic here.  I'm most likely going to re-invent the wheel, but it'll be more hexagon than a circle.

These are some of the tools that I'll draw inspiration from, and may very really be a better fit:

* [pgsnapper](https://aws.amazon.com/blogs/database/monitor-amazon-rds-for-postgresql-and-amazon-aurora-postgresql-performance-using-pgsnapper/) This is where I really got the main idea from. 
* [PMM](https://www.percona.com/software/pmm/quickstart)  Percon's full fledged suite of tools.
* [PgHero](https://github.com/ankane/pghero) Basic but great tool developed at instacart. 
* [pg_gather](https://github.com/jobinau/pg_gather) Jobin's excellent analysis tool
* [postgres_exporter](https://github.com/prometheus-community/postgres_exporter) The Prometheus Exporter
* [postgres_dba](https://github.com/NikolayS/postgres_dba) A set of useful tools from Nikolay Samokhvalov of postgres.ai



## Production Usage
As I write this, the only thing that exists is the readme, so it's 100% safe.

That being said, my intent is that the only thing this will do to the database is essentially "select * from pg_stat_statements;", and similar.  Analysis will be done later on.  I can't imagine what would be added to make it not safe, but production usage is at your own discretion.
