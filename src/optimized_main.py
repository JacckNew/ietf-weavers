"""
Optimized main pipeline for large-scale IETF data processing.
Uses sampling, batching, and performance optimizations for datasets with 100k+ messages.
"""

import os
import sys
import json
import random
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse
from collections import defaultdict, Counter
import multiprocessing as mp

# Add project root and agent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agent'))

try:
    import networkx as nx
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.cluster import KMeans
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: Some dependencies not available. Install: pip install networkx scikit-learn")

from agent.utils import PersonIdentityResolver, EmailParser


class OptimizedIETFProcessor:
    """
    Optimized processor for large IETF datasets.
    
    Key optimizations:
    1. Sampling: Process representative subset instead of entire dataset
    2. Efficient graph construction: Avoid O(n²) operations
    3. Fast topic modeling: Use LDA instead of BERTopic for speed
    4. Batch processing: Process data in chunks
    5. Parallel processing: Use multiprocessing where possible
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.person_resolver = PersonIdentityResolver()
        self.email_parser = EmailParser()
        
        # Results storage
        self.graph = None
        self.metrics_data = None
        self.topic_analysis = None
        
        # Performance tracking
        self.processing_stats = {
            'total_emails': 0,
            'sampled_emails': 0,
            'processing_time': 0.0,
            'nodes': 0,
            'edges': 0
        }
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration optimized for large datasets."""
        return {
            'sample_rate': 0.1,  # Process 10% of data for speed
            'min_sample_size': 5000,  # Minimum number of emails to sample
            'max_sample_size': 50000,  # Maximum number of emails to sample
            'n_topics': 20,  # Reduced from 50 for speed
            'min_emails_per_person': 3,  # Reduced threshold
            'batch_size': 1000,  # Process in batches
            'use_multiprocessing': True,
            'n_processes': min(4, mp.cpu_count()),
            'output_dir': 'visualisation',
            'export_individual_features': True
        }
    
    def load_and_sample_data(self, data_source: str) -> List[Dict]:
        """
        Load and intelligently sample email data.
        
        Strategy:
        1. Load metadata first to understand distribution
        2. Stratified sampling by mailing list and time
        3. Ensure key participants are included
        """
        print(f"Loading data from: {data_source}")
        start_time = datetime.now()
        
        # Load data
        if data_source.endswith('.json'):
            with open(data_source, 'r', encoding='utf-8') as f:
                all_emails = json.load(f)
        else:
            print(f"Unsupported format: {data_source}")
            return []
        
        self.processing_stats['total_emails'] = len(all_emails)
        print(f"Loaded {len(all_emails):,} total emails")
        
        # Quick analysis for sampling strategy
        mailing_lists = Counter()
        date_distribution = Counter()
        sender_counts = Counter()
        
        print("Analyzing data distribution...")
        for email in all_emails[:min(10000, len(all_emails))]:  # Sample for analysis
            mailing_list = email.get('mailing_list', email.get('list_name', 'unknown'))
            mailing_lists[mailing_list] += 1
            
            from_email = email.get('from', '')
            if self.email_parser.classify_email_type(from_email) == 'individual':
                sender_counts[from_email] += 1
            
            # Extract year-month for temporal distribution
            date_str = email.get('date', '')
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                year_month = f"{date_obj.year}-{date_obj.month:02d}"
                date_distribution[year_month] += 1
            except:
                pass
        
        print(f"Found {len(mailing_lists)} mailing lists")
        print(f"Found {len(sender_counts)} unique senders")
        print(f"Date range: {min(date_distribution.keys())} to {max(date_distribution.keys())}")
        
        # Calculate sample size
        sample_size = int(len(all_emails) * self.config['sample_rate'])
        sample_size = max(self.config['min_sample_size'], 
                         min(sample_size, self.config['max_sample_size']))
        
        print(f"Target sample size: {sample_size:,} ({sample_size/len(all_emails)*100:.1f}%)")
        
        # Stratified sampling
        sampled_emails = self._stratified_sample(all_emails, sample_size, 
                                               mailing_lists, sender_counts)
        
        self.processing_stats['sampled_emails'] = len(sampled_emails)
        processing_time = (datetime.now() - start_time).total_seconds()
        self.processing_stats['processing_time'] += processing_time
        
        print(f"Sampled {len(sampled_emails):,} emails in {processing_time:.1f}s")
        return sampled_emails
    
    def _stratified_sample(self, all_emails: List[Dict], target_size: int,
                          mailing_lists: Counter, sender_counts: Counter) -> List[Dict]:
        """
        Perform stratified sampling to ensure representative data.
        """
        # Ensure we include top senders (key participants)
        top_senders = set([email for email, count in sender_counts.most_common(100)])
        
        # Group emails by mailing list
        emails_by_list = defaultdict(list)
        for email in all_emails:
            mailing_list = email.get('mailing_list', email.get('list_name', 'unknown'))
            emails_by_list[mailing_list].append(email)
        
        sampled = []
        
        # Sample proportionally from each mailing list
        total_lists = len(emails_by_list)
        for mailing_list, emails in emails_by_list.items():
            # Calculate proportional sample size
            list_proportion = len(emails) / len(all_emails)
            list_sample_size = int(target_size * list_proportion)
            list_sample_size = max(10, min(list_sample_size, len(emails)))  # At least 10, at most all
            
            # Prioritize emails from top senders
            priority_emails = []
            regular_emails = []
            
            for email in emails:
                from_email = email.get('from', '')
                if (self.email_parser.classify_email_type(from_email) == 'individual' and 
                    from_email in top_senders):
                    priority_emails.append(email)
                elif self.email_parser.classify_email_type(from_email) == 'individual':
                    regular_emails.append(email)
            
            # Sample: prioritize key participants, then random
            list_sample = []
            
            # Take some priority emails
            priority_count = min(len(priority_emails), list_sample_size // 3)
            if priority_emails:
                list_sample.extend(random.sample(priority_emails, priority_count))
            
            # Fill the rest randomly
            remaining = list_sample_size - len(list_sample)
            if regular_emails and remaining > 0:
                remaining = min(remaining, len(regular_emails))
                list_sample.extend(random.sample(regular_emails, remaining))
            
            sampled.extend(list_sample)
        
        # If we still need more, add random samples
        if len(sampled) < target_size:
            remaining_emails = [email for email in all_emails 
                              if email not in sampled and 
                              self.email_parser.classify_email_type(email.get('from', '')) == 'individual']
            
            if remaining_emails:
                additional_needed = min(target_size - len(sampled), len(remaining_emails))
                sampled.extend(random.sample(remaining_emails, additional_needed))
        
        # Shuffle the final sample
        random.shuffle(sampled)
        return sampled[:target_size]
    
    def build_efficient_graph(self, email_data: List[Dict]) -> Any:
        """
        Build social graph with performance optimizations.
        
        Optimizations:
        1. Process in batches
        2. Use hash maps for fast lookups
        3. Avoid expensive O(n²) operations where possible
        """
        print("Building social graph...")
        start_time = datetime.now()
        
        if not DEPENDENCIES_AVAILABLE:
            print("NetworkX not available, returning None")
            return None
        
        graph = nx.DiGraph()
        
        # Track interactions efficiently
        person_data = defaultdict(lambda: {
            'emails': [],
            'mailing_lists': set(),
            'first_date': None,
            'last_date': None,
            'email_count': 0
        })
        
        reply_pairs = []
        message_to_sender = {}
        
        # Process emails in batches
        batch_size = self.config['batch_size']
        total_batches = (len(email_data) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            if batch_idx % 10 == 0:
                print(f"Processing batch {batch_idx + 1}/{total_batches}")
            
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(email_data))
            batch = email_data[start_idx:end_idx]
            
            for email in batch:
                from_email = email.get('from', '')
                message_id = email.get('message_id', '')
                in_reply_to = email.get('in_reply_to', '')
                mailing_list = email.get('mailing_list', email.get('list_name', ''))
                date_str = email.get('date', '')
                
                # Skip non-individual emails
                if self.email_parser.classify_email_type(from_email) != 'individual':
                    continue
                
                # Map email to person
                person_id = self.person_resolver.add_email_mapping(from_email)
                if not person_id:
                    continue
                
                # Track message sender for reply analysis
                if message_id:
                    message_to_sender[message_id] = person_id
                
                # Update person data
                person_data[person_id]['email_count'] += 1
                person_data[person_id]['emails'].append(email)
                if mailing_list:
                    person_data[person_id]['mailing_lists'].add(mailing_list)
                
                # Track temporal data
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if person_data[person_id]['first_date'] is None:
                        person_data[person_id]['first_date'] = date_obj
                        person_data[person_id]['last_date'] = date_obj
                    else:
                        person_data[person_id]['first_date'] = min(person_data[person_id]['first_date'], date_obj)
                        person_data[person_id]['last_date'] = max(person_data[person_id]['last_date'], date_obj)
                except:
                    pass
                
                # Track reply relationships
                if in_reply_to and in_reply_to in message_to_sender:
                    original_sender = message_to_sender[in_reply_to]
                    if original_sender != person_id:  # Don't count self-replies
                        reply_pairs.append((person_id, original_sender))
        
        # Filter people by minimum email threshold
        min_emails = self.config['min_emails_per_person']
        active_people = {person_id for person_id, data in person_data.items() 
                        if data['email_count'] >= min_emails}
        
        print(f"Found {len(active_people)} active participants (>= {min_emails} emails)")
        
        # Add nodes to graph
        for person_id in active_people:
            data = person_data[person_id]
            
            # Calculate attributes
            duration = 0
            if data['first_date'] and data['last_date']:
                duration = (data['last_date'] - data['first_date']).days
            
            # Add node with attributes
            graph.add_node(person_id, 
                          email_count=data['email_count'],
                          mailing_lists_count=len(data['mailing_lists']),
                          activity_duration_days=duration,
                          first_email=data['first_date'].isoformat() if data['first_date'] else None,
                          last_email=data['last_date'].isoformat() if data['last_date'] else None)
        
        # Add edges from reply relationships
        edge_weights = Counter()
        for replier, original in reply_pairs:
            if replier in active_people and original in active_people:
                edge_weights[(replier, original)] += 1
        
        for (replier, original), weight in edge_weights.items():
            graph.add_edge(replier, original, weight=weight, interaction_type='reply')
        
        self.processing_stats['nodes'] = graph.number_of_nodes()
        self.processing_stats['edges'] = graph.number_of_edges()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges in {processing_time:.1f}s")
        
        return graph
    
    def calculate_fast_metrics(self, graph: nx.DiGraph) -> Dict:
        """Calculate essential network metrics efficiently."""
        print("Calculating network metrics...")
        start_time = datetime.now()
        
        metrics = {}
        
        # Basic centrality measures (most important)
        print("Calculating degree centrality...")
        metrics['degree_centrality'] = nx.degree_centrality(graph)
        
        print("Calculating betweenness centrality...")
        # Use approximation for large graphs
        if graph.number_of_nodes() > 1000:
            k = min(100, graph.number_of_nodes())  # Sample nodes for approximation
            metrics['betweenness_centrality'] = nx.betweenness_centrality(graph, k=k)
        else:
            metrics['betweenness_centrality'] = nx.betweenness_centrality(graph)
        
        # Community detection (fast algorithm)
        print("Detecting communities...")
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(graph.to_undirected())
            metrics['community'] = partition
        except ImportError:
            # Fallback to simple connected components
            undirected = graph.to_undirected()
            components = nx.connected_components(undirected)
            partition = {}
            for i, component in enumerate(components):
                for node in component:
                    partition[node] = i
            metrics['community'] = partition
        
        # Calculate additional node attributes
        for node in graph.nodes():
            node_data = graph.nodes[node]
            node_data['degree_centrality'] = metrics['degree_centrality'].get(node, 0)
            node_data['betweenness_centrality'] = metrics['betweenness_centrality'].get(node, 0)
            node_data['community'] = metrics['community'].get(node, 0)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Metrics calculated in {processing_time:.1f}s")
        
        return metrics
    
    def run_fast_topic_analysis(self, email_data: List[Dict]) -> Dict:
        """
        Fast topic analysis using LDA instead of BERTopic.
        Much faster for large datasets.
        """
        print("Running fast topic analysis...")
        start_time = datetime.now()
        
        if not DEPENDENCIES_AVAILABLE:
            print("Scikit-learn not available, skipping topic analysis")
            return {'topics': [], 'person_topics': {}}
        
        # Prepare documents (one per person)
        person_documents = defaultdict(list)
        
        for email in email_data:
            from_email = email.get('from', '')
            content = email.get('content', '')
            subject = email.get('subject', '')
            
            if self.email_parser.classify_email_type(from_email) != 'individual':
                continue
                
            person_id = self.person_resolver.email_to_person.get(from_email)
            if person_id and content:
                # Combine subject and content
                text = f"{subject} {content}"
                person_documents[person_id].append(text)
        
        # Concatenate documents per person
        documents = []
        person_order = []
        
        for person_id, texts in person_documents.items():
            if len(texts) >= self.config['min_emails_per_person']:
                combined_text = ' '.join(texts)
                documents.append(combined_text)
                person_order.append(person_id)
        
        if len(documents) < 2:
            print("Not enough documents for topic analysis")
            return {'topics': [], 'person_topics': {}}
        
        print(f"Processing {len(documents)} person documents for topic analysis")
        
        # Vectorize documents
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        doc_term_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        
        # LDA topic modeling
        n_topics = min(self.config['n_topics'], len(documents) // 2)
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=10,  # Reduced iterations for speed
            n_jobs=-1
        )
        
        lda.fit(doc_term_matrix)
        doc_topic_dist = lda.transform(doc_term_matrix)
        
        # Extract topics
        topics = []
        for topic_idx in range(n_topics):
            top_words_idx = lda.components_[topic_idx].argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topics.append({
                'id': topic_idx,
                'words': top_words,
                'top_participants': []
            })
        
        # Assign dominant topics to participants
        person_topics = {}
        for i, person_id in enumerate(person_order):
            dominant_topic = np.argmax(doc_topic_dist[i])
            person_topics[person_id] = dominant_topic
        
        # Add top participants to topics
        topic_participants = defaultdict(list)
        for person_id, topic_id in person_topics.items():
            topic_participants[topic_id].append(person_id)
        
        for topic in topics:
            topic['top_participants'] = topic_participants[topic['id']][:5]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Topic analysis completed in {processing_time:.1f}s")
        
        return {
            'topics': topics,
            'person_topics': person_topics
        }
    
    def export_visualization_data(self, graph: nx.DiGraph, topic_analysis: Dict):
        """Export data for D3.js visualization."""
        print("Exporting visualization data...")
        
        # Prepare nodes
        nodes = []
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id].copy()
            node_data['id'] = node_id
            
            # Add topic information
            if node_id in topic_analysis['person_topics']:
                node_data['dominant_topic'] = topic_analysis['person_topics'][node_id]
            
            nodes.append(node_data)
        
        # Prepare links
        links = []
        for source, target in graph.edges():
            edge_data = graph[source][target].copy()
            edge_data['source'] = source
            edge_data['target'] = target
            links.append(edge_data)
        
        # Prepare visualization data
        viz_data = {
            'nodes': nodes,
            'links': links,
            'topics': topic_analysis['topics'],
            'metadata': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'total_topics': len(topic_analysis['topics']),
                'processing_stats': self.processing_stats,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        # Export main visualization data
        output_file = os.path.join(self.config['output_dir'], 'data.json')
        with open(output_file, 'w') as f:
            json.dump(viz_data, f, indent=2)
        
        # Export individual features CSV
        if self.config['export_individual_features']:
            import pandas as pd
            
            features_data = []
            for node in nodes:
                features_data.append({
                    'person_id': node['id'],
                    'email_count': node.get('email_count', 0),
                    'degree_centrality': node.get('degree_centrality', 0),
                    'betweenness_centrality': node.get('betweenness_centrality', 0),
                    'community': node.get('community', 0),
                    'mailing_lists_count': node.get('mailing_lists_count', 0),
                    'activity_duration_days': node.get('activity_duration_days', 0),
                    'dominant_topic': node.get('dominant_topic', -1)
                })
            
            df = pd.DataFrame(features_data)
            features_file = os.path.join(self.config['output_dir'], 'individual_features.csv')
            df.to_csv(features_file, index=False)
        
        # Export topic analysis
        topic_file = os.path.join(self.config['output_dir'], 'topic_analysis.json')
        with open(topic_file, 'w') as f:
            json.dump(topic_analysis, f, indent=2)
        
        print(f"Visualization data exported to {self.config['output_dir']}/")
        print(f"- Nodes: {len(nodes)}")
        print(f"- Links: {len(links)}")
        print(f"- Topics: {len(topic_analysis['topics'])}")
    
    def run_optimized_pipeline(self, data_source: str):
        """Run the complete optimized pipeline."""
        print("=" * 60)
        print("OPTIMIZED IETF WEAVERS PIPELINE")
        print("=" * 60)
        print(f"Processing: {data_source}")
        print(f"Configuration: {self.config}")
        print()
        
        total_start_time = datetime.now()
        
        try:
            # Step 1: Load and sample data
            email_data = self.load_and_sample_data(data_source)
            if not email_data:
                print("No data loaded. Exiting.")
                return
            
            # Step 2: Build graph efficiently
            self.graph = self.build_efficient_graph(email_data)
            
            # Step 3: Calculate metrics
            self.metrics_data = self.calculate_fast_metrics(self.graph)
            
            # Step 4: Topic analysis
            self.topic_analysis = self.run_fast_topic_analysis(email_data)
            
            # Step 5: Export visualization data
            self.export_visualization_data(self.graph, self.topic_analysis)
            
            # Final statistics
            total_time = (datetime.now() - total_start_time).total_seconds()
            self.processing_stats['total_processing_time'] = total_time
            
            print("\n" + "=" * 60)
            print("PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"Total processing time: {total_time:.1f} seconds")
            print(f"Original dataset: {self.processing_stats['total_emails']:,} emails")
            print(f"Processed sample: {self.processing_stats['sampled_emails']:,} emails ({self.processing_stats['sampled_emails']/self.processing_stats['total_emails']*100:.1f}%)")
            print(f"Network: {self.processing_stats['nodes']} nodes, {self.processing_stats['edges']} edges")
            print(f"Processing rate: {self.processing_stats['sampled_emails']/total_time:.0f} emails/second")
            print(f"\nVisualization files generated in: {self.config['output_dir']}/")
            print("- data.json (main visualization data)")
            print("- individual_features.csv (participant analysis)")
            print("- topic_analysis.json (topic modeling results)")
            
        except Exception as e:
            print(f"Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Optimized IETF Weavers Pipeline")
    parser.add_argument("data_source", help="Path to JSON data file")
    parser.add_argument("--sample-rate", type=float, default=0.1, 
                       help="Fraction of data to sample (default: 0.1)")
    parser.add_argument("--min-sample", type=int, default=5000,
                       help="Minimum sample size (default: 5000)")
    parser.add_argument("--max-sample", type=int, default=50000,
                       help="Maximum sample size (default: 50000)")
    parser.add_argument("--n-topics", type=int, default=20,
                       help="Number of topics (default: 20)")
    parser.add_argument("--min-emails", type=int, default=3,
                       help="Minimum emails per person (default: 3)")
    parser.add_argument("--output-dir", default="visualisation",
                       help="Output directory (default: visualisation)")
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        'sample_rate': args.sample_rate,
        'min_sample_size': args.min_sample,
        'max_sample_size': args.max_sample,
        'n_topics': args.n_topics,
        'min_emails_per_person': args.min_emails,
        'output_dir': args.output_dir,
        'batch_size': 1000,
        'export_individual_features': True
    }
    
    # Initialize and run processor
    processor = OptimizedIETFProcessor(config)
    processor.run_optimized_pipeline(args.data_source)


if __name__ == "__main__":
    main()
