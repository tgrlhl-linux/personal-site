import mysql from 'mysql2/promise';

let pool;

function getEnv(name, fallback) {
  // Works both with import.meta.env (Astro/Vite) and process.env (Node.js)
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[name]) {
    return import.meta.env[name];
  }
  if (typeof process !== 'undefined' && process.env && process.env[name]) {
    return process.env[name];
  }
  return fallback;
}

export function getPool() {
  if (!pool) {
    pool = mysql.createPool({
      host: getEnv('DB_HOST', 'localhost'),
      port: parseInt(getEnv('DB_PORT', '4000')),
      user: getEnv('DB_USER', 'root'),
      password: getEnv('DB_PASSWORD', ''),
      database: getEnv('DB_NAME', 'personal_site'),
      ssl: { rejectUnauthorized: true },
      waitForConnections: true,
      connectionLimit: 5,
    });
  }
  return pool;
}

export async function query(sql, params = []) {
  const conn = getPool();
  const [rows] = await conn.query(sql, params);
  return rows;
}
