import mysql from 'mysql2/promise';

let pool;

export function getPool() {
  if (!pool) {
    pool = mysql.createPool({
      host: import.meta.env.DB_HOST,
      port: parseInt(import.meta.env.DB_PORT || '4000'),
      user: import.meta.env.DB_USER,
      password: import.meta.env.DB_PASSWORD,
      database: import.meta.env.DB_NAME,
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
