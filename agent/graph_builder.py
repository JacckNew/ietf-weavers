"""
Social graph builder for IETF mailing lists.
Builds sender-replier social graph based on email thread analysis.
"""

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: NetworkX not available. Please install: pip install networkx")

from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict, Counter
from datetime import datetime
import json

try:
    from .utils import EmailParser, PersonIdentityResolver, ThreadAnalyzer
except ImportError:
    from utils import EmailParser, PersonIdentityResolver, ThreadAnalyzer


class SocialGraphBuilder:
    """
    Builds directed social graph from email interactions.
    
    Based on methodology:
    - Nodes: unique participants
    - Edges: inferred reply relationships from threads
    - Multi-layer network construction
    """
    
    def __init__(self):
        if not NETWORKX_AVAILABLE:
            print("Warning: NetworkX not available. Graph functionality will be limited.")
            self.graph = None
        else:
            self.graph = nx.DiGraph()
        
        self.person_resolver = PersonIdentityResolver()
        self.email_parser = EmailParser()
        self.thread_analyzer = ThreadAnalyzer()
        
        # Track different types of interactions
        self.email_exchanges = defaultdict(int)  # Direct email exchanges
        self.reply_relationships = defaultdict(int)  # Reply relationships
        self.thread_participation = defaultdict(set)  # Shared thread participation
        self.mailing_list_participation = defaultdict(set)  # Shared mailing lists
        
        # Temporal tracking
        self.person_first_email = {}
        self.person_last_email = {}
        self.person_email_count = defaultdict(int)
        self.person_mailing_lists = defaultdict(set)
    
    def add_email(self, message_data: Dict, mailing_list: str = ""):
        """
        Add email to graph construction.
        
        Args:
            message_data: Dictionary with email headers and content
            mailing_list: Name of the mailing list
        """
        from_email = message_data.get('from', '')
        message_id = message_data.get('message_id', '')
        in_reply_to = message_data.get('in_reply_to', '')
        date_str = message_data.get('date', '')
        subject = message_data.get('subject', '')
        
        # Skip automated emails
        if self.email_parser.classify_email_type(from_email) != 'individual':
            return
        
        # Add person mapping
        person_id = self.person_resolver.add_email_mapping(from_email)
        if not person_id:
            return
        
        # Add to thread analyzer
        self.thread_analyzer.add_message(message_id, in_reply_to, from_email, date_str, subject)
        
        # Track temporal activity
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if person_id not in self.person_first_email:
                self.person_first_email[person_id] = date_obj
            else:
                self.person_first_email[person_id] = min(self.person_first_email[person_id], date_obj)
            
            if person_id not in self.person_last_email:
                self.person_last_email[person_id] = date_obj
            else:
                self.person_last_email[person_id] = max(self.person_last_email[person_id], date_obj)
        except:
            pass
        
        # Track participation
        self.person_email_count[person_id] += 1
        if mailing_list:
            self.person_mailing_lists[person_id].add(mailing_list)
        
        # Add node to graph
        if NETWORKX_AVAILABLE and self.graph is not None:
            if not self.graph.has_node(person_id):
                self.graph.add_node(person_id, email=from_email)
        elif person_id not in getattr(self, '_nodes', set()):
            # Fallback: just track nodes in a set if NetworkX not available
            if not hasattr(self, '_nodes'):
                self._nodes = set()
                self._edges = []
            self._nodes.add(person_id)
    
    def build_interaction_graph(self):
        """
        Build interaction graph from thread analysis.
        Extract person-to-person interactions from email threads.
        """
        # Build thread structure
        self.thread_analyzer.build_thread_structure()
        
        # Extract interactions
        interactions = self.thread_analyzer.extract_interactions()
        
        for from_email, to_email in interactions:
            from_person = self.person_resolver.email_to_person.get(from_email)
            to_person = self.person_resolver.email_to_person.get(to_email)
            
            if from_person and to_person and from_person != to_person:
                # Add reply relationship
                self.reply_relationships[(from_person, to_person)] += 1
                
                # Add edge to graph
                if NETWORKX_AVAILABLE and self.graph is not None:
                    if self.graph.has_edge(from_person, to_person):
                        self.graph[from_person][to_person]['weight'] += 1
                    else:
                        self.graph.add_edge(from_person, to_person, weight=1, interaction_type='reply')
                else:
                    # Fallback: just track edges in a list
                    if not hasattr(self, '_edges'):
                        self._edges = []
                    self._edges.append((from_person, to_person, 1, 'reply'))
    
    def add_co_participation_edges(self):
        """Add edges based on shared mailing list participation."""
        persons = list(self.person_mailing_lists.keys())
        
        for i, person1 in enumerate(persons):
            for person2 in persons[i+1:]:
                # Check for shared mailing lists
                shared_lists = self.person_mailing_lists[person1] & self.person_mailing_lists[person2]
                
                if shared_lists:
                    if NETWORKX_AVAILABLE and self.graph is not None:
                        # Add undirected co-participation edge
                        if not self.graph.has_edge(person1, person2):
                            self.graph.add_edge(person1, person2, weight=0, interaction_type='co_participation')
                        if not self.graph.has_edge(person2, person1):
                            self.graph.add_edge(person2, person1, weight=0, interaction_type='co_participation')
                        
                        # Update edge attributes
                        self.graph[person1][person2]['shared_lists'] = len(shared_lists)
                        self.graph[person2][person1]['shared_lists'] = len(shared_lists)
                    else:
                        # Fallback: track co-participation edges
                        if not hasattr(self, '_edges'):
                            self._edges = []
                        self._edges.append((person1, person2, 0, 'co_participation'))
                        self._edges.append((person2, person1, 0, 'co_participation'))
    
    def calculate_node_attributes(self):
        """Calculate node-level attributes for social network analysis."""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return
        
        for person_id in self.graph.nodes():
            attributes = {}
            
            # Communication volume
            attributes['email_count'] = self.person_email_count.get(person_id, 0)
            
            # Temporal activity
            if person_id in self.person_first_email:
                attributes['first_email'] = self.person_first_email[person_id].isoformat()
            if person_id in self.person_last_email:
                attributes['last_email'] = self.person_last_email[person_id].isoformat()
            
            # Activity duration
            if person_id in self.person_first_email and person_id in self.person_last_email:
                duration = self.person_last_email[person_id] - self.person_first_email[person_id]
                attributes['activity_duration_days'] = duration.days
            
            # Collaboration breadth
            attributes['mailing_lists_count'] = len(self.person_mailing_lists.get(person_id, set()))
            attributes['mailing_lists'] = list(self.person_mailing_lists.get(person_id, set()))
            
            # Update node attributes
            if NETWORKX_AVAILABLE and self.graph is not None:
                import networkx as nx
                nx.set_node_attributes(self.graph, {person_id: attributes})
    
    def get_multilayer_networks(self) -> Dict[str, Any]:
        """
        Return different network layers as specified in methodology:
        - Email exchange networks (who emails whom)
        - Reply networks (who responds to whom)
        - Mailing list co-participation (shared venues)
        """
        networks = {}
        
        if not NETWORKX_AVAILABLE:
            # Return simple dictionaries instead of NetworkX graphs
            networks['reply'] = {
                'edges': [(p1, p2, count) for (p1, p2), count in self.reply_relationships.items()],
                'type': 'directed'
            }
            networks['co_participation'] = {
                'edges': [],
                'type': 'undirected'  
            }
            return networks
        
        # Reply network (directed)
        reply_network = nx.DiGraph()
        for (person1, person2), count in self.reply_relationships.items():
            reply_network.add_edge(person1, person2, weight=count)
        networks['reply'] = reply_network
        
        # Co-participation network (undirected)
        coparticipation_network = nx.Graph()
        persons = list(self.person_mailing_lists.keys())
        
        for i, person1 in enumerate(persons):
            for person2 in persons[i+1:]:
                shared_lists = self.person_mailing_lists[person1] & self.person_mailing_lists[person2]
                if shared_lists:
                    coparticipation_network.add_edge(person1, person2, 
                                                   weight=len(shared_lists),
                                                   shared_lists=list(shared_lists))
        networks['co_participation'] = coparticipation_network
        
        return networks
    
    def export_graph_data(self, output_file: str):
        """Export graph data in format suitable for analysis."""
        # Calculate final attributes
        self.calculate_node_attributes()
        
        # Prepare export data
        export_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_nodes': 0,
                'total_edges': 0,
                'is_directed': True,
                'person_mappings': {
                    'email_to_person': self.person_resolver.email_to_person,
                    'person_to_emails': self.person_resolver.person_to_emails,
                    'person_to_name': self.person_resolver.person_to_name
                }
            }
        }
        
        if NETWORKX_AVAILABLE and self.graph is not None:
            export_data['metadata']['total_nodes'] = self.graph.number_of_nodes()
            export_data['metadata']['total_edges'] = self.graph.number_of_edges()
            
            # Export nodes
            for node_id in self.graph.nodes():
                node_data = {'id': node_id}
                node_data.update(self.graph.nodes[node_id])
                export_data['nodes'].append(node_data)
            
            # Export edges
            for source, target in self.graph.edges():
                edge_data = {
                    'source': source,
                    'target': target
                }
                edge_data.update(self.graph[source][target])
                export_data['edges'].append(edge_data)
        else:
            # Fallback for when NetworkX is not available
            nodes = getattr(self, '_nodes', set())
            edges = getattr(self, '_edges', [])
            
            export_data['metadata']['total_nodes'] = len(nodes)
            export_data['metadata']['total_edges'] = len(edges)
            
            # Export nodes
            for node_id in nodes:
                export_data['nodes'].append({'id': node_id})
            
            # Export edges
            for edge in edges:
                if len(edge) >= 4:
                    source, target, weight, interaction_type = edge[:4]
                    export_data['edges'].append({
                        'source': source,
                        'target': target,
                        'weight': weight,
                        'interaction_type': interaction_type
                    })
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return export_data
    
    def get_graph(self):
        """Return the constructed graph."""
        if NETWORKX_AVAILABLE and self.graph is not None:
            return self.graph
        else:
            # Return a simple graph-like object
            return {
                'nodes': getattr(self, '_nodes', set()),
                'edges': getattr(self, '_edges', []),
                'is_networkx': False
            }
    
    def get_person_resolver(self) -> PersonIdentityResolver:
        """Return the person identity resolver."""
        return self.person_resolver


def load_email_data(file_path: str) -> List[Dict]:
    """Load email data from file (implement based on your data format)."""
    # This is a placeholder - implement based on your actual data format
    # Could be JSON, CSV, or direct mailing list parsing
    with open(file_path, 'r') as f:
        return json.load(f)


def process_mailing_list_archive(archive_path: str, mailing_list_name: str) -> SocialGraphBuilder:
    """Process a mailing list archive and build social graph."""
    builder = SocialGraphBuilder()
    
    # Load email data (implement based on your format)
    email_data = load_email_data(archive_path)
    
    for email in email_data:
        builder.add_email(email, mailing_list_name)
    
    # Build interaction graph
    builder.build_interaction_graph()
    builder.add_co_participation_edges()
    
    return builder