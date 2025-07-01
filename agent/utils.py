"""
Email parsing, NER, and cleaning utilities for IETF mailing list analysis.
Based on the methodology from IETF Email Network Analysis project.
"""

import re
import json
from typing import Dict, List, Set, Tuple, Optional
from email.utils import parseaddr
from datetime import datetime
import hashlib


class EmailParser:
    """Parse and normalize email addresses and messages."""
    
    def __init__(self):
        # Automated email patterns from methodology
        self.automated_patterns = [
            r'.*-archive@.*',
            r'.*-bounces@.*',
            r'noreply@.*',
            r'notification@.*',
            r'trac\+.*@tools\.ietf\.org',
            r'.*-secretary@.*',
            r'.*-secretariat@.*',
        ]
        
        # Role-based email patterns
        self.role_patterns = [
            r'.*-chairs@ietf\.org',
            r'.*-ads@ietf\.org',
            r'chair@ietf\.org',
            r'ietf-.*@ietf\.org',
        ]
        
        self.compiled_automated = [re.compile(pattern, re.IGNORECASE) for pattern in self.automated_patterns]
        self.compiled_role = [re.compile(pattern, re.IGNORECASE) for pattern in self.role_patterns]
    
    def normalize_email(self, email: str) -> str:
        """
        Normalize email address following methodology standards.
        
        Process:
        1. Convert to lowercase
        2. Handle obfuscated addresses
        3. Remove display name artifacts
        4. Validate format
        """
        if not email:
            return ""
        
        # Extract email from display name format
        _, addr = parseaddr(email)
        if not addr:
            addr = email
        
        # Convert to lowercase
        addr = addr.lower().strip()
        
        # Handle obfuscated addresses
        addr = re.sub(r'\s+at\s+', '@', addr)
        addr = re.sub(r'\s+dot\s+', '.', addr)
        
        # Remove extra whitespace and brackets
        addr = re.sub(r'[<>]', '', addr)
        addr = re.sub(r'\s+', '', addr)
        
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', addr):
            return ""
        
        return addr
    
    def classify_email_type(self, email: str) -> str:
        """
        Classify email into categories based on methodology.
        
        Returns: 'automated', 'role-based', or 'individual'
        """
        normalized = self.normalize_email(email)
        
        # Check automated patterns
        for pattern in self.compiled_automated:
            if pattern.match(normalized):
                return 'automated'
        
        # Check role-based patterns
        for pattern in self.compiled_role:
            if pattern.match(normalized):
                return 'role-based'
        
        return 'individual'
    
    def extract_message_headers(self, message) -> Dict:
        """Extract key headers from email message."""
        headers = {}
        
        try:
            headers['from'] = self.normalize_email(message.get('From', ''))
            headers['to'] = [self.normalize_email(addr) for addr in message.get_all('To', [])]
            headers['cc'] = [self.normalize_email(addr) for addr in message.get_all('Cc', [])]
            headers['date'] = message.get('Date', '')
            headers['message_id'] = message.get('Message-ID', '')
            headers['in_reply_to'] = message.get('In-Reply-To', '')
            headers['references'] = message.get('References', '')
            headers['subject'] = message.get('Subject', '')
        except Exception as e:
            print(f"Error extracting headers: {e}")
        
        return headers


class PersonIdentityResolver:
    """
    Multi-step identity linking process from methodology:
    1. URI-based matching (official datatracker records)
    2. Name-based matching across different sources
    3. Email-based clustering for same individuals
    4. Cross-validation with affiliation data
    """
    
    def __init__(self):
        self.email_to_person = {}
        self.person_to_emails = {}
        self.person_to_name = {}
        self.person_to_datatracker = {}
        self.person_counter = 0
    
    def generate_person_id(self, email: str) -> str:
        """Generate unique person ID."""
        self.person_counter += 1
        return f"person_{self.person_counter:06d}"
    
    def add_email_mapping(self, email: str, name: str = "", datatracker_uri: str = "") -> str:
        """Add email to person mapping."""
        email = EmailParser().normalize_email(email)
        if not email:
            return ""
        
        # Check if email already mapped
        if email in self.email_to_person:
            person_id = self.email_to_person[email]
        else:
            person_id = self.generate_person_id(email)
            self.email_to_person[email] = person_id
            self.person_to_emails[person_id] = []
        
        # Add email to person's email list
        if email not in self.person_to_emails[person_id]:
            self.person_to_emails[person_id].append(email)
        
        # Update name if provided
        if name:
            self.person_to_name[person_id] = name
        
        # Update datatracker URI if provided
        if datatracker_uri:
            self.person_to_datatracker[person_id] = datatracker_uri
        
        return person_id
    
    def merge_persons(self, person_id1: str, person_id2: str) -> str:
        """Merge two person identities."""
        if person_id1 not in self.person_to_emails or person_id2 not in self.person_to_emails:
            return person_id1
        
        # Merge emails
        emails1 = self.person_to_emails[person_id1]
        emails2 = self.person_to_emails[person_id2]
        
        # Update all email mappings to point to person_id1
        for email in emails2:
            self.email_to_person[email] = person_id1
        
        # Merge email lists
        self.person_to_emails[person_id1] = list(set(emails1 + emails2))
        
        # Merge names (keep first non-empty)
        if person_id2 in self.person_to_name and person_id1 not in self.person_to_name:
            self.person_to_name[person_id1] = self.person_to_name[person_id2]
        
        # Merge datatracker URIs (keep first non-empty)
        if person_id2 in self.person_to_datatracker and person_id1 not in self.person_to_datatracker:
            self.person_to_datatracker[person_id1] = self.person_to_datatracker[person_id2]
        
        # Remove person_id2
        del self.person_to_emails[person_id2]
        if person_id2 in self.person_to_name:
            del self.person_to_name[person_id2]
        if person_id2 in self.person_to_datatracker:
            del self.person_to_datatracker[person_id2]
        
        return person_id1
    
    def export_mappings(self, output_dir: str):
        """Export mappings to JSON files as specified in methodology."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export email to person ID mapping
        with open(os.path.join(output_dir, 'emailID_pid_dict.json'), 'w') as f:
            json.dump(self.email_to_person, f, indent=2)
        
        # Export person to email list mapping
        with open(os.path.join(output_dir, 'pid_emailID_dict.json'), 'w') as f:
            json.dump(self.person_to_emails, f, indent=2)
        
        # Export person ID to names mapping
        with open(os.path.join(output_dir, 'pid_name_dict.json'), 'w') as f:
            json.dump(self.person_to_name, f, indent=2)
        
        # Export person to datatracker URI mapping
        with open(os.path.join(output_dir, 'pid_datatracker_dict.json'), 'w') as f:
            json.dump(self.person_to_datatracker, f, indent=2)


class ThreadAnalyzer:
    """
    Email thread reconstruction algorithm from methodology:
    1. Parse Message-ID and In-Reply-To headers
    2. Build directed graph of message relationships
    3. Identify thread roots and conversation trees
    4. Handle missing/broken thread references
    5. Extract interaction patterns from thread structure
    """
    
    def __init__(self):
        self.messages = {}
        self.threads = {}
    
    def add_message(self, message_id: str, in_reply_to: str, from_email: str, 
                   date: str, subject: str):
        """Add message to thread analysis."""
        self.messages[message_id] = {
            'in_reply_to': in_reply_to,
            'from': from_email,
            'date': date,
            'subject': subject,
            'replies': []
        }
    
    def build_thread_structure(self):
        """Build thread structure from message relationships."""
        # Find reply relationships
        for msg_id, msg_data in self.messages.items():
            reply_to = msg_data['in_reply_to']
            if reply_to and reply_to in self.messages:
                self.messages[reply_to]['replies'].append(msg_id)
        
        # Identify thread roots (messages with no parent)
        thread_roots = []
        for msg_id, msg_data in self.messages.items():
            reply_to = msg_data['in_reply_to']
            if not reply_to or reply_to not in self.messages:
                thread_roots.append(msg_id)
        
        return thread_roots
    
    def extract_interactions(self) -> List[Tuple[str, str]]:
        """Extract person-to-person interactions from threads."""
        interactions = []
        
        for msg_id, msg_data in self.messages.items():
            from_email = msg_data['from']
            
            # Direct replies
            for reply_id in msg_data['replies']:
                reply_data = self.messages[reply_id]
                to_email = reply_data['from']
                if from_email != to_email:
                    interactions.append((from_email, to_email))
        
        return interactions


def clean_text(text: str) -> str:
    """Clean text content for analysis."""
    if not text:
        return ""
    
    # Remove email signatures
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip common signature markers
        if line.strip().startswith(('--', '___', '***')):
            break
        # Skip quoted text
        if line.strip().startswith('>'):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()


def filter_automated_emails(emails: List[str]) -> Tuple[List[str], List[str]]:
    """Separate automated from individual emails."""
    parser = EmailParser()
    individual = []
    automated = []
    
    for email in emails:
        if parser.classify_email_type(email) == 'individual':
            individual.append(email)
        else:
            automated.append(email)
    
    return individual, automated