"""
SQL-based IETF data retrieval for the API backend.
Provides efficient data access methods using SQLite.
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime


class IETFDatabaseManager:
    """
    Manages IETF data storage and retrieval using SQLite.
    Provides methods to initialize database, import data, and query efficiently.
    """
    
    def __init__(self, db_path: str = "cache/ietf_network.db"):
        """Initialize database manager with specified database path."""
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection with row factory for dict results."""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_database(self):
        """Create database schema if not exists."""
        conn = self.connect()
        
        # Create nodes table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            email_count INTEGER,
            mailing_lists_count INTEGER, 
            activity_duration_days INTEGER,
            degree_centrality REAL,
            betweenness_centrality REAL,
            community INTEGER,
            dominant_topic INTEGER
        )
        ''')
        
        # Create links table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            target TEXT, 
            weight REAL,
            interaction_type TEXT,
            FOREIGN KEY (source) REFERENCES nodes (id),
            FOREIGN KEY (target) REFERENCES nodes (id)
        )
        ''')
        
        # Create topics table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            words TEXT,
            top_participants TEXT
        )
        ''')
        
        # Create metadata table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        # Create indexes for performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_node_community ON nodes(community)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_node_degree ON nodes(degree_centrality)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_node_emails ON nodes(email_count)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_links_source ON links(source)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_links_target ON links(target)')
        
        conn.commit()
        return conn
    
    def import_data_from_json(self, json_path: str = "visualisation/data.json"):
        """
        Import data from the visualization JSON file into the database.
        
        Args:
            json_path: Path to the data.json file
        
        Returns:
            dict with import statistics
        """
        if not os.path.exists(json_path):
            return {"error": f"Data file not found: {json_path}"}
            
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        conn = self.connect()
        
        # Clear existing data
        conn.execute("DELETE FROM nodes")
        conn.execute("DELETE FROM links")
        conn.execute("DELETE FROM topics")
        conn.execute("DELETE FROM metadata")
        
        # Import nodes
        for node in data['nodes']:
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
        
        # Import links
        for link in data['links']:
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
        
        # Import topics
        if 'topics' in data:
            for topic in data['topics']:
                conn.execute(
                    "INSERT INTO topics (id, words, top_participants) VALUES (?, ?, ?)",
                    (
                        topic['id'],
                        json.dumps(topic.get('words', [])),
                        json.dumps(topic.get('top_participants', []))
                    )
                )
        
        # Import metadata
        if 'metadata' in data:
            for key, value in data['metadata'].items():
                conn.execute(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    (key, json.dumps(value))
                )
        
        # Add import metadata
        conn.execute(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            ('last_import', datetime.now().isoformat())
        )
        
        conn.commit()
        
        # Get statistics
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes")
        nodes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM links")
        links_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM topics")
        topics_count = cursor.fetchone()[0]
        
        self.close()
        
        return {
            "status": "success",
            "imported_at": datetime.now().isoformat(),
            "nodes": nodes_count,
            "links": links_count,
            "topics": topics_count
        }
    
    def get_filtered_graph(self, 
                          limit: int = 500,
                          min_degree: float = 0.0,
                          min_emails: int = 0,
                          community: Optional[List[int]] = None,
                          topic: Optional[int] = None) -> Dict[str, Any]:
        """
        Get filtered graph data for visualization.
        
        Args:
            limit: Maximum number of nodes to return
            min_degree: Minimum degree centrality threshold
            min_emails: Minimum email count threshold
            community: List of community IDs to filter by
            topic: Topic ID to filter by
            
        Returns:
            Dict with nodes and links
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Build WHERE clause for nodes
        where_clauses = []
        params = []
        
        if min_degree > 0:
            where_clauses.append("degree_centrality >= ?")
            params.append(min_degree)
        
        if min_emails > 0:
            where_clauses.append("email_count >= ?")
            params.append(min_emails)
        
        if community:
            placeholders = ','.join(['?'] * len(community))
            where_clauses.append(f"community IN ({placeholders})")
            params.extend(community)
        
        if topic is not None:
            where_clauses.append("dominant_topic = ?")
            params.append(topic)
        
        # Build the final WHERE clause
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get nodes
        cursor.execute(
            f"""
            SELECT * FROM nodes 
            WHERE {where_sql}
            ORDER BY degree_centrality DESC, email_count DESC
            LIMIT ?
            """,
            params + [limit]
        )
        
        nodes = [dict(row) for row in cursor.fetchall()]
        
        if not nodes:
            self.close()
            return {"nodes": [], "links": []}
        
        # Get node IDs for link filtering
        node_ids = [node["id"] for node in nodes]
        placeholders = ','.join(['?'] * len(node_ids))
        
        # Get links between these nodes
        cursor.execute(
            f"""
            SELECT * FROM links
            WHERE source IN ({placeholders})
            AND target IN ({placeholders})
            """,
            node_ids + node_ids
        )
        
        links = [dict(row) for row in cursor.fetchall()]
        
        self.close()
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        # Node count
        cursor.execute("SELECT COUNT(*) FROM nodes")
        stats["total_nodes"] = cursor.fetchone()[0]
        
        # Link count
        cursor.execute("SELECT COUNT(*) FROM links")
        stats["total_links"] = cursor.fetchone()[0]
        
        # Community count
        cursor.execute("SELECT COUNT(DISTINCT community) FROM nodes")
        stats["communities"] = cursor.fetchone()[0]
        
        # Topic count
        cursor.execute("SELECT COUNT(*) FROM topics")
        stats["topics"] = cursor.fetchone()[0]
        
        # Email statistics
        cursor.execute("SELECT SUM(email_count) FROM nodes")
        stats["total_emails"] = cursor.fetchone()[0]
        
        # Average emails per person
        cursor.execute("SELECT AVG(email_count) FROM nodes")
        stats["avg_emails_per_person"] = cursor.fetchone()[0]
        
        # Additional metadata
        cursor.execute("SELECT key, value FROM metadata")
        for row in cursor.fetchall():
            try:
                stats[row["key"]] = json.loads(row["value"])
            except:
                stats[row["key"]] = row["value"]
        
        self.close()
        return stats
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Get topic data."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM topics")
        topics = []
        
        for row in cursor.fetchall():
            topic = {
                "id": row["id"],
                "words": json.loads(row["words"]),
                "top_participants": json.loads(row["top_participants"])
            }
            topics.append(topic)
        
        self.close()
        return topics
    
    def get_communities(self) -> List[Dict[str, Any]]:
        """Get community statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT community, COUNT(*) as count, AVG(email_count) as avg_emails
            FROM nodes
            GROUP BY community
            ORDER BY count DESC
        """)
        
        communities = []
        for row in cursor.fetchall():
            communities.append({
                "id": row["community"],
                "size": row["count"],
                "avg_emails": row["avg_emails"]
            })
        
        self.close()
        return communities


# Example usage
if __name__ == "__main__":
    db_manager = IETFDatabaseManager()
    db_manager.initialize_database()
    
    # Import data
    result = db_manager.import_data_from_json()
    print(f"Data import result: {result}")
    
    # Test queries
    graph_data = db_manager.get_filtered_graph(limit=100, min_emails=5)
    print(f"Filtered graph: {len(graph_data['nodes'])} nodes, {len(graph_data['links'])} links")
    
    stats = db_manager.get_stats()
    print(f"Network stats: {stats}")
