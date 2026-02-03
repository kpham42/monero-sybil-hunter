import logging
import os
import random
import geoip2.database

# Pool of innocent ISPs/Countries (Noise)
MOCK_COUNTRIES = ['FR', 'NL', 'RU', 'SG', 'JP', 'GB', 'CA', 'BR', 'AU', 'IN']
MOCK_ASNS = [
    "AS16509 (Amazon.com)", 
    "AS13335 (Cloudflare, Inc.)", 
    "AS7922 (Comcast Cable)", 
    "AS20473 (Choopa, LLC)", 
    "AS3320 (Deutsche Telekom AG)", 
    "AS1239 (Sprint)"
]
MOCK_VERSIONS = [
    "Monero/0.18.3.1", 
    "Monero/0.18.3.0", 
    "Monero/0.18.2.2", 
    "Monero/0.18.2.0", 
    "Monero/0.17.3.0", 
    "Monero/0.18.0.0"
]

# Possible Sybil Scenarios (The "Bad Guy" changes each run)
SYBIL_PROFILES = [
    {"asn": "AS14061 (DigitalOcean, LLC)", "country": "US", "version": "Monero/0.18.0.0-Patched"},  
    {"asn": "AS24940 (Hetzner Online GmbH)", "country": "DE", "version": "Monero/0.19.0.0-Beta"}, 
    {"asn": "AS45102 (Alibaba Cloud)",       "country": "CN", "version": "XMR-Node-Proxy/0.1"}, 
    {"asn": "AS9009 (M247 Ltd)",             "country": "RO", "version": "Monero/0.18.1.0-Evil"}, 
]

class GeoIPHandler:
    _instance = None # Singleton storage

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeoIPHandler, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.city_reader = None
        self.asn_reader = None
        
        self.use_mock = os.getenv("USE_MOCK", "False").lower() == "true"
        self.city_path = 'data/GeoLite2-City.mmdb'
        self.asn_path = 'data/GeoLite2-ASN.mmdb'

        # --- DYNAMIC THREAT SELECTION ---
        # Pick one random attacker profile for this session
        self.threat_profile = random.choice(SYBIL_PROFILES)
        
        if self.use_mock:
            logging.info(f"🎰 Generating MOCK Attack Scenario: {self.threat_profile['asn']} | {self.threat_profile['country']} | {self.threat_profile['version']}")

        if not self.use_mock:
            # Try loading City DB
            if os.path.exists(self.city_path):
                try:
                    self.city_reader = geoip2.database.Reader(self.city_path)
                except Exception as e:
                    logging.warning(f"⚠️ City DB Load Failed: {e}")
            
            # Try loading ASN DB
            if os.path.exists(self.asn_path):
                try:
                    self.asn_reader = geoip2.database.Reader(self.asn_path)
                except Exception as e:
                    logging.warning(f"⚠️ ASN DB Load Failed: {e}")
            
            # If we missed both, fall back to mock
            if not self.city_reader and not self.asn_reader:
                self.use_mock = True

    def get_asn(self, ip):
        """Returns the ISP/ASN String."""
        if self.use_mock or not self.asn_reader:
            seed = sum(ord(c) for c in ip)
            
            # 33% Chance of being the Selected Sybil Attacker
            if seed % 3 == 0: 
                return self.threat_profile['asn']
                
            return MOCK_ASNS[seed % len(MOCK_ASNS)]
            
        try:
            response = self.asn_reader.asn(ip) 
            return f"{response.autonomous_system_organization}"
        except:
            return "Unknown ISP"

    def get_country(self, ip):
        """Returns the 2-letter country code."""
        if self.use_mock or not self.city_reader:
            seed = sum(ord(c) for c in ip)
            
            # CORRELATION LOGIC:
            if seed % 3 == 0:
                return self.threat_profile['country']
                
            return MOCK_COUNTRIES[seed % len(MOCK_COUNTRIES)]
        
        try:
            response = self.city_reader.city(ip)
            return response.country.iso_code or "XX"
        except:
            return "XX"

    def get_version(self, ip):
        """Returns the User-Agent / Software Version."""
        if self.use_mock:
            seed = sum(ord(c) for c in ip)
            
            # CORRELATION LOGIC:
            if seed % 3 == 0:
                return self.threat_profile['version']
                
            return MOCK_VERSIONS[seed % len(MOCK_VERSIONS)]
            
        return "Monero/0.18.0.0"

# --- EXPORTED FUNCTIONS ---
# These must be at the global level (indentation 0)
def get_geoip_data(ip):
    return GeoIPHandler().get_country(ip)

def get_asn_data(ip):
    return GeoIPHandler().get_asn(ip)

def get_version_data(ip):
    return GeoIPHandler().get_version(ip)