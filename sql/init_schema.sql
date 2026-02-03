-- Table to store unique Monero Nodes
CREATE TABLE IF NOT EXISTS nodes (
    ip VARCHAR(45) PRIMARY KEY,
    port INT NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    protocol_version INT,
    user_agent VARCHAR(255),
    asn VARCHAR(50),          -- e.g., "AS14061"
    isp_name VARCHAR(255),    -- e.g., "DigitalOcean, LLC"
    country_code VARCHAR(5)   -- e.g., "US", "DE"
);

-- Index for fast queries on ASN (finding Sybil clusters)
CREATE INDEX IF NOT EXISTS idx_nodes_asn ON nodes(asn);
CREATE INDEX IF NOT EXISTS idx_nodes_country ON nodes(country_code);

-- Table to log historical peer connections
CREATE TABLE IF NOT EXISTS peer_connections (
    id SERIAL PRIMARY KEY,
    source_ip VARCHAR(45) REFERENCES nodes(ip),
    peer_ip VARCHAR(45),
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);