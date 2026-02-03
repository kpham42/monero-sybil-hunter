import matplotlib.pyplot as plt
import logging
import os

class NetworkVisualizer:
    def __init__(self):
        self.reports_dir = "reports"
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def generate_all_charts(self, data):
        """Generates forensics charts based on available data keys."""
        if not data: 
            logging.warning("⚠️ No data provided to Visualizer.")
            return

        # Generate Country Chart
        if 'countries' in data and data['countries']:
            self.plot_countries(data['countries'])
        
        # Generate ISP Chart
        if 'isps' in data and data['isps']:
            self.plot_isps(data['isps'])
        
        # Chart 3: Subnet Clusters
        if 'subnet' in data and data['subnet']:
            self.plot_subnets(data['subnet'])
            
        # Chart 4: Concentration (Ensure this matches the key in analyzer.py)
        if 'concentration' in data and data['concentration']:
            self.plot_resilience(data['concentration']) # Calling the actual function name
        
        logging.info(f"✅ 4 Reports generated in '{self.reports_dir}/'")

    def plot_countries(self, country_data):
        if not country_data: return
        
        plt.figure(figsize=(10, 6))
        # Bar chart for countries
        plt.bar(country_data.keys(), country_data.values(), color='#4e79a7')
        plt.title('Top Hosting Locations (Monero Nodes)', fontsize=14)
        plt.xlabel('Country Code', fontsize=12)
        plt.ylabel('Node Count', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.savefig(f"{self.reports_dir}/network_map.png")
        plt.close()

    def plot_isps(self, isp_data):
        """Generates the ISP Breakdown Pie Chart."""
        if not isp_data: return
        
        plt.figure(figsize=(10, 8))
        # Pie chart for ISPs
        plt.pie(isp_data.values(), labels=isp_data.keys(), autopct='%1.1f%%', startangle=140)
        plt.title('Top ISPs / Hosting Providers', fontsize=14)
        
        plt.savefig(f"{self.reports_dir}/top_isps.png")
        plt.close()

    def plot_versions(self, version_data):
        if not version_data: return
        
        plt.figure(figsize=(10, 6))
        plt.barh(list(version_data.keys()), list(version_data.values()), color='#e15759')
        plt.title('Node Version Distribution', fontsize=14)
        plt.xlabel('Count')
        
        plt.tight_layout()
        plt.savefig(f"{self.reports_dir}/versions.png")
        plt.close()

    def plot_subnets(self, subnet_data):
        """Detects IP clustering for Sybil analysis."""
        if not subnet_data: return
        
        plt.figure(figsize=(14, 8))
        sorted_keys = sorted(subnet_data, key=subnet_data.get, reverse=True)
        sorted_values = [subnet_data[k] for k in sorted_keys]
        plt.bar(sorted_keys, sorted_values, color='orange', alpha=0.7, edgecolor='black')
        plt.title('Infrastructure Clustering (IP Subnet Concentration)', fontsize=16, weight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.ylabel('Node Count', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.subplots_adjust(bottom=0.25)
        plt.savefig(f"{self.reports_dir}/subnet_clusters.png", bbox_inches='tight', dpi=300)
        plt.close()

    def plot_resilience(self, concentration_data):
        """Visualizes network centralization risk."""
        plt.figure(figsize=(8, 8))
        plt.pie(concentration_data.values(), labels=concentration_data.keys(), autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
        plt.title('Network Resilience: Provider Dependency', fontsize=14)
        plt.savefig(f"{self.reports_dir}/network_resilience.png")
        plt.close()