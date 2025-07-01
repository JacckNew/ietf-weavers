"""
Topic modeling using BERTopic for IETF email analysis.
Runs BERTopic to extract discussion themes and participant-topic distributions.
"""

from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json
import numpy as np
from datetime import datetime, timedelta

try:
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer
    from sentence_transformers import SentenceTransformer
    import pandas as pd
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: BERTopic dependencies not available. Please install bertopic, scikit-learn, sentence-transformers, and pandas")


class TopicModeler:
    """
    BERTopic-based topic modeling following methodology:
    - Concatenate each user's emails into one document per user per time window
    - Extract 50-100 topics
    - Calculate participant-topic distributions
    - Calculate topic entropy for each participant
    """
    
    def __init__(self, n_topics: int = 50, time_window_months: int = 6):
        self.n_topics = n_topics
        self.time_window_months = time_window_months
        self.model = None
        self.documents = []
        self.document_metadata = []
        self.topics = None
        self.topic_info = None
        
        if DEPENDENCIES_AVAILABLE:
            # Initialize BERTopic model
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize BERTopic model with custom settings."""
        if not DEPENDENCIES_AVAILABLE:
            return
        
        # Use sentence transformer for embeddings
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Custom vectorizer to handle email-specific vocabulary
        vectorizer_model = CountVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1,  # Minimum document frequency (must be 1 for small datasets)
            max_df=1.0,  # Maximum document frequency (allow all terms)
            max_features=500  # Reduced for small datasets
        )
        
        # Configure UMAP for small datasets
        from umap import UMAP
        umap_model = UMAP(
            n_neighbors=min(3, max(2, len(self.documents) if hasattr(self, 'documents') else 5)),
            n_components=min(2, self.n_topics),
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        # Configure HDBSCAN for small datasets
        from hdbscan import HDBSCAN
        hdbscan_model = HDBSCAN(
            min_cluster_size=2,  # Minimum cluster size for small datasets
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # Initialize BERTopic with small dataset configuration
        self.model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            nr_topics=min(self.n_topics, 5),  # Limit topics for small datasets
            calculate_probabilities=True,
            verbose=True
        )
    
    def prepare_documents(self, email_data: List[Dict], person_resolver) -> List[Dict]:
        """
        Prepare documents for topic modeling.
        
        Concatenate each user's emails into one document per user per time window.
        
        Args:
            email_data: List of email dictionaries
            person_resolver: PersonIdentityResolver instance
        
        Returns:
            List of document dictionaries
        """
        if not DEPENDENCIES_AVAILABLE:
            return []
        
        # Group emails by person and time window
        person_time_emails = defaultdict(lambda: defaultdict(list))
        
        for email in email_data:
            from_email = email.get('from', '')
            content = email.get('content', '')
            date_str = email.get('date', '')
            
            # Skip if no content or automated email
            if not content or not from_email:
                continue
            
            # Get person ID
            person_id = person_resolver.email_to_person.get(from_email)
            if not person_id:
                continue
            
            # Parse date and determine time window
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                time_window = self._get_time_window(date_obj)
            except:
                continue
            
            person_time_emails[person_id][time_window].append({
                'content': content,
                'date': date_obj,
                'email': from_email
            })
        
        # Create documents by concatenating emails per person per time window
        documents = []
        
        for person_id, time_windows in person_time_emails.items():
            for time_window, emails in time_windows.items():
                if len(emails) < 2:  # Skip if too few emails
                    continue
                
                # Concatenate email contents
                combined_content = ' '.join([email['content'] for email in emails])
                
                # Clean the content
                cleaned_content = self._clean_text(combined_content)
                
                if len(cleaned_content.split()) < 50:  # Skip if too short
                    continue
                
                doc_metadata = {
                    'person_id': person_id,
                    'time_window': time_window,
                    'email_count': len(emails),
                    'date_range': {
                        'start': min(email['date'] for email in emails).isoformat(),
                        'end': max(email['date'] for email in emails).isoformat()
                    }
                }
                
                documents.append({
                    'content': cleaned_content,
                    'metadata': doc_metadata
                })
        
        return documents
    
    def _get_time_window(self, date_obj: datetime) -> str:
        """Get time window identifier for a date."""
        # Round to nearest time window
        year = date_obj.year
        month = ((date_obj.month - 1) // self.time_window_months) * self.time_window_months + 1
        return f"{year}-{month:02d}"
    
    def _clean_text(self, text: str) -> str:
        """Clean text for topic modeling."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip quoted text (starts with >)
            if line.startswith('>'):
                continue
            
            # Skip signature lines
            if line.startswith(('--', '___', '***')):
                break
            
            # Skip headers and technical markers
            if line.startswith(('From:', 'To:', 'Subject:', 'Date:', 'Message-ID:')):
                continue
            
            cleaned_lines.append(line)
        
        cleaned_text = ' '.join(cleaned_lines)
        
        # Remove extra whitespace
        cleaned_text = ' '.join(cleaned_text.split())
        
        return cleaned_text
    
    def fit_topic_model(self, documents: List[Dict]) -> Tuple[List[int], List[float]]:
        """
        Fit BERTopic model on documents.
        
        Returns:
            Tuple of (topics, probabilities)
        """
        if not DEPENDENCIES_AVAILABLE or not self.model:
            return [], []
        
        # Check if we have enough documents for topic modeling
        if len(documents) < 3:
            print(f"⚠️  Only {len(documents)} documents available. Topic modeling requires at least 3 documents.")
            print("Skipping topic modeling phase...")
            return [], []
        
        self.documents = documents
        self.document_metadata = [doc['metadata'] for doc in documents]
        
        # Extract text content
        texts = [doc['content'] for doc in documents]
        
        try:
            # Fit the model
            topics, probabilities = self.model.fit_transform(texts)
            
            self.topics = topics
            self.topic_info = self.model.get_topic_info()
            
            return topics, probabilities
        except Exception as e:
            print(f"⚠️  Topic modeling failed with error: {e}")
            print("This often happens with very small datasets. Skipping topic modeling...")
            return [], []
    
    def calculate_participant_topic_distributions(self) -> Dict[str, Dict[int, float]]:
        """
        Calculate participant-topic distributions.
        
        Returns:
            Dictionary mapping person_id to topic distribution
        """
        if not self.topics or not self.document_metadata:
            return {}
        
        # Group documents by person
        person_topics = defaultdict(list)
        person_probs = defaultdict(list)
        
        for i, metadata in enumerate(self.document_metadata):
            person_id = metadata['person_id']
            topic = self.topics[i]
            
            person_topics[person_id].append(topic)
            
            # Get topic probabilities if available
            if hasattr(self.model, 'probabilities_') and self.model.probabilities_ is not None:
                person_probs[person_id].append(self.model.probabilities_[i])
        
        # Calculate distributions
        participant_distributions = {}
        
        for person_id in person_topics:
            topics = person_topics[person_id]
            
            # Count topic occurrences
            topic_counts = defaultdict(int)
            for topic in topics:
                topic_counts[topic] += 1
            
            # Normalize to probabilities
            total_docs = len(topics)
            topic_dist = {topic: count / total_docs for topic, count in topic_counts.items()}
            
            participant_distributions[person_id] = topic_dist
        
        return participant_distributions
    
    def calculate_topic_entropy(self, participant_distributions: Dict[str, Dict[int, float]]) -> Dict[str, float]:
        """
        Calculate topic entropy for each participant.
        Higher entropy = more diverse topic engagement.
        """
        entropies = {}
        
        for person_id, topic_dist in participant_distributions.items():
            if not topic_dist:
                entropies[person_id] = 0.0
                continue
            
            # Calculate Shannon entropy
            probs = list(topic_dist.values())
            entropy = -sum(p * np.log2(p) for p in probs if p > 0)
            entropies[person_id] = entropy
        
        return entropies
    
    def get_topic_keywords(self, top_k: int = 10) -> Dict[int, List[str]]:
        """Get top keywords for each topic."""
        if not self.model or self.topic_info is None or self.topic_info.empty:
            return {}
        
        topic_keywords = {}
        
        for topic_id in self.topic_info['Topic']:
            if topic_id == -1:  # Skip outlier topic
                continue
            
            # Get topic words
            topic_words = self.model.get_topic(topic_id)
            keywords = [word for word, _ in topic_words[:top_k]]
            topic_keywords[topic_id] = keywords
        
        return topic_keywords
    
    def get_top_participants_per_topic(self, participant_distributions: Dict[str, Dict[int, float]], 
                                     top_k: int = 10) -> Dict[int, List[Tuple[str, float]]]:
        """Get top participants for each topic."""
        topic_participants = defaultdict(list)
        
        # Collect all person-topic pairs
        for person_id, topic_dist in participant_distributions.items():
            for topic_id, prob in topic_dist.items():
                topic_participants[topic_id].append((person_id, prob))
        
        # Sort and get top participants per topic
        top_participants = {}
        for topic_id, participants in topic_participants.items():
            sorted_participants = sorted(participants, key=lambda x: x[1], reverse=True)
            top_participants[topic_id] = sorted_participants[:top_k]
        
        return top_participants
    
    def export_topic_analysis(self, output_file: str, person_resolver) -> Dict[str, Any]:
        """Export comprehensive topic analysis results."""
        if not self.model or not self.topics:
            return {}
        
        # Calculate distributions and entropy
        participant_distributions = self.calculate_participant_topic_distributions()
        topic_entropies = self.calculate_topic_entropy(participant_distributions)
        topic_keywords = self.get_topic_keywords()
        top_participants = self.get_top_participants_per_topic(participant_distributions)
        
        # Prepare export data
        export_data = {
            'model_info': {
                'n_topics': self.n_topics,
                'time_window_months': self.time_window_months,
                'n_documents': len(self.documents),
                'topic_count': len(set(self.topics))
            },
            'topics': [],
            'participants': {},
            'document_assignments': []
        }
        
        # Export topic information
        for topic_id, keywords in topic_keywords.items():
            topic_data = {
                'topic_id': topic_id,
                'keywords': keywords,
                'top_participants': [
                    {
                        'person_id': person_id,
                        'probability': prob,
                        'name': person_resolver.person_to_name.get(person_id, ''),
                        'emails': person_resolver.person_to_emails.get(person_id, [])
                    }
                    for person_id, prob in top_participants.get(topic_id, [])
                ]
            }
            export_data['topics'].append(topic_data)
        
        # Export participant information
        for person_id, topic_dist in participant_distributions.items():
            export_data['participants'][person_id] = {
                'topic_distribution': topic_dist,
                'topic_entropy': topic_entropies.get(person_id, 0.0),
                'name': person_resolver.person_to_name.get(person_id, ''),
                'emails': person_resolver.person_to_emails.get(person_id, []),
                'dominant_topics': sorted(topic_dist.items(), key=lambda x: x[1], reverse=True)[:3]
            }
        
        # Export document assignments
        for i, (topic, metadata) in enumerate(zip(self.topics, self.document_metadata)):
            export_data['document_assignments'].append({
                'document_id': i,
                'topic': topic,
                'metadata': metadata
            })
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return export_data


def run_topic_modeling(email_data: List[Dict], person_resolver, 
                      n_topics: int = 50, time_window_months: int = 6) -> TopicModeler:
    """Run complete topic modeling pipeline."""
    modeler = TopicModeler(n_topics=n_topics, time_window_months=time_window_months)
    
    # Prepare documents
    documents = modeler.prepare_documents(email_data, person_resolver)
    print(f"Prepared {len(documents)} documents for topic modeling")
    
    if documents:
        # Fit model
        topics, probabilities = modeler.fit_topic_model(documents)
        print(f"Identified {len(set(topics))} topics")
    
    return modeler