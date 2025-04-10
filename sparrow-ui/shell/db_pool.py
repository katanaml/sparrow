import atexit
import configparser


# Function to get database configuration
def get_db_config():
    config = configparser.ConfigParser()
    try:
        config.read("config.properties")

        # Check if database is enabled
        db_enabled = False
        if "settings" in config.sections() and "use_database" in config["settings"]:
            db_enabled = config.getboolean("settings", "use_database", fallback=False)

        # Get database connection details if enabled
        db_config = {
            "enabled": db_enabled,
            "user": None,
            "password": None,
            "host": None,
            "port": None,
            "service": None
        }

        # Only populate connection details if database is enabled
        if db_enabled and "database" in config.sections():
            db_config["user"] = config.get("database", "user", fallback="")
            db_config["password"] = config.get("database", "password", fallback="")
            db_config["host"] = config.get("database", "host", fallback="")
            db_config["port"] = config.get("database", "port", fallback="1521")
            db_config["service"] = config.get("database", "service", fallback="")

        return db_config
    except Exception as e:
        print(f"Error reading database config: {e}")
        return {"enabled": False}


# Get database configuration
db_config = get_db_config()
database_enabled = db_config["enabled"]

# Only import oracledb if database is enabled
if database_enabled:
    import oracledb

# Connection pool variables
connection_pool = None
pool_closed = False


def initialize_connection_pool(min_connections=2, max_connections=10, increment=1):
    """Initialize the connection pool at application startup"""
    global connection_pool, pool_closed, database_enabled, db_config

    if not database_enabled:
        return False

    if connection_pool and not pool_closed:
        return True  # Pool already initialized

    try:
        # Create the connection pool using config values
        dsn = oracledb.makedsn(
            db_config["host"],
            db_config["port"],
            service_name=db_config["service"]
        )

        connection_pool = oracledb.create_pool(
            user=db_config["user"],
            password=db_config["password"],
            dsn=dsn,
            min=min_connections,
            max=max_connections,
            increment=increment,
            getmode=oracledb.POOL_GETMODE_WAIT
        )

        pool_closed = False
        print(f"Connection pool created with {min_connections}-{max_connections} connections")
        return True
    except Exception as e:
        print(f"Error creating connection pool: {e}")
        return False


def close_connection_pool():
    """Close the connection pool on application shutdown"""
    global connection_pool, pool_closed, database_enabled

    if not database_enabled:
        return

    if connection_pool and not pool_closed:
        try:
            connection_pool.close()
            pool_closed = True
            print("Connection pool closed")
        except Exception as e:
            print(f"Error closing connection pool: {e}")


# Register the shutdown function
atexit.register(close_connection_pool)


def get_connection_from_pool():
    """Get a connection from the pool"""
    global connection_pool, pool_closed, database_enabled

    if not database_enabled:
        return None

    if pool_closed:
        initialize_connection_pool()
    elif not connection_pool:
        initialize_connection_pool()

    return connection_pool.acquire()


def release_connection(connection):
    """Release a connection back to the pool"""
    global connection_pool, pool_closed, database_enabled

    if not database_enabled:
        return

    if connection and connection_pool and not pool_closed:
        try:
            connection_pool.release(connection)
        except Exception as e:
            print(f"Error releasing connection: {e}")


def get_restricted_key(client_ip):
    """
    Call the obtain_sparrow_key PL/SQL function to get a restricted key
    based on rate limiting rules.

    Args:
        client_ip (str): The client's IP address

    Returns:
        str or None: A sparrow key if available, None if rate limited or error
    """
    # If database is not enabled, return None
    global database_enabled

    if not database_enabled:
        return None

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Declare a variable to hold the returned value from the function
        out_var = cursor.var(str)

        # Call the PL/SQL function
        cursor.execute(
            "BEGIN :result := obtain_sparrow_key(:ip); END;",
            result=out_var,
            ip=client_ip
        )

        # Get the result
        key = out_var.getvalue()

        cursor.close()
        return key
    except Exception as e:
        print(f"Error calling obtain_sparrow_key: {str(e)}")
        return None
    finally:
        if connection:
            release_connection(connection)


def verify_key(key):
    """
    Verify if a provided Sparrow key exists in the database and is enabled.

    Args:
        key (str): The Sparrow key to verify

    Returns:
        bool: True if key exists and is enabled, False otherwise
    """
    # If database is not enabled, return True (skip check)
    global database_enabled

    if not database_enabled:
        return True

    if not key or key.strip() == "":
        return False

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Execute SQL query to check if the key exists and is enabled
        query = """
            SELECT COUNT(*) 
            FROM SPARROW.SPARROW_KEYS 
            WHERE SPARROW_KEY = :key 
            AND ENABLED = 1
        """

        cursor.execute(query, key=key)
        count = cursor.fetchone()[0]

        # If count > 0, key exists and is enabled
        exists = count > 0

        cursor.close()
        return exists
    except Exception as e:
        print(f"Error verifying key: {str(e)}")
        return False  # On error, assume key doesn't exist
    finally:
        if connection:
            release_connection(connection)


def get_inference_logs(period="1week"):
    """
    Fetch inference logs from the database for a specified time period,
    excluding records with SPARROW_KEY_ID = 1 and COUNTRY_NAME that is 'Unknown' or NULL.

    Args:
        period (str): Time period to fetch data for.
                      Valid values: "1week", "2weeks", "1month", "6months", "all"
                      Default is "1week".

    Returns:
        list: A list of dictionaries containing log data if database is enabled,
              an empty list otherwise.
    """
    # If database is not enabled, return empty list
    global database_enabled

    if not database_enabled:
        return []

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Base query
        query = """
            SELECT
                TIMESTAMP as log_date,
                COUNTRY_NAME,
                INFERENCE_DURATION,
                PAGE_COUNT,
                MODEL_NAME,
                INFERENCE_HOST_IP
            FROM 
                SPARROW.INFERENCE_LOGS
            WHERE 
                SPARROW_KEY_ID != 1
                AND COUNTRY_NAME IS NOT NULL 
                AND COUNTRY_NAME != 'Unknown' 
                AND COUNTRY_NAME != 'Lithuania'
        """

        # Add time period filter if not 'all'
        if period != "all":
            time_filter = None
            if period == "1week":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '7' DAY"
            elif period == "2weeks":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '14' DAY"
            elif period == "1month":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '1' MONTH"
            elif period == "6months":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '6' MONTH"

            if time_filter:
                query += f" AND {time_filter}"

        # Add order by clause
        query += " ORDER BY TIMESTAMP DESC"

        cursor.execute(query)

        # Fetch all rows and convert to list of dictionaries
        columns = [col[0].lower() for col in cursor.description]
        results = []

        for row in cursor:
            results.append(dict(zip(columns, row)))

        cursor.close()
        return results

    except Exception as e:
        print(f"Error fetching inference logs: {str(e)}")
        return []
    finally:
        if connection:
            release_connection(connection)


def get_unique_users_by_country(period="1week"):
    """
    Fetch count of unique users (by IP address) per country from the database
    for a specified time period, excluding records with SPARROW_KEY_ID = 1
    and COUNTRY_NAME that is 'Unknown' or NULL.

    Args:
        period (str): Time period to fetch data for.
                      Valid values: "1week", "2weeks", "1month", "6months", "all"
                      Default is "1week".

    Returns:
        list: A list of dictionaries containing country and unique user count if database is enabled,
              an empty list otherwise.
    """
    # If database is not enabled, return empty list
    global database_enabled

    if not database_enabled:
        return []

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Base query to count distinct IP addresses by country
        query = """
            SELECT
                COUNTRY_NAME,
                COUNT(DISTINCT INFERENCE_HOST_IP) as unique_users
            FROM 
                SPARROW.INFERENCE_LOGS
            WHERE 
                SPARROW_KEY_ID != 1
                AND COUNTRY_NAME IS NOT NULL 
                AND COUNTRY_NAME != 'Unknown' 
                AND COUNTRY_NAME != 'Lithuania'
        """

        # Add time period filter if not 'all'
        if period != "all":
            time_filter = None
            if period == "1week":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '7' DAY"
            elif period == "2weeks":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '14' DAY"
            elif period == "1month":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '1' MONTH"
            elif period == "6months":
                time_filter = "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '6' MONTH"

            if time_filter:
                query += f" AND {time_filter}"

        # Group by country and order by unique user count in descending order
        query += " GROUP BY COUNTRY_NAME ORDER BY unique_users DESC"

        cursor.execute(query)

        # Fetch all rows and convert to list of dictionaries
        columns = [col[0].lower() for col in cursor.description]
        results = []

        for row in cursor:
            results.append(dict(zip(columns, row)))

        cursor.close()
        return results

    except Exception as e:
        print(f"Error fetching unique users by country: {str(e)}")
        return []
    finally:
        if connection:
            release_connection(connection)