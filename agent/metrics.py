"""
Network metrics calculation for social network analysis.
Calculates centrality and network features based on methodology.
"""

from typing import Dict, List, Tuple, Any
from collections import defaultdict

try:
    import networkx as nx
    import numpy as np
    import community as community_louvain  # python-louvain
    NETWORKX_AVAILABLE = True
except ImportError as e:
    NETWORKX_AVAILABLE = False
    print(f"Warning: NetworkX dependencies not available: {e}")
    print("Please install: pip install networkx numpy python-louvain")


class NetworkMetrics:
    """
    Calculate comprehensive network metrics following the methodology:
    - Degree, betweenness, closeness centrality
    - Community detection using Louvain
    - Participation duration, area coverage, and mail volume
    """
    
    def __init__(self, graph):
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX dependencies not available. Please install required packages.")
        
        self.graph = graph
        self.metrics = {}
    
    def calculate_centrality_measures(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate centrality measures for all nodes.
        
        Returns:
            Dictionary with centrality scores for each node
        """
        centrality_metrics = {}
        
        # Degree centrality
        degree_centrality = nx.degree_centrality(self.graph)
        
        # Betweenness centrality
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        # Closeness centrality
        closeness_centrality = nx.closeness_centrality(self.graph)
        
        # Eigenvector centrality (handle disconnected components)
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
        except:
            eigenvector_centrality = {node: 0.0 for node in self.graph.nodes()}
        
        # PageRank (useful for directed graphs)
        pagerank = nx.pagerank(self.graph)
        
        # Combine all centrality measures
        for node in self.graph.nodes():
            centrality_metrics[node] = {
                'degree_centrality': degree_centrality.get(node, 0.0),
                'betweenness_centrality': betweenness_centrality.get(node, 0.0),
                'closeness_centrality': closeness_centrality.get(node, 0.0),
                'eigenvector_centrality': eigenvector_centrality.get(node, 0.0),
                'pagerank': pagerank.get(node, 0.0)
            }
        
        return centrality_metrics
    
    def detect_communities(self) -> Dict[str, int]:
        """
        Detect communities using Louvain algorithm.
        
        Returns:
            Dictionary mapping node to community ID
        """
        # Convert to undirected graph for community detection
        if self.graph.is_directed():
            undirected_graph = self.graph.to_undirected()
        else:
            undirected_graph = self.graph
        
        # Apply Louvain community detection
        try:
            communities = community_louvain.best_partition(undirected_graph)
        except:
            # Fallback: assign all nodes to community 0
            communities = {node: 0 for node in self.graph.nodes()}
        
        return communities
    
    def calculate_structural_features(self) -> Dict[str, Any]:
        """Calculate network-level structural features."""
        features = {}
        
        # Basic network properties
        features['num_nodes'] = self.graph.number_of_nodes()
        features['num_edges'] = self.graph.number_of_edges()
        features['density'] = nx.density(self.graph)
        
        # Connectivity measures
        if nx.is_connected(self.graph.to_undirected() if self.graph.is_directed() else self.graph):
            features['diameter'] = nx.diameter(self.graph.to_undirected() if self.graph.is_directed() else self.graph)
            features['average_path_length'] = nx.average_shortest_path_length(
                self.graph.to_undirected() if self.graph.is_directed() else self.graph
            )
        else:
            features['diameter'] = None
            features['average_path_length'] = None
        
        # Clustering
        features['average_clustering'] = nx.average_clustering(
            self.graph.to_undirected() if self.graph.is_directed() else self.graph
        )
        
        # Degree distribution
        degrees = [d for n, d in self.graph.degree()]
        features['average_degree'] = np.mean(degrees)
        features['degree_std'] = np.std(degrees)
        features['max_degree'] = max(degrees) if degrees else 0
        features['min_degree'] = min(degrees) if degrees else 0
        
        return features
    
    def calculate_individual_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate individual-level features following methodology:
        - Communication volume
        - Network position
        - Temporal activity
        - Influence metrics
        - Collaboration breadth
        """
        individual_features = {}
        
        # Get centrality measures
        centrality_metrics = self.calculate_centrality_measures()
        
        # Get community assignments
        communities = self.detect_communities()
        
        for node in self.graph.nodes():
            features = {}
            node_data = self.graph.nodes[node]
            
            # Copy existing node attributes
            features.update(node_data)
            
            # Add centrality measures
            features.update(centrality_metrics.get(node, {}))
            
            # Add community assignment
            features['community'] = communities.get(node, -1)
            
            # Network position features
            features['degree'] = self.graph.degree(node)
            features['in_degree'] = self.graph.in_degree(node) if self.graph.is_directed() else features['degree']
            features['out_degree'] = self.graph.out_degree(node) if self.graph.is_directed() else features['degree']
            
            # Local clustering coefficient
            features['clustering_coefficient'] = nx.clustering(
                self.graph.to_undirected() if self.graph.is_directed() else self.graph, 
                node
            )
            
            # Neighbor characteristics
            neighbors = list(self.graph.neighbors(node))
            features['num_neighbors'] = len(neighbors)
            
            if neighbors:
                neighbor_degrees = [self.graph.degree(neighbor) for neighbor in neighbors]
                features['avg_neighbor_degree'] = np.mean(neighbor_degrees)
                features['max_neighbor_degree'] = max(neighbor_degrees)
            else:
                features['avg_neighbor_degree'] = 0
                features['max_neighbor_degree'] = 0
            
            # Influence metrics (based on edge weights if available)
            edge_weights = []
            for neighbor in neighbors:
                if 'weight' in self.graph[node][neighbor]:
                    edge_weights.append(self.graph[node][neighbor]['weight'])
            
            if edge_weights:
                features['total_interaction_weight'] = sum(edge_weights)
                features['avg_interaction_weight'] = np.mean(edge_weights)
                features['max_interaction_weight'] = max(edge_weights)
            else:
                features['total_interaction_weight'] = 0
                features['avg_interaction_weight'] = 0
                features['max_interaction_weight'] = 0
            
            individual_features[node] = features
        
        return individual_features
    
    def calculate_relationship_features(self) -> List[Dict[str, Any]]:
        """
        Calculate relationship-level features:
        - Interaction frequency
        - Response latency (if temporal data available)
        - Thread participation
        - Topic overlap
        """
        relationship_features = []
        
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            features = {
                'source': source,
                'target': target,
                'interaction_frequency': edge_data.get('weight', 1),
                'interaction_type': edge_data.get('interaction_type', 'unknown')
            }
            
            # Add other edge attributes
            for key, value in edge_data.items():
                if key not in ['weight', 'interaction_type']:
                    features[key] = value
            
            # Calculate reciprocity
            features['is_reciprocal'] = self.graph.has_edge(target, source)
            if features['is_reciprocal']:
                features['reciprocal_weight'] = self.graph[target][source].get('weight', 1)
                if features['reciprocal_weight'] > 0:
                    features['reciprocity_ratio'] = features['interaction_frequency'] / features['reciprocal_weight']
                else:
                    features['reciprocity_ratio'] = float('inf')
            else:
                features['reciprocal_weight'] = 0
                features['reciprocity_ratio'] = float('inf')
            
            relationship_features.append(features)
        
        return relationship_features
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive network analysis report."""
        report = {}
        
        # Network-level features
        report['network_structure'] = self.calculate_structural_features()
        
        # Individual features
        report['individual_features'] = self.calculate_individual_features()
        
        # Relationship features
        report['relationship_features'] = self.calculate_relationship_features()
        
        # Community analysis
        communities = self.detect_communities()
        community_sizes = defaultdict(int)
        for node, community in communities.items():
            community_sizes[community] += 1
        
        report['community_analysis'] = {
            'num_communities': len(community_sizes),
            'community_sizes': dict(community_sizes),
            'modularity': community_louvain.modularity(communities, self.graph.to_undirected() if self.graph.is_directed() else self.graph)
        }
        
        return report
    
    def export_features_csv(self, output_file: str):
        """Export individual features to CSV file."""
        try:
            import pandas as pd
        except ImportError:
            print("Warning: pandas not available. Cannot export CSV. Please install: pip install pandas")
            return None
        
        individual_features = self.calculate_individual_features()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(individual_features, orient='index')
        df.index.name = 'person_id'
        
        # Save to CSV
        df.to_csv(output_file)
        
        return df


def calculate_network_metrics(graph) -> NetworkMetrics:
    """Calculate all network metrics for a given graph."""
    if not NETWORKX_AVAILABLE:
        print("Warning: NetworkX not available. Returning empty metrics.")
        return None
    
    metrics_calculator = NetworkMetrics(graph)
    return metrics_calculator


def compare_networks(graphs: Dict[str, Any]) -> Dict[str, Any]:
    """Compare multiple networks (e.g., different time periods)."""
    if not NETWORKX_AVAILABLE:
        print("Warning: NetworkX not available. Cannot compare networks.")
        return {}
    
    comparison = {}
    
    for name, graph in graphs.items():
        metrics = NetworkMetrics(graph)
        comparison[name] = metrics.calculate_structural_features()
    
    return comparison