name: maxcompute-sql
description: Write, optimize, and review SQL queries for Alibaba Cloud MaxCompute (ODPS). Use when working with MaxCompute SQL for data analysis, ETL jobs, table management, or query optimization. Covers DDL/DML operations, built-in functions, UDFs, partitioned tables, and performance tuning for large-scale data processing.
---

# MaxCompute SQL

## Overview

MaxCompute SQL (ODPS SQL) is Alibaba Cloud's distributed SQL engine for petabyte-scale data warehousing. This skill provides comprehensive guidance for writing efficient, correct SQL for data analysis and ETL workflows on MaxCompute.

## Core Capabilities

### 1. SQL Query Writing
- SELECT queries with complex joins, subqueries, and window functions
- Aggregation queries (GROUP BY, ROLLUP, CUBE)
- Data manipulation (INSERT, INSERT OVERWRITE, INSERT INTO)
- Multi-table operations (UNION, INTERSECT, MINUS)

### 2. Table Management
- CREATE TABLE with proper partitioning strategy
- ALTER TABLE operations (add/drop columns, rename)
- DROP TABLE and TRUNCATE TABLE
- Table lifecycle management (set TTL)

### 3. Partition Operations
- Partition pruning optimization techniques
- Dynamic and static partitioning
- ALTER TABLE ADD/DROP PARTITION
- MSCK REPAIR TABLE for partition recovery

### 4. Built-in Functions
- Mathematical functions (ABS, ROUND, POW, etc.)
- String functions (CONCAT, SUBSTR, REGEXP, etc.)
- Date functions (TO_DATE, DATEADD, DATEDIFF, etc.)
- Aggregate functions (COUNT, SUM, AVG, COLLECT_SET, etc.)
- Window functions (ROW_NUMBER, RANK, LAG, LEAD, etc.)

### 5. Advanced Features
- Common Table Expressions (CTEs) with WITH clause
- MAPJOIN hints for small table optimization
- UDF/UDAF/UDTF integration patterns
- MaxCompute 2.0 type system (ARRAY, MAP, STRUCT)

## Quick Start

### Basic Query Structure
```sql
-- Recommended: set job priority first (speeds up scheduling)
set odps.instance.priority=7;

-- Simple SELECT
SELECT column1, column2
FROM table_name
WHERE condition
LIMIT 100;

-- With aggregation
SELECT 
    category,
    COUNT(*) as cnt,
    SUM(amount) as total_amount
FROM sales_table
WHERE dt = '20250101'
GROUP BY category;
```

### Partitioned Table Best Practice
```sql
-- Create partitioned table
CREATE TABLE user_behavior (
    user_id STRING,
    event_type STRING,
    event_time DATETIME
) PARTITIONED BY (dt STRING, hour STRING);

-- Query with partition pruning (ALWAYS include partition keys)
SELECT *
FROM user_behavior
WHERE dt = '20250101' AND hour = '12';
```

## Optimization Patterns

### 1. Avoid Full Table Scans
```sql
-- BAD: No partition filter
SELECT * FROM large_table WHERE user_id = 'xxx';

-- GOOD: With partition filter
SELECT * FROM large_table 
WHERE dt = '20250101' AND user_id = 'xxx';
```

### 2. Use MAPJOIN for Small Tables
```sql
-- When joining with small dimension table (< 512MB)
SELECT /*+ MAPJOIN(dim) */ 
    f.*, dim.name
FROM fact_table f
JOIN dim_table dim ON f.dim_id = dim.id;
```

### 3. Minimize Data Shuffling
```sql
-- Use DISTRIBUTE BY for controlling data distribution
INSERT OVERWRITE TABLE target_table
SELECT /*+ REPARTITION(100) */ *
FROM source_table;
```

## Common Functions Reference

See [references/functions.md](references/functions.md) for complete function documentation.

### Frequently Used Date Functions
```sql
TO_DATE('2025-01-01', 'yyyy-MM-dd')     -- String to date
DATEADD(TO_DATE('20250101', 'yyyyMMdd'), 1, 'dd')  -- Add days
DATEDIFF(end_date, start_date, 'dd')    -- Date difference
FROM_UNIXTIME(unix_timestamp)           -- Unix timestamp to datetime
GETDATE()                               -- Current datetime
```

### Window Functions
```sql
-- Row number within groups
SELECT 
    user_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY amount DESC) as rn
FROM transactions;

-- Running totals
SELECT 
    date,
    daily_amount,
    SUM(daily_amount) OVER (ORDER BY date) as running_total
FROM daily_sales;
```

## ETL Job Patterns

### Incremental Data Loading
```sql
-- Insert overwrite with partition
INSERT OVERWRITE TABLE target_table PARTITION (dt = '${bizdate}')
SELECT 
    user_id,
    event_count,
    SUM(amount) as total_amount
FROM source_table
WHERE dt = '${bizdate}'
GROUP BY user_id, event_count;
```

### Multi-Stage Processing with CTEs
```sql
WITH 
step1 AS (
    SELECT user_id, COUNT(*) as cnt
    FROM raw_data
    WHERE dt = '${bizdate}'
    GROUP BY user_id
),
step2 AS (
    SELECT user_id, cnt,
           NTILE(10) OVER (ORDER BY cnt DESC) as decile
    FROM step1
)
SELECT * FROM step2 WHERE decile <= 3;
```

## Data Type Considerations

MaxCompute 2.0 supports complex types:
```sql
-- ARRAY type
ARRAY(1, 2, 3)
EXPLODE(array_col)  -- Explode array to rows

-- MAP type
MAP('key1', 'value1', 'key2', 'value2')
MAP_KEYS(map_col)
MAP_VALUES(map_col)

-- STRUCT type
STRUCT('John', 30, 'Engineer')
named_struct('name', 'John', 'age', 30)
```

## Executing SQL & Fetching Data

Use the provided Python script to execute SQL queries and retrieve results directly.

### Two Execution Modes

| Mode | Command | Best For | Response Time |
|------|---------|----------|---------------|
| **Traditional** (default) | `--sql "SELECT ..."` | Large data, complex ETL | Minutes |
| **MCQA Interactive** | `--interactive` / `-i` | Small queries, ad-hoc analysis | Seconds |

**MCQA (MaxCompute Query Acceleration)** is the same engine DataStudio uses for fast interactive queries. Use it for:
- Exploratory data analysis (< 10,000 rows)
- Quick validation of query logic
- Real-time dashboards

Use **Traditional mode** for:
- Large-scale aggregations
- Production ETL jobs
- Complex multi-stage processing

### Setup

1. **Install dependency**:
   ```bash
   pip install pyodps>=0.11.4.1  # MCQA requires 0.11.4.1+
   ```

2. **Configure environment variables** (recommended for security):
   ```bash
   export ODPS_ACCESS_ID="your-access-key-id"
   export ODPS_ACCESS_KEY="your-access-key-secret"
   export ODPS_PROJECT="your-default-project"
   export ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
   ```

### Usage Examples

#### Traditional Mode (Default)

**Execute a simple query**:
```bash
python scripts/get_data.py --sql "SELECT * FROM my_table LIMIT 10"
```

**Execute with parameters**:
```bash
python scripts/get_data.py \
  --sql "SELECT * FROM sales WHERE dt='${bizdate}'" \
  --params '{"bizdate": "20250101"}'
```

**Output as JSON**:
```bash
python scripts/get_data.py \
  --sql "SELECT category, SUM(amount) as total FROM sales GROUP BY category" \
  --format json
```

**Save to file**:
```bash
python scripts/get_data.py \
  --file query.sql \
  --format csv \
  --output results.csv
```

**Execute SQL from file**:
```bash
python scripts/get_data.py --file my_query.sql --limit 100
```

#### MCQA Interactive Mode (Fast!)

**Quick data preview** (like DataStudio):
```bash
python scripts/get_data.py \
  --sql "SELECT * FROM users LIMIT 100" \
  --interactive
```

**Ad-hoc aggregation** (small dataset):
```bash
python scripts/get_data.py \
  --sql "SELECT status, COUNT(*) FROM orders WHERE dt='20250224' GROUP BY status" \
  -i --format table
```

**Query from file with MCQA**:
```bash
python scripts/get_data.py --file quick_check.sql --interactive
```

**MCQA without fallback** (fail fast if MCQA unavailable):
```bash
python scripts/get_data.py \
  --sql "SELECT * FROM events LIMIT 50" \
  --interactive --fallback none
```

**MCQA with specific fallback policy**:
```bash
python scripts/get_data.py \
  --sql "SELECT * FROM events LIMIT 50" \
  -i --fallback "noresource,unsupported"
```

### MCQA Fallback Policies

When MCQA is unavailable, you can control fallback behavior:

| Policy | Description |
|--------|-------------|
| `all` (default) | Auto fallback on any error |
| `none` / `no` | Never fallback, fail fast |
| `noresource` | Fallback only when resources insufficient |
| `unsupported` | Fallback only when SQL not supported by MCQA |
| `timeout` | Fallback only on timeout |
| `noresource,unsupported` | Combined policies |

**Note**: MCQA does not support multi-statement SQL (e.g., `set ...; select ...;`). For MCQA mode, use single SELECT statements only.

### Programmatic Usage

```python
from scripts.get_data import get_odps_client, execute_sql, fetch_results

# Initialize client
odps = get_odps_client(project="my_project")

# Execute SQL
instance = execute_sql(odps, "SELECT * FROM users WHERE dt='20250101'")

# Fetch results
results = fetch_results(odps, instance, limit=100)

# Process results
for row in results:
    print(row)
```

## Resources

### scripts/
- [get_data.py](scripts/get_data.py) - Execute MaxCompute SQL queries and fetch results. Supports parameterized queries, multiple output formats (JSON, CSV, table), and environment-based configuration.

### references/
- [functions.md](references/functions.md) - Complete MaxCompute SQL function reference

## References

- MaxCompute SQL syntax: https://help.aliyun.com/document_detail/27874.html
- Built-in functions: https://help.aliyun.com/document_detail/27884.html
- Query optimization: https://help.aliyun.com/document_detail/102752.html
