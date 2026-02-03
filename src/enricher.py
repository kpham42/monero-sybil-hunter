import asyncio
import aiohttp
import logging
from src.storage import StorageManager

class DataEnricher:
    def __init__(self):
        self.storage = None 

    async def enrich_data(self):
        if not self.storage:
            self.storage = StorageManager()
            await self.storage.connect()

        # UPDATED: Using the exact column names from your storage.py
        query = """
            SELECT DISTINCT TRIM(ip) as ip FROM nodes 
            WHERE COALESCE(country_code, '') IN ('', 'XX', 'None', 'Unknown')
               OR COALESCE(isp_name, '') IN ('', 'Unknown', 'Unknown ISP')
        """
        rows = await self.storage.pool.fetch(query)

        if not rows:
            logging.info("✅ Enrichment: No empty nodes found.")
            return

        logging.info(f"🧠 Forensic Enricher: Resolving {len(rows)} nodes...")

        async with aiohttp.ClientSession() as session:
            for i, record in enumerate(rows):
                ip = record['ip']
                await self.resolve_ip(session, ip)
                # Respect API rate limits
                await asyncio.sleep(1.5) 

        logging.info("✅ Enrichment Cycle Complete.")

    async def resolve_ip(self, session, ip):
        clean_ip = ip.strip()
        url = f"http://ip-api.com/json/{clean_ip}"
        
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status != 200: return
                data = await resp.json()
                
                if data.get('status') == 'success':
                    country = data.get('countryCode', 'Unknown')
                    isp = data.get('isp', 'Unknown ISP')
                    
                    # UPDATED: Mapping to country_code and isp_name
                    result = await self.storage.pool.execute(
                        "UPDATE nodes SET country_code = $1, isp_name = $2 WHERE TRIM(ip) = $3", 
                        country, isp, clean_ip
                    )
                    
                    if result == "UPDATE 1":
                        logging.info(f"   📍 Fixed: {clean_ip} -> {country}")
                    else:
                        logging.error(f"   ❌ DB Mismatch: Could not update {clean_ip}")
                        
                else:
                    # Mark to avoid infinite retries
                    await self.storage.pool.execute(
                        "UPDATE nodes SET country_code = 'Unknown', isp_name = 'Private' WHERE TRIM(ip) = $1", 
                        clean_ip
                    )
        except Exception as e:
            logging.error(f"   ❌ Error for {clean_ip}: {e}")