import asyncio
import logging
import os
import argparse
import random
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.storage import StorageManager
from src.crawler import MoneroCrawler
from src.analyzer import NetworkAnalyzer
from src.visualizer import NetworkVisualizer
from src.enricher import DataEnricher 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def inject_seed_data(shutdown_event):
    """
    Injects synthetic data for portfolio demo.
    Creates a 'Sybil Attack' pattern to ensure graphs look interesting.
    """
    logging.info("💉 Injecting synthetic data for portfolio demo...")
    storage = StorageManager()
    await storage.connect()
    
    await storage.reset_db()
    
    # --- CONFIGURING THE SCENARIO ---
    total_nodes = 120
    sybil_count = 35  # Increased to ~30% to guarantee alert trigger
    sybil_isp = "Malicious Corp Ltd."
    sybil_subnet = "10.66.6" 
    
    # Random pools for "Legitimate" traffic
    legit_isps = ["Amazon AWS", "Hetzner Online", "DigitalOcean", "Comcast", "Orange", "Google Cloud"]
    legit_countries = ["US", "DE", "FR", "CN", "NL", "SG", "JP"]
    
    logging.info(f"🎭 Generating {total_nodes} nodes with a {sybil_count}-node Sybil cluster...")

    for i in range(total_nodes):
        if shutdown_event.is_set(): break 
        
        # LOGIC: First 35 nodes are the ATTACKERS. The rest are random victims.
        if i < sybil_count:
            # SYBIL NODE (Suspicious Pattern)
            fake_ip = f"{sybil_subnet}.{i + 1}"
            isp = sybil_isp
            country = "XX" # Hiding location
            asn = "AS66666"
            version = 9999 
        else:
            # LEGITIMATE NODE (Randomized)
            fake_ip = f"{random.randint(1,220)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            isp = random.choice(legit_isps)
            country = random.choice(legit_countries)
            asn = f"AS{random.randint(1000, 90000)}"
            version = 1
        
        node_data = {
            'ip': fake_ip,
            'port': 18080,
            'version': version,
            'user_agent': f"Monero/v0.18.0.{version}",
            'asn': asn,
            'isp': isp,
            'country': country 
        }
        await storage.add_node(node_data)
        
        if i % 20 == 0: await asyncio.sleep(0.01)
    
    await storage.flush_buffer()
    await storage.close()
    logging.info("✅ Injection Complete: Sybil Scenario Loaded.")

async def run_crawler(duration, shutdown_event):
    """PHASE 1: CRAWL"""
    storage = StorageManager()
    await storage.connect()
    
    logging.info("🧹 Wiping old data to ensure fresh scan...")
    await storage.reset_db()
    
    crawler = MoneroCrawler(storage, concurrency=50)
    crawler_task = asyncio.create_task(crawler.start(duration))
    shutdown_wait = asyncio.create_task(shutdown_event.wait())
    
    # Race: Run until crawler finishes OR user hits Ctrl+C
    done, pending = await asyncio.wait(
        [crawler_task, shutdown_wait],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    if shutdown_wait in done:
        logging.warning("⚠️ Aborting Crawler (User Interrupt)...")
        crawler_task.cancel()
        try:
            await crawler_task
        except asyncio.CancelledError:
            pass
    
    logging.info("💾 Performing final database flush...")
    await storage.flush_buffer() 
    await storage.close()

async def run_enrichment(shutdown_event):
    """PHASE 2: ENRICH"""
    logging.info("🧠 Starting Data Enrichment (Resolving ISPs & Countries)...")
    enricher = DataEnricher()
    
    enrich_task = asyncio.create_task(enricher.enrich_data())
    shutdown_wait = asyncio.create_task(shutdown_event.wait())
    
    done, pending = await asyncio.wait(
        [enrich_task, shutdown_wait],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    if shutdown_wait in done:
        logging.warning("⚠️ Aborting Enrichment (User Interrupt)...")
        enrich_task.cancel()
        try:
            await enrich_task
        except asyncio.CancelledError:
            logging.info("🛑 Enrichment stopped cleanly.")
    else:
        try:
            await enrich_task
        except Exception as e:
            logging.error(f"❌ Enrichment error: {e}")

async def run_forensics_check(shutdown_event):
    """PHASE 3: FORENSIC ALERTS"""
    if shutdown_event.is_set(): return
    logging.info("🔍 Running Sybil Detection Engine...")
    analyzer = NetworkAnalyzer()
    # Calls the detection method (now properly inside the class)
    await analyzer.detect_sybils()

def generate_report():
    """PHASE 4: REPORT (Synchronous)"""
    logging.info("📊 Starting Analysis Phase...")
    analyzer = NetworkAnalyzer()
    
    data = analyzer.generate_report_data()
    
    if data:
        viz = NetworkVisualizer()
        viz.generate_all_charts(data)
        logging.info("✅ Report Generation Complete. Check /reports folder.")
    else:
        logging.warning("⚠️ No data to analyze.")

async def main_pipeline(args):
    """Orchestrates the entire async workflow in ONE event loop."""
    # 1. Create the Event specific to THIS running loop
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    # 2. Register Signal Handlers (The Asyncio Way)
    def signal_handler():
        logging.info("\n🛑 Interrupt received! Shutting down gracefully...")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # 3. Run Steps Sequence
    try:
        # STEP 1: CRAWL
        if args.mock:
            await inject_seed_data(shutdown_event)
        elif not args.skip_scan:
            if not shutdown_event.is_set():
                await run_crawler(args.time, shutdown_event)
        else:
            logging.info("⏭️  Skipping Scan (Using existing database)...")

        # STEP 2: ENRICH
        # Skip enrichment if we are in mock mode (don't overwrite fake data)
        if not shutdown_event.is_set() and not args.mock:
            await run_enrichment(shutdown_event)
        elif args.mock:
            logging.info("⏭️  Skipping Enrichment (Mock Data is already pre-filled).")

        # STEP 3: FORENSICS (The Alert!)
        # Runs on both Mock and Real data
        if not shutdown_event.is_set():
            await run_forensics_check(shutdown_event)

    except asyncio.CancelledError:
        logging.info("🚫 Pipeline Cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🕵️ Monero Sybil Hunter - Network Forensics Tool",
        epilog="Example: python main.py --time 60 --skip-scan"
    )
    
    parser.add_argument('--mock', action='store_true', help='Use simulated data')
    parser.add_argument('--time', type=int, default=30, help='Crawl duration')
    parser.add_argument('--skip-scan', action='store_true', help='Skip crawling')
    parser.add_argument('--skip-report', action='store_true', help='Skip reporting')

    args = parser.parse_args()

    if args.mock:
        os.environ["USE_MOCK"] = "True"
        logging.info("🎭 MOCK MODE ENABLED")
    else:
        os.environ["USE_MOCK"] = "False"
        logging.info("🌐 REAL NETWORK MODE ENABLED")

    try:
        asyncio.run(main_pipeline(args))
        
        if not args.skip_report:
            generate_report()
            
    except KeyboardInterrupt:
        logging.info("🛑 Hard Exit.")
    except Exception as e:
        logging.error(f"❌ Fatal Error: {e}")