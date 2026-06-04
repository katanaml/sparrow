/**
 * db_pool.ts — Oracle DB connection pool
 * Server-side only. Equivalent of db_pool.py in Gradio app.
 * Uses oracledb Node.js driver (npm install oracledb).
 */

import oracledb from "oracledb";

// ─── Config from environment ──────────────────────────────────────────────
const DB_ENABLED = process.env.USE_DATABASE === "true";

const dbConfig = {
  user:        process.env.DB_USER     || "",
  password:    process.env.DB_PASSWORD || "",
  host:        process.env.DB_HOST     || "127.0.0.1",
  port:        parseInt(process.env.DB_PORT || "1521"),
  service:     process.env.DB_SERVICE  || "",
};

// ─── Pool singleton ───────────────────────────────────────────────────────
let pool: oracledb.Pool | null = null;

export async function initializeConnectionPool(): Promise<boolean> {
  if (!DB_ENABLED) return false;
  if (pool) return true;

  try {
    pool = await oracledb.createPool({
      user:             dbConfig.user,
      password:         dbConfig.password,
      connectString:    `${dbConfig.host}:${dbConfig.port}/${dbConfig.service}`,
      poolMin:          2,
      poolMax:          10,
      poolIncrement:    1,
    });

    console.log("Oracle connection pool created");
    return true;
  } catch (err) {
    console.error("Error creating connection pool:", err);
    return false;
  }
}

export async function closeConnectionPool(): Promise<void> {
  if (!DB_ENABLED || !pool) return;
  try {
    await pool.close(10);
    pool = null;
    console.log("Connection pool closed");
  } catch (err) {
    console.error("Error closing connection pool:", err);
  }
}

async function getConnection(): Promise<oracledb.Connection | null> {
  if (!DB_ENABLED) return null;
  if (!pool) await initializeConnectionPool();
  if (!pool) return null;
  return pool.getConnection();
}

// ─── verify_key ───────────────────────────────────────────────────────────
/**
 * Verify if a provided Sparrow key exists and is enabled.
 * Equivalent of db_pool.verify_key() in Python.
 */
export async function verify_key(key: string): Promise<boolean> {
  if (!DB_ENABLED) return true;   // DB disabled → skip check, allow all
  if (!key || key.trim() === "") return false;

  let connection: oracledb.Connection | null = null;
  try {
    connection = await getConnection();
    if (!connection) return false;

    const result = await connection.execute<[number]>(
      `SELECT COUNT(*) 
       FROM SPARROW.SPARROW_KEYS 
       WHERE SPARROW_KEY = :key 
       AND ENABLED = 1`,
      { key: key.trim() }
    );

    const count = result.rows?.[0]?.[0] ?? 0;
    return count > 0;
  } catch (err) {
    console.error("Error verifying key:", err);
    return false;
  } finally {
    if (connection) await connection.close();
  }
}

// ─── InferenceLog type ────────────────────────────────────────────────────
export interface InferenceLog {
  log_date:          Date;
  country_name:      string;
  inference_duration: number;
  page_count:        number;
  model_name:        string;
  inference_host_ip: string;
}

// ─── get_inference_logs ───────────────────────────────────────────────────
/**
 * Fetch inference logs for a given time period.
 * Excludes SPARROW_KEY_ID=1, Unknown/Lithuania countries, non-extraction types.
 * Equivalent of db_pool.get_inference_logs() in Python.
 */
export async function get_inference_logs(period = "1week"): Promise<InferenceLog[]> {
  if (!DB_ENABLED) return [];

  let connection: oracledb.Connection | null = null;
  try {
    connection = await getConnection();
    if (!connection) return [];

    let query = `
      SELECT
        TIMESTAMP AS log_date,
        COUNTRY_NAME,
        INFERENCE_DURATION,
        PAGE_COUNT,
        CASE
          WHEN MODEL_NAME IN ('mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit', 'lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-MLX-8bit')
            THEN 'Mistral-Small'
          WHEN MODEL_NAME = 'mlx-community/Ministral-3-14B-Instruct-2512-8bit'
            THEN 'Ministral'
          WHEN MODEL_NAME = 'mlx-community/dots.ocr-bf16'
            THEN 'Dots'
          ELSE MODEL_NAME
        END AS MODEL_NAME,
        INFERENCE_HOST_IP
      FROM SPARROW.INFERENCE_LOGS
      WHERE SPARROW_KEY_ID != 1
        AND COUNTRY_NAME IS NOT NULL
        AND COUNTRY_NAME != 'Unknown'
        AND COUNTRY_NAME != 'Lithuania'
        AND INFERENCE_TYPE = 'DATA_EXTRACTION'
    `;

    const timeFilters: Record<string, string> = {
      "1week":   "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '7' DAY",
      "2weeks":  "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '14' DAY",
      "1month":  "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '1' MONTH",
      "6months": "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '6' MONTH",
    };
    if (period !== "all" && timeFilters[period]) {
      query += ` AND ${timeFilters[period]}`;
    }
    query += " ORDER BY TIMESTAMP DESC";

    const result = await connection.execute<unknown[]>(query, [], {
      outFormat: oracledb.OUT_FORMAT_OBJECT,
    });

    return (((result.rows ?? []) as unknown[]) as Record<string, unknown>[]).map((row) => ({
      log_date:           row["LOG_DATE"] as Date,
      country_name:       row["COUNTRY_NAME"] as string,
      inference_duration: row["INFERENCE_DURATION"] as number,
      page_count:         row["PAGE_COUNT"] as number,
      model_name:         row["MODEL_NAME"] as string,
      inference_host_ip:  row["INFERENCE_HOST_IP"] as string,
    }));
  } catch (err) {
    console.error("Error fetching inference logs:", err);
    return [];
  } finally {
    if (connection) await connection.close();
  }
}

// ─── UniqueUsersByCountry type ────────────────────────────────────────────
export interface UniqueUsersByCountry {
  country_name:  string;
  unique_users:  number;
}

// ─── get_unique_users_by_country ──────────────────────────────────────────
/**
 * Fetch count of unique users (distinct IPs) per country for a given period.
 * Equivalent of db_pool.get_unique_users_by_country() in Python.
 */
export async function get_unique_users_by_country(period = "1week"): Promise<UniqueUsersByCountry[]> {
  if (!DB_ENABLED) return [];

  let connection: oracledb.Connection | null = null;
  try {
    connection = await getConnection();
    if (!connection) return [];

    let query = `
      SELECT
        COUNTRY_NAME,
        COUNT(DISTINCT INFERENCE_HOST_IP) AS unique_users
      FROM SPARROW.INFERENCE_LOGS
      WHERE SPARROW_KEY_ID != 1
        AND COUNTRY_NAME IS NOT NULL
        AND COUNTRY_NAME != 'Unknown'
        AND COUNTRY_NAME != 'Lithuania'
        AND INFERENCE_TYPE = 'DATA_EXTRACTION'
    `;

    const timeFilters: Record<string, string> = {
      "1week":   "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '7' DAY",
      "2weeks":  "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '14' DAY",
      "1month":  "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '1' MONTH",
      "6months": "TIMESTAMP >= SYSTIMESTAMP - INTERVAL '6' MONTH",
    };
    if (period !== "all" && timeFilters[period]) {
      query += ` AND ${timeFilters[period]}`;
    }
    query += " GROUP BY COUNTRY_NAME ORDER BY unique_users DESC";

    const result = await connection.execute<unknown[]>(query, [], {
      outFormat: oracledb.OUT_FORMAT_OBJECT,
    });

    return (((result.rows ?? []) as unknown[]) as Record<string, unknown>[]).map((row) => ({
      country_name: row["COUNTRY_NAME"] as string,
      unique_users: row["UNIQUE_USERS"] as number,
    }));
  } catch (err) {
    console.error("Error fetching unique users by country:", err);
    return [];
  } finally {
    if (connection) await connection.close();
  }
}

// ─── save_user_feedback ───────────────────────────────────────────────────
/**
 * Save user feedback to SPARROW.FEEDBACK table.
 * Equivalent of db_pool.save_user_feedback() in Python.
 */
export async function save_user_feedback(email: string, feedbackText: string): Promise<boolean> {
  if (!DB_ENABLED) {
    console.log("Database is not enabled. Cannot save feedback.");
    return false;
  }

  let connection: oracledb.Connection | null = null;
  try {
    connection = await getConnection();
    if (!connection) return false;

    await connection.execute(
      `INSERT INTO SPARROW.FEEDBACK (EMAIL, FEEDBACK) VALUES (:email, :feedback)`,
      { email, feedback: feedbackText }
    );

    await connection.commit();
    console.log(`Feedback saved successfully from ${email}`);
    return true;
  } catch (err) {
    console.error("Error saving feedback:", err);
    if (connection) {
      try { await connection.rollback(); } catch {}
    }
    return false;
  } finally {
    if (connection) await connection.close();
  }
}

/**
 * Get a rate-limited key for free-tier access via PL/SQL function.
 * Equivalent of db_pool.get_restricted_key() in Python.
 */
export async function get_restricted_key(clientIp: string): Promise<string | null> {
  if (!DB_ENABLED) return null;

  let connection: oracledb.Connection | null = null;
  try {
    connection = await getConnection();
    if (!connection) return null;

    const result = await connection.execute<{ result: string }>(
      `BEGIN :result := obtain_sparrow_key(:ip); END;`,
      {
        result: { dir: oracledb.BIND_OUT, type: oracledb.STRING },
        ip:     clientIp,
      }
    );

    return (result.outBinds as { result: string })?.result ?? null;
  } catch (err) {
    console.error("Error calling obtain_sparrow_key:", err);
    return null;
  } finally {
    if (connection) await connection.close();
  }
}