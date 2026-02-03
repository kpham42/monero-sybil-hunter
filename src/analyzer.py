import pandas as pd
import logging
import asyncio
from src.storage import StorageManager

class NetworkAnalyzer:
    def __init__(self):
        self.storage = StorageManager()

    async def fetch_data(self):
        """Fetches raw data from the database using the StorageManager schema."""
        await self.storage.connect()
        try:
            # UPDATED: Using isp_name and country_code from storage.py
            query = """
                SELECT ip, port, protocol_version, user_agent, country_code, isp_name 
                FROM nodes
            """
            rows = await self.storage.pool.fetch(query)
            
            if not rows:
                return pd.DataFrame()
            
            data = [dict(row) for row in rows]
            return pd.DataFrame(data)
            
        except Exception as e:
            logging.error(f"❌ Analysis failed: {e}")
            return pd.DataFrame()
        finally:
            await self.storage.close()

    async def detect_sybils(self):
        """Identifies ISPs controlling >20% of the network."""
        await self.storage.connect()
        try:
            # Find ISPs hosting more than 20% of your discovered nodes
            query = """
                WITH total AS (SELECT count(*) as full_count FROM nodes)
                SELECT isp_name, count(*) as cnt, 
                       (count(*)::float / (SELECT full_count FROM total) * 100) as network_percent
                FROM nodes
                GROUP BY isp_name
                HAVING count(*) > 5
                ORDER BY network_percent DESC;
            """
            rows = await self.storage.pool.fetch(query)
            for row in rows:
                if row['network_percent'] > 20:
                    print(f"\n[!] ⚠️  SYBIL ALERT: {row['isp_name']} controls {row['network_percent']:.2f}% of nodes!")
                    print(f"    Investigate cluster size: {row['cnt']} nodes\n")
        finally:
            await self.storage.close()

    def generate_report_data(self):
        """Processes the database rows for the visualizer."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        df = loop.run_until_complete(self.fetch_data())
        loop.close()

        if df.empty:
            logging.warning("⚠️ No data found in database to analyze.")
            return None

        logging.info(f"📊 Analyzing {len(df)} nodes...")

        # 1. Countries (Standardize XX/None to Unknown)
        df['country_code'] = df['country_code'].fillna('Unknown')
        df['country_code'] = df['country_code'].replace('XX', 'Unknown')
        country_counts = df['country_code'].value_counts().head(15).to_dict()

        # 2. ISPs (The enriched data)
        df['isp_name'] = df['isp_name'].fillna('Unknown ISP')
        isp_counts = df['isp_name'].value_counts().head(10).to_dict()

        # 3. Subnet Analysis (Forensic)
        # Groups by the first two octets (e.g., 1.2.x.x) to find clusters
        # Ensure IP is stripped before splitting
        df['subnet'] = df['ip'].str.strip().apply(lambda x: ".".join(x.split('.')[:2]) + ".0.0")
        subnet_counts = df['subnet'].value_counts().head(10).to_dict()

        # 4. Concentration Data
        # We want to see the share of the top 5 ISPs vs everyone else
        top_5_isp_total = df['isp_name'].value_counts().head(5).sum()
        others_total = len(df) - top_5_isp_total
        concentration_data = {"Top 5 Providers": int(top_5_isp_total), "Other Providers": int(others_total)}

        return {
            "total_nodes": len(df),
            "countries": country_counts,
            "isps": isp_counts,
            "subnets": subnet_counts,
            "concentration": concentration_data
        }