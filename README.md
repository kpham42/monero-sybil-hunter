# Monero Sybil Hunter

**A Python-based network observability suite designed to audit the Monero P2P network, analyze infrastructure resilience, and detect Sybil attack patterns.**

---

## Overview
I wrote this tool to analyze the decentralization (and potential centralization) of the Monero cryptocurrency network. By crawling active nodes and enriching them with ISP and geolocation metadata, it generates **Risk Assessment Reports** identifying:

* **Infrastructure Centralization**: Dependency on specific cloud providers (e.g., AWS, Hetzner) vs. residential ISPs.
* **Geo-Political Risk**: Concentration of nodes in specific jurisdictions.
* **Sybil Attack Vectors**: Detection of suspicious IP subnet clustering and version uniformity that often indicates surveillance attempts.

---

## Architecture

| Component | Module | Description |
| :--- | :--- | :--- |
| **Crawler** | `src/crawler.py` | Async scanner that discovers nodes via seeding and directory scraping. |
| **Enricher** | `src/enricher.py` | Forensic module that resolves unknown ISP/ASN data using external APIs. |
| **Analyzer** | `src/analyzer.py` | Uses Pandas to detect anomalies (e.g., "One ISP controls >15% of network"). |
| **Visualizer**| `src/visualizer.py`| Reporting engine that generates high-definition charts for forensic review. |
| **Storage** | `src/storage.py` | PostgreSQL backend using connection pooling (`asyncpg`). |

---

## Installation & Docker Setup

I highly recommend using Docker, but this can also be deployed locally as long as you have a PostgreSQL server running.

### Option A: Docker (Recommended)
1. **Launch Infrastructure:**
   ```bash
   docker-compose up -d
   ```
2. **Run the Tool inside the container:**
   ```bash
   docker-compose run app python main.py --mock
   ```

### Option B: Local Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Database:** Ensure PostgreSQL is running and update your `.env` file.

---

## Usage

### 1. Simulation Mode
Injects a synthetic "Sybil Attack Scenario" into the database. This creates a realistic dataset with a hidden cluster of malicious nodes to demonstrate the detection engine.
```bash
python main.py --mock
```
> **Scenario:** 120 Total Nodes. 30 "Attacker" nodes (25%) are injected on a specific subnet (`10.66.6.x`) with hidden locations to trigger risk alerts.

### 2. Real Network Scan
Performs a crawl of select portions of the Monero network using publically available sources and APIs.
```bash
python main.py --time 60
```

### 3. Report Generation Only
To regenerate graphs from existing data without re-scanning:
```bash
python main.py --skip-scan
```

---

## Forensic Reports
After execution, check the `reports/` folder for artifacts:

| Artifact | Forensic Value |
| :--- | :--- |
| `subnet_clusters.png` | **Infrastructure Clustering:** Large bars indicate many nodes on the same /24 subnet (likely a single entity). |
| `network_resilience.png` | **Bus Factor:** Shows how much of the network relies on the Top 5 providers. |
| `top_isps.png` | **Provider Breakdown:** Hosting providers (e.g., DigitalOcean) vs. Consumer ISPs (e.g., Comcast). |
| `network_map.png` | **Jurisdiction Map:** Global distribution of node locations. |

---

## Data Limitations & Disclaimer
*This tool is intended for educational and research purposes.*

* **Public-Only Visibility:** The crawler can only identify nodes that accept incoming connections. It does not map nodes behind Tor/I2P or NAT.
* **Snapshot Validity:** P2P networks are highly volatile. This data represents a momentary snapshot.
* **Enrichment Accuracy:** ISP data is derived from public APIs; misattribution can occur in edge cases.
* **Heuristic Detection:** Sybil detection is based on heuristics (Subnet/ISP concentration). This indicates **risk**, not definitive proof of malicious intent.

---

## License
**MIT License** - Open for educational use.
