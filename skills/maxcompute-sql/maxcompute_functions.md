# MaxCompute SQL Built-in Functions Reference

## Mathematical Functions

| Function | Description | Example |
|----------|-------------|---------|
| `ABS(x)` | Absolute value | `ABS(-5)` → 5 |
| `ROUND(x, d)` | Round to d decimal places | `ROUND(3.14159, 2)` → 3.14 |
| `FLOOR(x)` | Floor (largest integer ≤ x) | `FLOOR(3.7)` → 3 |
| `CEIL(x)` | Ceiling (smallest integer ≥ x) | `CEIL(3.2)` → 4 |
| `POWER(x, y)` / `POW(x, y)` | x raised to power y | `POW(2, 3)` → 8 |
| `SQRT(x)` | Square root | `SQRT(16)` → 4 |
| `LOG(x)` | Natural logarithm | `LOG(2.71828)` → ~1 |
| `LOG10(x)` | Base-10 logarithm | `LOG10(100)` → 2 |
| `LOG2(x)` | Base-2 logarithm | `LOG2(8)` → 3 |
| `EXP(x)` | e raised to power x | `EXP(1)` → 2.71828 |
| `SIN(x), COS(x), TAN(x)` | Trigonometric functions | `SIN(PI()/2)` → 1 |
| `RAND()` / `RANDOM()` | Random number [0, 1) | `RAND()` → 0.734... |
| `MOD(x, y)` | Modulo (remainder) | `MOD(10, 3)` → 1 |
| `SIGN(x)` | Sign of number (-1, 0, 1) | `SIGN(-42)` → -1 |

## String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `CONCAT(str1, str2, ...)` | Concatenate strings | `CONCAT('Hello', ' ', 'World')` → 'Hello World' |
| `CONCAT_WS(sep, str1, str2, ...)` | Concatenate with separator | `CONCAT_WS('-', '2025', '01', '01')` → '2025-01-01' |
| `SUBSTR(str, pos, len)` / `SUBSTRING(str, pos, len)` | Extract substring | `SUBSTR('Hello', 1, 3)` → 'Hel' |
| `LENGTH(str)` / `CHAR_LENGTH(str)` | String length | `LENGTH('Hello')` → 5 |
| `TRIM(str)` / `LTRIM(str)` / `RTRIM(str)` | Remove whitespace | `TRIM('  hello  ')` → 'hello' |
| `UPPER(str)` / `LOWER(str)` | Case conversion | `UPPER('hello')` → 'HELLO' |
| `REPLACE(str, old, new)` | Replace substring | `REPLACE('hello world', 'world', 'maxcompute')` → 'hello maxcompute' |
| `SPLIT(str, delim)` | Split string to array | `SPLIT('a,b,c', ',')` → ['a', 'b', 'c'] |
| `REGEXP_EXTRACT(str, pattern, group)` | Extract regex group | `REGEXP_EXTRACT('foo|bar', '(.*?)\\|(.*)', 1)` → 'foo' |
| `REGEXP_REPLACE(str, pattern, replacement)` | Replace with regex | `REGEXP_REPLACE('abc123', '[^0-9]', '')` → '123' |
| `REGEXP_COUNT(str, pattern)` | Count regex matches | `REGEXP_COUNT('a1b2c3', '[0-9]')` → 3 |
| `INSTR(str, substr)` | Find substring position | `INSTR('hello', 'll')` → 3 |
| `LPAD(str, len, pad)` / `RPAD(str, len, pad)` | Pad string | `LPAD('5', 3, '0')` → '005' |
| `REPEAT(str, n)` | Repeat string | `REPEAT('ab', 3)` → 'ababab' |
| `REVERSE(str)` | Reverse string | `REVERSE('hello')` → 'olleh' |
| `MD5(str)` | MD5 hash | `MD5('hello')` → '5d41402abc4b2a76b9719d911017c592' |
| `HASH(str)` | Hash code | `HASH('hello')` → integer |

## Date/Time Functions

| Function | Description | Example |
|----------|-------------|---------|
| `GETDATE()` / `CURRENT_TIMESTAMP` | Current datetime | `GETDATE()` → '2025-01-01 12:00:00' |
| `TO_DATE(str, format)` | String to date | `TO_DATE('20250101', 'yyyyMMdd')` |
| `TO_CHAR(date, format)` | Date to string | `TO_CHAR(GETDATE(), 'yyyy-MM-dd')` → '2025-01-01' |
| `YEAR(date)` / `MONTH(date)` / `DAY(date)` | Extract component | `YEAR('2025-01-15')` → 2025 |
| `HOUR(datetime)` / `MINUTE(datetime)` / `SECOND(datetime)` | Extract time | `HOUR('12:30:45')` → 12 |
| `DATEADD(date, n, unit)` | Add to date | `DATEADD('2025-01-01', 1, 'dd')` → '2025-01-02' |
| `DATEDIFF(end, start, unit)` | Date difference | `DATEDIFF('2025-01-15', '2025-01-01', 'dd')` → 14 |
| `DATEPART(date, unit)` | Extract date part | `DATEPART('2025-01-15', 'month')` → 1 |
| `DATETRUNC(date, unit)` | Truncate to unit | `DATETRUNC('2025-01-15 12:30:00', 'dd')` → '2025-01-15' |
| `FROM_UNIXTIME(unixtime)` | Unix timestamp to datetime | `FROM_UNIXTIME(1704067200)` |
| `TO_UNIX_TIMESTAMP(datetime)` / `UNIX_TIMESTAMP(datetime)` | Datetime to Unix timestamp | `UNIX_TIMESTAMP('2025-01-01')` |
| `WEEKOFYEAR(date)` | Week number (1-53) | `WEEKOFYEAR('2025-01-01')` → 1 |
| `DAYOFWEEK(date)` | Day of week (1-7) | `DAYOFWEEK('2025-01-01')` → 4 (Wednesday) |
| `LAST_DAY(date)` | Last day of month | `LAST_DAY('2025-01-15')` → '2025-01-31' |
| `ADD_MONTHS(date, n)` | Add months | `ADD_MONTHS('2025-01-15', 2)` → '2025-03-15' |
| `MONTHS_BETWEEN(date1, date2)` | Months difference | `MONTHS_BETWEEN('2025-03-15', '2025-01-15')` → 2 |

## Aggregate Functions

| Function | Description | Example |
|----------|-------------|---------|
| `COUNT(*)` / `COUNT(expr)` / `COUNT(DISTINCT expr)` | Count rows/values | `COUNT(DISTINCT user_id)` |
| `SUM(expr)` | Sum of values | `SUM(amount)` |
| `AVG(expr)` | Average | `AVG(score)` |
| `MIN(expr)` / `MAX(expr)` | Min/Max | `MAX(order_time)` |
| `STDDEV(expr)` / `STDDEV_SAMP(expr)` | Standard deviation | `STDDEV(salary)` |
| `VARIANCE(expr)` / `VAR_SAMP(expr)` | Variance | `VARIANCE(score)` |
| `PERCENTILE(expr, p)` | Percentile | `PERCENTILE(response_time, 0.95)` |
| `COLLECT_SET(expr)` | Collect distinct values to array | `COLLECT_SET(category)` |
| `COLLECT_LIST(expr)` | Collect all values to array | `COLLECT_LIST(user_id)` |
| `WM_CONCAT(sep, expr)` / `GROUP_CONCAT(expr)` | Concatenate with separator | `WM_CONCAT(',', name)` |
| `BIT_AND(expr)` / `BIT_OR(expr)` / `BIT_XOR(expr)` | Bitwise aggregation | `BIT_AND(flags)` |

## Window Functions

| Function | Description | Example |
|----------|-------------|---------|
| `ROW_NUMBER() OVER (...)` | Row number (1, 2, 3...) | `ROW_NUMBER() OVER (ORDER BY score DESC)` |
| `RANK() OVER (...)` | Rank (1, 2, 2, 4...) | `RANK() OVER (PARTITION BY class ORDER BY score DESC)` |
| `DENSE_RANK() OVER (...)` | Dense rank (1, 2, 2, 3...) | `DENSE_RANK() OVER (ORDER BY score DESC)` |
| `PERCENT_RANK() OVER (...)` | Percentile rank | `PERCENT_RANK() OVER (ORDER BY score)` |
| `CUME_DIST() OVER (...)` | Cumulative distribution | `CUME_DIST() OVER (ORDER BY score)` |
| `NTILE(n) OVER (...)` | Divide into n buckets | `NTILE(10) OVER (ORDER BY amount)` |
| `LAG(expr, offset, default) OVER (...)` | Previous row value | `LAG(price, 1, 0) OVER (ORDER BY date)` |
| `LEAD(expr, offset, default) OVER (...)` | Next row value | `LEAD(price, 1) OVER (ORDER BY date)` |
| `FIRST_VALUE(expr) OVER (...)` | First value in window | `FIRST_VALUE(price) OVER (ORDER BY date)` |
| `LAST_VALUE(expr) OVER (...)` | Last value in window | `LAST_VALUE(price) OVER (ORDER BY date)` |
| `NTH_VALUE(expr, n) OVER (...)` | Nth value | `NTH_VALUE(price, 3) OVER (ORDER BY date)` |

## Conditional Functions

| Function | Description | Example |
|----------|-------------|---------|
| `IF(condition, true_val, false_val)` | Conditional | `IF(age > 18, 'Adult', 'Minor')` |
| `CASE WHEN ... THEN ... END` | Case statement | `CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' ELSE 'C' END` |
| `COALESCE(val1, val2, ...)` | First non-null | `COALESCE(mobile, phone, 'N/A')` |
| `NVL(val, default)` | Replace null | `NVL(discount, 0)` |
| `NULLIF(val1, val2)` | Null if equal | `NULLIF(status, 'deleted')` |
| `ISNULL(expr)` | Check if null | `ISNULL(email)` |

## Type Conversion Functions

| Function | Description | Example |
|----------|-------------|---------|
| `CAST(expr AS type)` | Cast type | `CAST('123' AS BIGINT)` |
| `TRY_CAST(expr AS type)` | Safe cast (null on fail) | `TRY_CAST('abc' AS BIGINT)` → NULL |
| `DECIMAL(expr, p, s)` / `DECIMAL(expr)` | Convert to decimal | `DECIMAL(amount, 18, 2)` |
| `BIGINT(expr)` / `INT(expr)` / `SMALLINT(expr)` | Convert to integer | `BIGINT('123')` → 123 |
| `DOUBLE(expr)` / `FLOAT(expr)` | Convert to float | `DOUBLE('3.14')` → 3.14 |
| `STRING(expr)` / `VARCHAR(expr)` | Convert to string | `STRING(123)` → '123' |
| `BOOLEAN(expr)` | Convert to boolean | `BOOLEAN(1)` → true |
| `BINARY(expr)` | Convert to binary | `BINARY('hello')` |

## Array Functions

| Function | Description | Example |
|----------|-------------|---------|
| `ARRAY(val1, val2, ...)` | Create array | `ARRAY(1, 2, 3)` |
| `SIZE(array)` / `ARRAY_SIZE(array)` | Array length | `SIZE(ARRAY(1, 2, 3))` → 3 |
| `GET_JSON_OBJECT(json, path)` | Extract JSON value | `GET_JSON_OBJECT(json_col, '$.name')` |
| `JSON_TUPLE(json, key1, key2, ...)` | Extract multiple JSON fields | `JSON_TUPLE(json_col, 'id', 'name')` |
| `EXPLODE(array)` | Explode array to rows | `SELECT EXPLODE(ARRAY(1, 2, 3))` |
| `POSEXPLODE(array)` | Explode with position | `SELECT POSEXPLODE(ARRAY('a', 'b'))` → (0, 'a'), (1, 'b') |
| `SPLIT(str, delim)` | String to array | `SPLIT('a,b,c', ',')` |
| `ARRAY_CONTAINS(array, value)` | Check containment | `ARRAY_CONTAINS(ARRAY(1, 2, 3), 2)` → true |
| `SORT_ARRAY(array)` | Sort array | `SORT_ARRAY(ARRAY(3, 1, 2))` → [1, 2, 3] |
| `ARRAY_DISTINCT(array)` | Remove duplicates | `ARRAY_DISTINCT(ARRAY(1, 1, 2))` → [1, 2] |
| `SLICE(array, start, length)` | Subarray | `SLICE(ARRAY(1, 2, 3, 4), 1, 2)` → [2, 3] |
| `CONCAT_ARRAY(array1, array2)` | Concatenate arrays | `CONCAT_ARRAY(ARRAY(1, 2), ARRAY(3, 4))` → [1, 2, 3, 4] |

## Map Functions

| Function | Description | Example |
|----------|-------------|---------|
| `MAP(key1, val1, key2, val2, ...)` | Create map | `MAP('a', 1, 'b', 2)` |
| `MAP_KEYS(map)` | Get keys array | `MAP_KEYS(MAP('a', 1, 'b', 2))` → ['a', 'b'] |
| `MAP_VALUES(map)` | Get values array | `MAP_VALUES(MAP('a', 1, 'b', 2))` → [1, 2] |
| `MAP_ENTRIES(map)` | Get entries | `MAP_ENTRIES(MAP('a', 1))` |
| `SIZE(map)` | Map size | `SIZE(MAP('a', 1))` → 1 |

## Other Functions

| Function | Description | Example |
|----------|-------------|---------|
| `TRANS_ARRAY(sep, n, col1, col2, ...)` | Transform columns to rows | `TRANS_ARRAY(',', 2, col1, col2)` |
| `INLINE(array<struct>)` | Explode struct array | `INLINE(ARRAY(NAMED_STRUCT('a', 1, 'b', 2)))` |
| `NAMED_STRUCT(name1, val1, name2, val2, ...)` | Create named struct | `NAMAMED_STRUCT('x', 1, 'y', 2)` |
| `STRUCT(val1, val2, ...)` | Create struct | `STRUCT(1, 'hello', 3.14)` |
| `UUID()` | Generate UUID | `UUID()` → 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' |
| `CURRENT_USER()` | Current user | `CURRENT_USER()` |
| `CURRENT_DATABASE()` | Current project | `CURRENT_DATABASE()` |

## URL Functions

| Function | Description | Example |
|----------|-------------|---------|
| `PARSE_URL(url, part)` | Parse URL component | `PARSE_URL('http://example.com/path?k=v', 'HOST')` → 'example.com' |
| `PARSE_URL_TUPLE(url, part1, part2, ...)` | Parse multiple parts | `PARSE_URL_TUPLE(url, 'HOST', 'PATH', 'QUERY')` |
| `URL_DECODE(str)` / `URL_ENCODE(str)` | URL encoding | `URL_DECODE('hello%20world')` → 'hello world' |

## Encoding/Encryption Functions

| Function | Description | Example |
|----------|-------------|---------|
| `BASE64(str)` / `UNBASE64(str)` | Base64 encode/decode | `BASE64('hello')` → 'aGVsbG8=' |
| `HEX(str)` / `UNHEX(str)` | Hex encode/decode | `HEX('hello')` → '68656c6c6f' |
| `MD5(str)` | MD5 hash | `MD5('hello')` |
| `SHA1(str)` | SHA1 hash | `SHA1('hello')` |
| `SHA256(str)` / `SHA2(str, 256)` | SHA256 hash | `SHA256('hello')` |
| `CRC32(str)` | CRC32 checksum | `CRC32('hello')` |

## Usage Notes

1. **NULL handling**: Most functions return NULL if any argument is NULL (unless documented otherwise)
2. **Type coercion**: MaxCompute automatically converts compatible types in many cases
3. **Overflow**: Integer overflow wraps around; use DECIMAL for precision-critical calculations
4. **Date formats**: Common formats include 'yyyy-MM-dd', 'yyyyMMdd', 'yyyy-MM-dd HH:mm:ss'
5. **String indices**: SUBSTR uses 1-based indexing (first character is position 1)
