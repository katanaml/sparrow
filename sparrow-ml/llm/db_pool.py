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


