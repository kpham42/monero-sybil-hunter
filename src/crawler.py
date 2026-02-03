import asyncio
import logging
import aiohttp
import os
import re
from src.storage import StorageManager
from src.utils import get_geoip_data, get_asn_data, get_version_data

class MoneroCrawler:
    def __init__(self, storage_manager: StorageManager, concurrency=50):
        self.storage = storage_manager
        self.concurrency = concurrency
        self.queue = asyncio.Queue()
        self.seen_ips = set()
        self.active = True

    async def load_from_file(self):
        """1. Load nodes from targets.txt"""
        if os.path.exists('targets.txt'):
            count = 0
            with open('targets.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    
                    # Extract IP/Port
                    if ':' in line:
                        parts = line.split(':')
                        ip = parts[0]
                        try: port = int(parts[1])
                        except: port = 18080
                    else:
                        ip = line
                        port = 18080
                    
                    await self.queue.put((ip, port))
                    count += 1
            logging.info(f"📂 Loaded {count} targets from file.")

    async def fetch_public_nodes(self):
        """2. Load nodes from Web"""
        logging.info("🌍 Auto-discovering nodes from public directories...")
        sources = [
            "https://raw.githubusercontent.com/monero-project/monero/master/src/p2p/net_node.inl",
            "https://monero.fail/?nettype=mainnet"
        ]
        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            for url in sources:
                try:
                    async with session.get(url, timeout=5) as resp:
                        text = await resp.text()
                        # Find all IP:Port patterns
                        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:1808[0-9]\b', text)
                        if ips:
                            logging.info(f"✅ Scraped {len(ips)} nodes from {url}")
                            for entry in ips:
                                ip, port = entry.split(':')
                                await self.queue.put((ip, int(port)))
                except Exception:
                    pass

    async def start(self, duration):
    # Load targets...
        await self.load_from_file()
    
        workers = [asyncio.create_task(self.worker(i)) for i in range(self.concurrency)]
    
        try:
            # This is where the time limit is enforced
            await asyncio.wait_for(self.queue.join(), timeout=duration)
        except asyncio.TimeoutError:
            logging.info(f"⏱️  Time limit reached ({duration}s). Finishing up...")
        finally:
            self.active = False
            for w in workers:
                w.cancel()
        # The workers are dead, but the data they found is still in the 
        # storage manager's internal buffer, waiting for the flush() in main.py.

    async def worker(self, worker_id):
        while self.active:
            try:
                ip, port = await self.queue.get()
                if ip not in self.seen_ips:
                    self.seen_ips.add(ip)
                    await self.scan_node(ip, port)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                self.queue.task_done()

    async def scan_node(self, ip, port):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=2.0
            )
            
            asn_info = get_asn_data(ip)
            geo_info = get_geoip_data(ip)
            
            node_data = {
                'ip': ip, 'port': port, 'version': 1,
                'user_agent': "Monero/0.18.0.0",
                'asn': asn_info, 'isp': asn_info, 'country': geo_info
            }
            await self.storage.add_node(node_data)
            logging.info(f"✅ Verified Node: {ip} [{geo_info}]")
            writer.close()
            await writer.wait_closed()
        except:
            pass