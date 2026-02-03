import requests
import re
import logging
import json

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_huge_node_list():
    """
    Aggregates Monero nodes using the correct API endpoints and structures.
    """
    sources = [
        # 1. Monero.fail
        ("https://monero.fail/?nettype=mainnet", "regex"),
        
        # 2. Ditatompel API
        ("https://xmr.ditatompel.com/api/v1/nodes?limit=5000", "json_dita"),
        
        # 3. Lino's Community List
        ("https://community.rino.io/nodes.json", "json"),
        
        # 4. Monero.fail JSON
        ("https://monero.fail/json", "json_fail")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    all_nodes = set()
    print("🚀 Launching Mass Scraper...")
    
    for url, method in sources:
        try:
            print(f"🌍 Scraping {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            new_nodes = []
            
            if method == "regex":
                # Fallback: Find IP:Port in raw HTML
                new_nodes = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:1808[0-9]\b', response.text)
                
            elif method == "json_dita":
                # FIX: Parse the new nested structure (data -> items)
                try:
                    data = response.json()
                    # The API changed: nodes are now inside data['items'] or just data
                    items = data.get('data', {}).get('items', []) 
                    if not items and isinstance(data.get('data'), list):
                         items = data['data']
                    
                    for item in items:
                        host = item.get('hostname') or item.get('ip')
                        port = item.get('port', 18080)
                        if host:
                            new_nodes.append(f"{host}:{port}")
                except Exception as e:
                    print(f"   ⚠️ JSON Parse Error: {e}")

            elif method == "json_fail":
                # Monero.fail simple list
                try:
                    data = response.json()
                    # Sometimes it's a dict with 'nodes', sometimes a list
                    items = data if isinstance(data, list) else data.get('nodes', [])
                    for item in items:
                        # Handle {"url": "1.2.3.4:18080"} format
                        if 'url' in item:
                            new_nodes.append(item['url'])
                        # Handle {"ip": "...", "port": ...} format
                        elif 'ip' in item:
                            new_nodes.append(f"{item['ip']}:{item.get('port', 18080)}")
                except: pass

            elif method == "json":
                # Standard {'nodes': [...]} format
                try:
                    data = response.json()
                    nodes = data.get('nodes', [])
                    for n in nodes:
                        if 'ip' in n:
                            new_nodes.append(f"{n['ip']}:{n.get('port', 18080)}")
                except: pass

            # Deduplicate and Add
            added_count = 0
            for node in new_nodes:
                if "127.0.0.1" in node or "localhost" in node: continue
                all_nodes.add(node)
                added_count += 1
                
            print(f"   ✅ Found {added_count} nodes.")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # Write to file
    print(f"\n💾 Saving {len(all_nodes)} unique nodes to targets.txt...")
    with open("targets.txt", "w") as f:
        for node in all_nodes:
            f.write(f"{node}\n")
    
    print("🎉 Done! List updated.")

if __name__ == "__main__":
    get_huge_node_list()