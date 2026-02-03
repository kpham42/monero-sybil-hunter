import os
import logging
import asyncpg
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StorageManager:
    """
    Handles asynchronous database interactions using connection pooling and batch processing.
    """
    def __init__(self):
        self.pool = None
        self.node_buffer = []
        self.BATCH_SIZE = 50  # Flush to DB every 50 nodes found
        
        # --- SECURE CONFIG LOADING ---
        # We access os.environ inside __init__ so 'self' is valid.
        try:
            self.db_user = os.environ["POSTGRES_USER"]
            self.db_pass = os.environ["POSTGRES_PASSWORD"]
            self.db_name = os.environ["POSTGRES_DB"]
            # Optional vars can still use .get()
            self.db_host = os.environ.get("POSTGRES_HOST", "localhost")
            self.db_port = os.environ.get("POSTGRES_PORT", "5432")
        except KeyError as e:
            logging.critical(f"❌ Missing required environment variable: {e}")
            raise RuntimeError("Application cannot start without secure credentials.")

    async def connect(self):
        """
        Initializes the connection pool. 
        Must be awaited before using other methods.
        """
        try:
            self.pool = await asyncpg.create_pool(
                user=self.db_user,
                password=self.db_pass,
                database=self.db_name,
                host=self.db_host,
                port=self.db_port,
                min_size=5,  # Keep 5 connections open
                max_size=20  # Allow up to 20 during heavy load
            )
            logging.info("🔌 Connected to PostgreSQL database.")
        except Exception as e:
            logging.error(f"❌ Database connection failed: {e}")
            raise e

    async def add_node(self, node_data: dict):
        """
        Buffers a discovered node. Flushes to DB if buffer is full.
        Expected keys in node_data: ip, port, version, user_agent, asn, isp, country
        """
        self.node_buffer.append((
            node_data['ip'],
            node_data['port'],
            node_data.get('version', 0),
            node_data.get('user_agent', 'Unknown'),
            node_data.get('asn', 'Unknown'),
            node_data.get('isp', 'Unknown'),
            node_data.get('country', 'XX')
        ))

        if len(self.node_buffer) >= self.BATCH_SIZE:
            await self.flush_buffer()

    async def flush_buffer(self):
        """
        Writes buffered nodes to the database using an UPSERT strategy.
        If the IP exists, we update the 'last_seen' and telemetry data.
        """
        if not self.node_buffer:
            return

        query = """
        INSERT INTO nodes (ip, port, protocol_version, user_agent, asn, isp_name, country_code, last_seen)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ON CONFLICT (ip) DO UPDATE 
        SET 
            last_seen = NOW(),
            protocol_version = EXCLUDED.protocol_version,
            user_agent = EXCLUDED.user_agent,
            asn = EXCLUDED.asn,
            isp_name = EXCLUDED.isp_name;
        """

        async with self.pool.acquire() as conn:
            try:
                # executemany is highly optimized for batch inserts in asyncpg
                await conn.executemany(query, self.node_buffer)
                logging.info(f"💾 Flushed {len(self.node_buffer)} nodes to DB.")
                self.node_buffer = []  # Clear buffer
            except Exception as e:
                logging.error(f"❌ Failed to write batch: {e}")

    async def get_seed_nodes(self, limit=100):
        """
        Retrieves the most recently seen nodes to use as new crawler seeds.
        """
        query = "SELECT ip, port FROM nodes ORDER BY last_seen DESC LIMIT $1"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [(r['ip'], r['port']) for r in rows]
            
    async def reset_db(self):
        """
        Wipes all data from the nodes table. 
        ONLY used for testing/mocking to ensure clean graphs.
        """
        logging.warning("⚠️ RESETTING DATABASE (Mock Mode Active)")
        query = "TRUNCATE TABLE nodes CASCADE;"
        async with self.pool.acquire() as conn:
            await conn.execute(query)

    async def close(self):
        """
        Flush remaining data and close the connection pool.
        """
        await self.flush_buffer()
        if self.pool:
            await self.pool.close()
            logging.info("🔌 Database connection closed.")