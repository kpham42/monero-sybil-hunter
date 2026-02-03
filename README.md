# monero-sybil-hunter

A basic Python-based network observability suite designed to audit the Monero P2P network, analyze infrastructure resilience, and detect Sybil attack patterns.

Overview

Monero Sybil Hunter is a forensic tool built to analyze the decentralization of the Monero cryptocurrency network. By crawling active nodes and enriching them with ISP and geolocation metadata, it generates Risk Assessment Reports identifying:

Infrastructure Centralization: Dependency on specific cloud providers (e.g., AWS, Hetzner) vs. residential ISPs.

Geo-Political Risk: Concentration of nodes in specific jurisdictions.

Sybil Attack Vectors: Detection of suspicious IP subnet clustering and version uniformity that often indicates surveillance attempts.

Architecture

The project follows a modular, pipeline-oriented architecture:

Crawler (src/crawler.py): High-concurrency async scanner that discovers nodes via seeding and directory scraping.

Enricher (src/enricher.py): Forensic module that resolves ISP/ASN data using external APIs.

Analyzer (src/analyzer.py): Data science engine using Pandas to detect anomalies (e.g., "One ISP controls >15% of network").

Visualizer (src/visualizer.py): Reporting engine that generates high-definition charts for forensic review.

Storage (src/storage.py): Robust PostgreSQL backend using connection pooling (asyncpg).

Installation & Docker Setup

Option A: The "Industry Standard" (Docker)

Using Docker is recommended for portfolio reviews to ensure a consistent environment.

Launch Infrastructure:

docker-compose up -d



Run the Tool inside the container:

docker-compose run app python main.py --mock



Option B: Local Setup

Install dependencies: pip install -r requirements.txt

Setup Database: Ensure PostgreSQL is running and update your .env file.

Usage

Simulation Mode (Portfolio Demo)

Injects a synthetic "Sybil Attack Scenario" into the database. This creates a realistic dataset with a hidden cluster of malicious nodes to demonstrate the detection engine.

python main.py --mock



Scenario: 120 Total Nodes. 30 "Attacker" nodes (25%) are injected on a specific subnet (10.66.6.x) with hidden locations to trigger risk alerts.

Real Network Scan

Performs a live crawl of the public Monero network.

python main.py --time 60



Report Generation Only

To regenerate graphs from existing data without re-scanning:

python main.py --skip-scan



Forensic Reports

After execution, check the reports/ folder for artifacts:
| Artifact | Forensic Value |
| ----- | ----- |
| subnet_clusters.png | Infrastructure Clustering. Large bars indicate many nodes on the same /24 subnet (likely a single entity). |
| network_resilience.png | Measures the "Bus Factor." Shows how much of the network relies on the Top 5 providers. |
| top_isps.png | Breakdown of hosting providers (e.g., DigitalOcean vs. Comcast). |
| network_map.png | Global distribution of node jurisdictions. |

Data Limitations & Disclaimer

This tool is intended for educational and research purposes.

Public-Only Visibility: The crawler can only identify nodes that accept incoming connections. It does not map nodes behind Tor/I2P or NAT.

Snapshot Validity: P2P networks are highly volatile. This data represents a momentary snapshot.

Enrichment Accuracy: ISP data is derived from public APIs. Some edge cases exist where data center IPs are misattributed.

Heuristic Detection: Sybil detection is based on heuristics (Subnet/ISP concentration). This indicates risk, not definitive proof of malicious intent.

License

MIT License - Open for educational use.
