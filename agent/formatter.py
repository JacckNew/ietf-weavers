"""
Formatter module to output D3.js-ready JSON files.
Formats graph and topic data for visualization.
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import os
from datetime import datetime

# Check if NetworkX is available
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

def sanitize_for_json(obj):
    """
    Recursively sanitize data for JSON serialization.
    Replace Infinity, -Infinity, and NaN with appropriate values.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return 0.0  # Replace NaN with 0
        elif math.isinf(obj):
            return 999999.0 if obj > 0 else -999999.0  # Replace Infinity with large number
        else:
            return obj
    else:
        return obj


class D3Formatter:
    """
    Format network and topic data for D3.js visualization.
    
    Output format as specified in methodology:
    {
      "nodes": [
        {"id": "user@example.com", "group": "community1", "centrality": 0.34, ...}
      ],
      "links": [
        {"source": "userA", "target": "userB", "weight": 3}
      ],
      "topics": [
        {"topic_id": 0, "keywords": ["privacy", "security"], "top_participants": [...]}
      ]
    }
    """
    
    def __init__(self):
        self.data = {
            "nodes": [],
            "links": [],
            "topics": [],
            "metadata": {}
        }
    
    def format_network_data(self, graph, metrics_data: Dict, 
                          person_resolver, communities: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Format network data for D3.js visualization.
        
        Args:
            graph: NetworkX graph or fallback graph dict
            metrics_data: Network metrics data
            person_resolver: PersonIdentityResolver instance
            communities: Community assignments
        
        Returns:
            Formatted network data
        """
        nodes = []
        links = []
        
        # Handle different graph types
        is_networkx = NETWORKX_AVAILABLE and hasattr(graph, 'nodes')
        
        # Format nodes
        individual_features = metrics_data.get('individual_features', {})
        
        if is_networkx:
            node_ids = list(graph.nodes())
        else:
            node_ids = list(graph.get('nodes', set())) if isinstance(graph, dict) else []
        
        for node_id in node_ids:
            if is_networkx:
                node_data = graph.nodes.get(node_id, {})
            else:
                node_data = {}
                
            features = individual_features.get(node_id, {})
            
            # Get primary email for display
            emails = person_resolver.person_to_emails.get(node_id, [])
            primary_email = emails[0] if emails else node_id
            
            node = {
                "id": node_id,
                "email": primary_email,
                "name": person_resolver.person_to_name.get(node_id, primary_email),
                
                # Centrality measures (with defaults for missing NetworkX)
                "degree_centrality": features.get('degree_centrality', 0),
                "betweenness_centrality": features.get('betweenness_centrality', 0),
                "closeness_centrality": features.get('closeness_centrality', 0),
                "eigenvector_centrality": features.get('eigenvector_centrality', 0),
                "pagerank": features.get('pagerank', 0),
                
                # Network position
                "degree": features.get('degree', 0),
                "clustering_coefficient": features.get('clustering_coefficient', 0),
                
                # Activity metrics
                "email_count": features.get('email_count', 0),
                "mailing_lists_count": features.get('mailing_lists_count', 0),
                "activity_duration_days": features.get('activity_duration_days', 0),
                
                # Community assignment
                "group": communities.get(node_id, 0) if communities else 0,
                "community": communities.get(node_id, 0) if communities else 0,
                
                # Temporal data
                "first_email": features.get('first_email', ''),
                "last_email": features.get('last_email', ''),
                
                # Additional attributes
                "mailing_lists": features.get('mailing_lists', []),
                "total_interaction_weight": features.get('total_interaction_weight', 0)
            }
            
            nodes.append(node)
        
        # Format links
        relationship_features = metrics_data.get('relationship_features', [])
        
        if relationship_features:
            # Use relationship features if available
            for edge_data in relationship_features:
                link = {
                    "source": edge_data['source'],
                    "target": edge_data['target'],
                    "weight": edge_data.get('interaction_frequency', 1),
                    "type": edge_data.get('interaction_type', 'unknown'),
                    "is_reciprocal": edge_data.get('is_reciprocal', False),
                    "reciprocal_weight": edge_data.get('reciprocal_weight', 0)
                }
                
                # Add any additional edge attributes
                for key, value in edge_data.items():
                    if key not in ['source', 'target', 'interaction_frequency', 'interaction_type', 
                                  'is_reciprocal', 'reciprocal_weight']:
                        link[key] = value
                
                links.append(link)
        elif is_networkx:
            # Extract from NetworkX graph
            for source, target in graph.edges():
                edge_data = graph[source][target]
                link = {
                    "source": source,
                    "target": target,
                    "weight": edge_data.get('weight', 1),
                    "type": edge_data.get('interaction_type', 'unknown'),
                    "is_reciprocal": graph.has_edge(target, source)
                }
                links.append(link)
        elif isinstance(graph, dict) and 'edges' in graph:
            # Extract from fallback graph
            for edge in graph['edges']:
                if len(edge) >= 4:
                    source, target, weight, interaction_type = edge[:4]
                    link = {
                        "source": source,
                        "target": target,
                        "weight": weight,
                        "type": interaction_type,
                        "is_reciprocal": False  # Could be enhanced
                    }
                    links.append(link)
        
        return {"nodes": nodes, "links": links}
    
    def format_topic_data(self, topic_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format topic modeling results for visualization.
        
        Args:
            topic_analysis: Topic analysis results
        
        Returns:
            Formatted topic data
        """
        topics = []
        
        for topic_data in topic_analysis.get('topics', []):
            topic = {
                "topic_id": topic_data['topic_id'],
                "keywords": topic_data['keywords'],
                "top_participants": [
                    {
                        "person_id": p['person_id'],
                        "name": p['name'],
                        "probability": p['probability'],
                        "primary_email": p['emails'][0] if p['emails'] else p['person_id']
                    }
                    for p in topic_data.get('top_participants', [])[:10]  # Limit to top 10
                ]
            }
            topics.append(topic)
        
        return topics
    
    def add_temporal_data(self, temporal_snapshots: Dict[str, Any]):
        """Add temporal network snapshots for timeline visualization."""
        self.data["temporal"] = temporal_snapshots
    
    def add_metadata(self, network_stats: Dict[str, Any], topic_stats: Dict[str, Any] = None):
        """Add metadata about the analysis."""
        self.data["metadata"] = {
            "network": network_stats,
            "topics": topic_stats or {},
            "generated_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    
    def combine_data(self, network_data: Dict[str, Any], topic_data: List[Dict[str, Any]],
                    metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Combine network and topic data into final visualization format.
        
        Args:
            network_data: Formatted network data
            topic_data: Formatted topic data
            metadata: Additional metadata
        
        Returns:
            Complete visualization data
        """
        # Add topic entropy to nodes
        if topic_data and 'participants' in topic_data:
            participant_data = topic_data.get('participants', {})
            
            for node in network_data['nodes']:
                person_id = node['id']
                if person_id in participant_data:
                    node['topic_entropy'] = participant_data[person_id].get('topic_entropy', 0)
                    node['dominant_topics'] = participant_data[person_id].get('dominant_topics', [])
        
        combined_data = {
            "nodes": network_data['nodes'],
            "links": network_data['links'],
            "topics": topic_data if isinstance(topic_data, list) else [],
            "metadata": metadata or {}
        }
        
        return combined_data
    
    def export_d3_json(self, output_file: str, network_data: Dict[str, Any], 
                      topic_data: List[Dict[str, Any]] = None, 
                      metadata: Dict[str, Any] = None):
        """
        Export complete D3.js-ready JSON file.
        
        Args:
            output_file: Output file path
            network_data: Network data (nodes and links)
            topic_data: Topic modeling results
            metadata: Additional metadata
        """
        # Combine all data
        complete_data = self.combine_data(network_data, topic_data or [], metadata or {})
        
        # Ensure JSON serializable
        def make_serializable(obj):
            if isinstance(obj, (datetime,)):
                return obj.isoformat()
            elif isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, float):
                if math.isnan(obj):
                    return 0.0
                elif math.isinf(obj):
                    return 999999.0 if obj > 0 else -999999.0
                else:
                    return obj
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            return obj
        
        # Sanitize data
        complete_data = sanitize_for_json(complete_data)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(complete_data, f, indent=2, default=make_serializable)
        
        return complete_data
    
    def export_timeline_data(self, temporal_data: Dict[str, Dict[str, Any]], 
                           output_file: str):
        """Export temporal network data for timeline visualization."""
        timeline_data = {
            "timeline": temporal_data,
            "metadata": {
                "time_periods": list(temporal_data.keys()),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(timeline_data, f, indent=2, default=str)
        
        return timeline_data
    
    def create_summary_stats(self, network_data: Dict[str, Any], 
                           topic_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create summary statistics for the visualization."""
        stats = {}
        
        # Network statistics
        nodes = network_data.get('nodes', [])
        links = network_data.get('links', [])
        
        stats['network'] = {
            'total_nodes': len(nodes),
            'total_links': len(links),
            'avg_degree': sum(node.get('degree', 0) for node in nodes) / len(nodes) if nodes else 0,
            'max_centrality': max(node.get('betweenness_centrality', 0) for node in nodes) if nodes else 0,
            'communities': len(set(node.get('community', 0) for node in nodes)) if nodes else 0
        }
        
        # Topic statistics
        if topic_data:
            stats['topics'] = {
                'total_topics': len(topic_data),
                'avg_keywords_per_topic': sum(len(t.get('keywords', [])) for t in topic_data) / len(topic_data) if topic_data else 0,
                'topics_with_participants': sum(1 for t in topic_data if t.get('top_participants'))
            }
        
        return stats


def format_for_visualization(graph, metrics_data: Dict, person_resolver,
                           topic_analysis: Dict = None, communities: Dict = None) -> Dict[str, Any]:
    """
    Main function to format all data for D3.js visualization.
    
    Args:
        graph: NetworkX graph or fallback graph dict
        metrics_data: Network metrics results
        person_resolver: PersonIdentityResolver instance
        topic_analysis: Topic modeling results (optional)
        communities: Community assignments (optional)
    
    Returns:
        Complete formatted data for visualization
    """
    formatter = D3Formatter()
    
    # Format network data
    network_data = formatter.format_network_data(graph, metrics_data, person_resolver, communities)
    
    # Format topic data
    topic_data = []
    if topic_analysis:
        topic_data = formatter.format_topic_data(topic_analysis)
    
    # Create metadata
    metadata = formatter.create_summary_stats(network_data, topic_data)
    
    # Combine everything
    complete_data = formatter.combine_data(network_data, topic_data, metadata)
    
    return complete_data