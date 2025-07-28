"""
Migration script to create ietf_network.db from processed visualization data.
This creates a proper network database optimized for the API backend.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def create_network_database():
    """Create the ietf_network.db database from processed JSON data."""
    
    # Database path
    db_path = "cache/ietf_network.db"
    
    # Ensure cache directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print(f"Creating network database at: {db_path}")
    
    # Create schema
    create_schema(conn)
    
    # Import data from visualization JSON
    import_visualization_data(conn)
    
    # Create indexes for performance
    create_indexes(conn)
    
    # Add metadata
    add_metadata(conn)
    
    conn.close()
    print("✅ Network database created successfully!")
    
    return db_path


def create_schema(conn):
    """Create the database schema for network analysis."""
    
    print("Creating database schema...")
    
    # Create nodes table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        email_count INTEGER DEFAULT 0,
        mailing_lists_count INTEGER DEFAULT 0,
        activity_duration_days INTEGER DEFAULT 0,
        degree_centrality REAL DEFAULT 0.0,
        betweenness_centrality REAL DEFAULT 0.0,
        community INTEGER DEFAULT 0,
        dominant_topic INTEGER DEFAULT -1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create links table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        interaction_type TEXT DEFAULT 'reply',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source) REFERENCES nodes (id),
        FOREIGN KEY (target) REFERENCES nodes (id)
    )
    ''')
    
    # Create topics table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY,
        words TEXT,
        top_participants TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create metadata table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("✅ Schema created")


def import_visualization_data(conn):
    """Import data from the visualization JSON file."""
    
    print("Importing data from visualization JSON...")
    
    # Clear existing data
    conn.execute("DELETE FROM nodes")
    conn.execute("DELETE FROM links") 
    conn.execute("DELETE FROM topics")
    conn.execute("DELETE FROM metadata WHERE key NOT LIKE 'schema_%'")
    
    # Load data from visualization JSON
    json_path = "visualisation/data.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Visualization data not found at {json_path}")
        print("Run the fast processor first: python src/fast_main.py")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data.get('nodes', []))} nodes and {len(data.get('links', []))} links")
    
    # Import nodes
    nodes_imported = 0
    for node in data.get('nodes', []):
        conn.execute(
            """
            INSERT INTO nodes 
            (id, email_count, mailing_lists_count, activity_duration_days,
             degree_centrality, betweenness_centrality, community, dominant_topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node['id'],
                node.get('email_count', 0),
                node.get('mailing_lists_count', 0),
                node.get('activity_duration_days', 0),
                node.get('degree_centrality', 0.0),
                node.get('betweenness_centrality', 0.0),
                node.get('community', 0),
                node.get('dominant_topic', -1)
            )
        )
        nodes_imported += 1
    
    # Import links
    links_imported = 0
    for link in data.get('links', []):
        # Handle both string and object references
        source = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        conn.execute(
            """
            INSERT INTO links 
            (source, target, weight, interaction_type)
            VALUES (?, ?, ?, ?)
            """,
            (
                source,
                target,
                link.get('weight', 1.0),
                link.get('interaction_type', 'reply')
            )
        )
        links_imported += 1
    
    # Import topics
    topics_imported = 0
    for topic in data.get('topics', []):
        conn.execute(
            "INSERT INTO topics (id, words, top_participants) VALUES (?, ?, ?)",
            (
                topic['id'],
                json.dumps(topic.get('words', [])),
                json.dumps(topic.get('top_participants', []))
            )
        )
        topics_imported += 1
    
    # Import metadata
    if 'metadata' in data:
        for key, value in data['metadata'].items():
            conn.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
    
    conn.commit()
    print(f"✅ Imported {nodes_imported} nodes, {links_imported} links, {topics_imported} topics")


def create_indexes(conn):
    """Create indexes for performance optimization."""
    
    print("Creating performance indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_node_community ON nodes(community)",
        "CREATE INDEX IF NOT EXISTS idx_node_degree ON nodes(degree_centrality)",
        "CREATE INDEX IF NOT EXISTS idx_node_emails ON nodes(email_count)",
        "CREATE INDEX IF NOT EXISTS idx_node_topic ON nodes(dominant_topic)",
        "CREATE INDEX IF NOT EXISTS idx_links_source ON links(source)",
        "CREATE INDEX IF NOT EXISTS idx_links_target ON links(target)",
        "CREATE INDEX IF NOT EXISTS idx_links_weight ON links(weight)",
    ]
    
    for index_sql in indexes:
        conn.execute(index_sql)
    
    conn.commit()
    print("✅ Indexes created")


def add_metadata(conn):
    """Add metadata about the database creation."""
    
    print("Adding metadata...")
    
    # Get statistics
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM nodes")
    nodes_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM links") 
    links_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM topics")
    topics_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT community) FROM nodes")
    communities_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(email_count) FROM nodes")
    total_emails = cursor.fetchone()[0] or 0
    
    # Add metadata
    metadata_entries = [
        ('db_created_at', datetime.now().isoformat()),
        ('db_version', '1.0'),
        ('total_nodes', str(nodes_count)),
        ('total_links', str(links_count)),
        ('total_topics', str(topics_count)),
        ('total_communities', str(communities_count)),
        ('total_emails', str(total_emails)),
        ('source', 'visualization_data_migration'),
        ('schema_version', '1.0')
    ]
    
    for key, value in metadata_entries:
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()
    print(f"✅ Added metadata: {nodes_count} nodes, {links_count} links, {topics_count} topics")


def get_database_stats(db_path):
    """Get and display database statistics."""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n📊 Database Statistics for {db_path}:")
    print("=" * 50)
    
    # Table sizes
    tables = ['nodes', 'links', 'topics', 'metadata']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:15}: {count:,} records")
    
    # File size
    file_size = os.path.getsize(db_path)
    size_mb = file_size / (1024 * 1024)
    print(f"{'File size':15}: {size_mb:.2f} MB")
    
    # Sample data
    print(f"\n📋 Sample Node Data:")
    cursor.execute("SELECT id, email_count, community, degree_centrality FROM nodes ORDER BY email_count DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} emails, community {row[2]}, centrality {row[3]:.4f}")
    
    conn.close()


if __name__ == "__main__":
    print("🚀 Starting IETF Network Database Creation")
    print("=" * 50)
    
    # Create the database
    db_path = create_network_database()
    
    # Show statistics
    get_database_stats(db_path)
    
    print("\n✅ Migration complete!")
    print(f"Network database created at: {db_path}")
    print("You can now run the API server with the new database.")
