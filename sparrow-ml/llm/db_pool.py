import oracledb
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

    # Switch to thin mode
    oracledb.defaults.config_dir = None

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


def log_inference_start(client_ip, country_name=None, sparrow_key=None, page_count=1):
    """
    Logs the start of an inference request to INFERENCE_LOGS table using a PL/SQL function.

    Args:
        client_ip (str): The client's IP address
        country_name (str, optional): The country determined from the IP address
        sparrow_key (str, optional): The sparrow key used for this request
        page_count (int, optional): Number of pages processed in this request, defaults to 1

    Returns:
        int or None: The log ID if successfully logged, None otherwise
    """
    # If database is not enabled, return None
    global database_enabled

    if not database_enabled:
        return None

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Call the PL/SQL function to handle everything in one call
        out_var = cursor.var(int)

        cursor.execute(
            "BEGIN :result := log_inference_request(:ip, :country, :key, :page_count); END;",
            result=out_var,
            ip=client_ip,
            country=country_name,
            key=sparrow_key,
            page_count=page_count
        )

        # Get the result - handle if it returns a list
        log_id_value = out_var.getvalue()
        if isinstance(log_id_value, list) and len(log_id_value) > 0:
            log_id = log_id_value[0]
        else:
            log_id = log_id_value

        # Commit the transaction
        connection.commit()

        cursor.close()
        if log_id:
            print(f"Created inference log with ID: {log_id}")
        return log_id
    except Exception as e:
        print(f"Error logging inference start: {str(e)}")
        return None
    finally:
        if connection:
            release_connection(connection)


def update_inference_duration(log_id, duration):
    """Update the record with the actual duration"""
    global database_enabled

    if not database_enabled or log_id is None:
        return True

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        update_sql = """
            UPDATE inference_logs
            SET inference_duration = :duration
            WHERE id = :id
        """

        cursor.execute(
            update_sql,
            duration=duration,
            id=log_id
        )

        connection.commit()
        cursor.close()

        return True
    except Exception as e:
        print(f"Error updating inference duration: {str(e)}")
        return False
    finally:
        if connection:
            release_connection(connection)


def validate_and_increment_key(sparrow_key):
    """
    Validates a sparrow key and increments its usage counter if valid.

    This function calls the PL/SQL validate_and_increment_key function which:
    1. Checks if the key exists in the SPARROW_KEYS table
    2. Verifies the key is enabled
    3. Checks if incrementing would exceed the usage limit
    4. If all checks pass, increments the counter and updates last_used_date

    Args:
        sparrow_key (str): The sparrow key to validate and increment

    Returns:
        bool: True if key is valid and was incremented successfully, False otherwise
    """
    # If database is not enabled, return False
    global database_enabled

    if not database_enabled:
        return False

    connection = None
    try:
        connection = get_connection_from_pool()
        cursor = connection.cursor()

        # Declare a variable to hold the returned value from the function
        out_var = cursor.var(int)

        # Call the PL/SQL function
        cursor.execute(
            "BEGIN :result := validate_and_increment_key(:key); END;",
            result=out_var,
            key=sparrow_key
        )

        # Get the result (0 or 1)
        result = out_var.getvalue()

        cursor.close()
        return result == 1  # Convert 1/0 to True/False
    except Exception as e:
        print(f"Error calling validate_and_increment_key: {str(e)}")
        return False
    finally:
        if connection:
            release_connection(connection)