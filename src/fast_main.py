"""
Fast and simple IETF data processor for large datasets.
Optimized for performance over feature completeness.
"""

import os
import sys
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse
from collections import defaultdict, Counter

# Add project root and agent directory to path  
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agent'))

try:
    import networkx as nx
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    import pandas as pd
    DEPENDENCIES_AVAILABLE = True
    print("All dependencies loaded successfully")
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: Missing dependencies - {e}")

from agent.utils import PersonIdentityResolver, EmailParser


class FastIETFProcessor:
    """Fast processor for large IETF datasets with intelligent sampling."""
    
    def __init__(self):
        self.person_resolver = PersonIdentityResolver()
        self.email_parser = EmailParser()
        
        # Configuration
        self.sample_rate = 0.05  # Process 5% of data
        self.min_emails_per_person = 2
        self.n_topics = 15
        self.batch_size = 500
        
        # Results
        self.stats = {}
    
    def load_and_sample(self, data_file: str) -> List[Dict]:
        """Load data with intelligent sampling."""
        print(f"Loading data from: {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        print(f"Loaded {len(all_data):,} emails")
        
        # Quick analysis
        print("Analyzing data distribution...")
        individuals = []
        for email in all_data[:min(10000, len(all_data))]:
            if self.email_parser.classify_email_type(email.get('from', '')) == 'individual':
                individuals.append(email)
        
        # Calculate sample size
        total_individuals = int(len(individuals) * (len(all_data) / min(10000, len(all_data))))
        sample_size = max(1000, int(total_individuals * self.sample_rate))
        sample_size = min(sample_size, 20000)  # Cap at 20k for performance
        
        print(f"Estimated {total_individuals:,} individual emails, sampling {sample_size:,}")
        
        # Filter to individuals only and sample
        all_individuals = [email for email in all_data 
                          if self.email_parser.classify_email_type(email.get('from', '')) == 'individual']
        
        if len(all_individuals) > sample_size:
            sampled = random.sample(all_individuals, sample_size)
        else:
            sampled = all_individuals
        
        print(f"Final sample: {len(sampled):,} emails")
        
        self.stats['total_emails'] = len(all_data)
        self.stats['individual_emails'] = len(all_individuals)
        self.stats['sampled_emails'] = len(sampled)
        
        return sampled
    
    def build_graph(self, emails: List[Dict]):
        """Build social network graph."""
        if not DEPENDENCIES_AVAILABLE:
            print("NetworkX not available, skipping graph")
            return None, {}
            
        print("Building social graph...")
        graph = nx.DiGraph()
        
        # Track people and interactions
        people = {}  # person_id -> {emails: int, lists: set, first: date, last: date}
        replies = []  # (from_person, to_person) pairs
        message_to_person = {}  # message_id -> person_id
        
        # Process emails
        for i, email in enumerate(emails):
            if i % 1000 == 0:
                print(f"Processed {i:,}/{len(emails):,} emails")
            
            from_email = email.get('from', '')
            message_id = email.get('message_id', '')
            in_reply_to = email.get('in_reply_to', '')
            mailing_list = email.get('mailing_list', email.get('list_name', ''))
            date_str = email.get('date', '')
            
            # Handle in_reply_to as list or string
            if isinstance(in_reply_to, list):
                in_reply_to = in_reply_to[0] if in_reply_to else ''
            elif not isinstance(in_reply_to, str):
                in_reply_to = str(in_reply_to) if in_reply_to else ''
            
            # Map to person
            person_id = self.person_resolver.add_email_mapping(from_email)
            if not person_id:
                continue
            
            # Track message
            if message_id:
                message_to_person[message_id] = person_id
            
            # Initialize person data
            if person_id not in people:
                people[person_id] = {
                    'emails': 0,
                    'lists': set(),
                    'first': None,
                    'last': None
                }
            
            # Update person data
            people[person_id]['emails'] += 1
            if mailing_list:
                people[person_id]['lists'].add(mailing_list)
            
            # Track dates
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if people[person_id]['first'] is None:
                    people[person_id]['first'] = date_obj
                    people[person_id]['last'] = date_obj
                else:
                    if date_obj < people[person_id]['first']:
                        people[person_id]['first'] = date_obj
                    if date_obj > people[person_id]['last']:
                        people[person_id]['last'] = date_obj
            except:
                pass
            
            # Track reply
            if in_reply_to and in_reply_to in message_to_person:
                original_person = message_to_person[in_reply_to]
                if original_person != person_id:
                    replies.append((person_id, original_person))
        
        # Filter active people
        active_people = {pid: data for pid, data in people.items() 
                        if data['emails'] >= self.min_emails_per_person}
        
        print(f"Found {len(active_people)} active participants")
        
        # Add nodes
        for person_id, data in active_people.items():
            duration = 0
            if data['first'] and data['last']:
                duration = (data['last'] - data['first']).days
            
            graph.add_node(person_id,
                          email_count=data['emails'],
                          mailing_lists_count=len(data['lists']),
                          activity_duration_days=duration)
        
        # Add edges
        reply_weights = Counter()
        for replier, original in replies:
            if replier in active_people and original in active_people:
                reply_weights[(replier, original)] += 1
        
        for (replier, original), weight in reply_weights.items():
            graph.add_edge(replier, original, weight=weight)
        
        print(f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
        # Calculate metrics
        metrics = {}
        if graph.number_of_nodes() > 0:
            print("Calculating centrality...")
            metrics['degree_centrality'] = nx.degree_centrality(graph)
            
            if graph.number_of_nodes() < 1000:
                metrics['betweenness_centrality'] = nx.betweenness_centrality(graph)
            else:
                # Approximate for large graphs
                metrics['betweenness_centrality'] = nx.betweenness_centrality(graph, k=100)
            
            # Community detection
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(graph.to_undirected())
                metrics['community'] = partition
            except ImportError:
                # Simple fallback
                partition = {node: 0 for node in graph.nodes()}
                metrics['community'] = partition
        
        # Update node attributes
        for node in graph.nodes():
            graph.nodes[node]['degree_centrality'] = metrics.get('degree_centrality', {}).get(node, 0)
            graph.nodes[node]['betweenness_centrality'] = metrics.get('betweenness_centrality', {}).get(node, 0)
            graph.nodes[node]['community'] = metrics.get('community', {}).get(node, 0)
        
        return graph, metrics
    
    def analyze_topics(self, emails: List[Dict], active_people: set):
        """Fast topic analysis using LDA."""
        if not DEPENDENCIES_AVAILABLE:
            print("Scikit-learn not available, skipping topics")
            return {'topics': [], 'person_topics': {}}
        
        print("Analyzing topics...")
        
        # Group emails by person
        person_texts = defaultdict(list)
        for email in emails:
            from_email = email.get('from', '')
            person_id = self.person_resolver.email_to_person.get(from_email)
            
            if person_id in active_people:
                subject = email.get('subject', '')
                content = email.get('content', '')
                text = f"{subject} {content}".strip()
                if text:
                    person_texts[person_id].append(text)
        
        # Create documents
        documents = []
        person_order = []
        for person_id, texts in person_texts.items():
            if len(texts) >= 2:  # Minimum texts per person
                combined = ' '.join(texts)
                documents.append(combined)
                person_order.append(person_id)
        
        if len(documents) < 5:
            print("Not enough documents for topic analysis")
            return {'topics': [], 'person_topics': {}}
        
        print(f"Processing {len(documents)} person documents")
        
        # Vectorize
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        
        doc_matrix = vectorizer.fit_transform(documents)
        features = vectorizer.get_feature_names_out()
        
        # LDA
        n_topics = min(self.n_topics, len(documents) // 2)
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, max_iter=5)
        lda.fit(doc_matrix)
        doc_topic_dist = lda.transform(doc_matrix)
        
        # Extract topics
        topics = []
        for i in range(n_topics):
            top_words_idx = lda.components_[i].argsort()[-8:][::-1]
            words = [features[idx] for idx in top_words_idx]
            topics.append({
                'id': i,
                'words': words,
                'top_participants': []
            })
        
        # Assign people to topics
        person_topics = {}
        for i, person_id in enumerate(person_order):
            dominant_topic = doc_topic_dist[i].argmax()
            person_topics[person_id] = int(dominant_topic)
        
        print(f"Found {len(topics)} topics")
        return {'topics': topics, 'person_topics': person_topics}
    
    def export_data(self, graph, topic_analysis):
        """Export visualization data."""
        print("Exporting visualization data...")
        
        # Prepare nodes
        nodes = []
        if graph:
            for node_id in graph.nodes():
                node_data = dict(graph.nodes[node_id])
                node_data['id'] = node_id
                
                # Add topic
                if node_id in topic_analysis['person_topics']:
                    node_data['dominant_topic'] = topic_analysis['person_topics'][node_id]
                
                nodes.append(node_data)
        
        # Prepare links
        links = []
        if graph:
            for source, target in graph.edges():
                edge_data = dict(graph[source][target])
                edge_data['source'] = source
                edge_data['target'] = target
                links.append(edge_data)
        
        # Create visualization data
        viz_data = {
            'nodes': nodes,
            'links': links,
            'topics': topic_analysis['topics'],
            'metadata': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'total_topics': len(topic_analysis['topics']),
                'stats': self.stats,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        # Export files
        os.makedirs('visualisation', exist_ok=True)
        
        # Main data
        with open('visualisation/data.json', 'w') as f:
            json.dump(viz_data, f, indent=2)
        
        # Features CSV
        if nodes:
            features = []
            for node in nodes:
                features.append({
                    'person_id': node['id'],
                    'email_count': node.get('email_count', 0),
                    'degree_centrality': node.get('degree_centrality', 0),
                    'betweenness_centrality': node.get('betweenness_centrality', 0),
                    'community': node.get('community', 0),
                    'mailing_lists_count': node.get('mailing_lists_count', 0),
                    'activity_duration_days': node.get('activity_duration_days', 0),
                    'dominant_topic': node.get('dominant_topic', -1)
                })
            
            df = pd.DataFrame(features)
            df.to_csv('visualisation/individual_features.csv', index=False)
        
        # Topics
        with open('visualisation/topic_analysis.json', 'w') as f:
            json.dump(topic_analysis, f, indent=2)
        
        print("Export completed!")
        return viz_data
    
    def run(self, data_file: str):
        """Run the complete fast processing pipeline."""
        print("=" * 50)
        print("FAST IETF PROCESSOR")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # Load and sample data
            emails = self.load_and_sample(data_file)
            
            # Build graph
            graph, metrics = self.build_graph(emails)
            
            # Get active people
            if graph:
                active_people = set(graph.nodes())
            else:
                active_people = set()
            
            # Topic analysis
            topic_analysis = self.analyze_topics(emails, active_people)
            
            # Export
            viz_data = self.export_data(graph, topic_analysis)
            
            # Summary
            total_time = (datetime.now() - start_time).total_seconds()
            
            print("\n" + "=" * 50)
            print("PROCESSING COMPLETED!")
            print("=" * 50)
            print(f"Total time: {total_time:.1f} seconds")
            print(f"Original emails: {self.stats.get('total_emails', 0):,}")
            print(f"Processed emails: {self.stats.get('sampled_emails', 0):,}")
            print(f"Network nodes: {len(viz_data['nodes'])}")
            print(f"Network edges: {len(viz_data['links'])}")
            print(f"Topics found: {len(viz_data['topics'])}")
            print(f"Processing rate: {self.stats.get('sampled_emails', 0)/total_time:.0f} emails/sec")
            print("\nFiles generated:")
            print("- visualisation/data.json")
            print("- visualisation/individual_features.csv")  
            print("- visualisation/topic_analysis.json")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Fast IETF data processor")
    parser.add_argument("data_file", help="Path to IETF JSON data file")
    parser.add_argument("--sample-rate", type=float, default=0.05, help="Sample rate (default: 0.05)")
    parser.add_argument("--min-emails", type=int, default=2, help="Min emails per person (default: 2)")
    
    args = parser.parse_args()
    
    processor = FastIETFProcessor()
    processor.sample_rate = args.sample_rate
    processor.min_emails_per_person = args.min_emails
    
    processor.run(args.data_file)


if __name__ == "__main__":
    main()
