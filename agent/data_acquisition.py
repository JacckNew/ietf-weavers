"""
IETF Data Acquisition Module using glasgow-ipl/ietfdata library
===============================================================

This module integrates the ietfdata library to fetch real IETF Datatracker and
mail archive data, transforming them into the normalized format expected by the
IETF Weavers pipeline.

Key Features:
- Fetch IETF mailing list data using MailArchive3
- Fetch IETF Datatracker metadata using DataTracker
- Transform raw data into pipeline-compatible JSON format
- Support both live and offline/cached data access
- Handle multiple mailing lists and time ranges
"""

import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Iterator, TYPE_CHECKING
from email.headerregistry import Address
import email
import email.utils
from email.message import EmailMessage

if TYPE_CHECKING:
    from ietfdata.datatracker import DataTracker
    from ietfdata.mailarchive3 import MailArchive

try:
    from ietfdata.datatracker import DataTracker
    from ietfdata.mailarchive3 import MailArchive
    IETFDATA_AVAILABLE = True
except ImportError:
    print("Warning: ietfdata library not available. Install with: pip install ietfdata")
    IETFDATA_AVAILABLE = False
    DataTracker = None  # type: ignore
    MailArchive = None  # type: ignore


class IETFDataAcquisition:
    """
    IETF data acquisition using the glasgow-ipl/ietfdata library.
    
    This class provides methods to:
    1. Fetch IETF mailing list archives
    2. Fetch IETF Datatracker metadata 
    3. Transform data into pipeline format
    4. Cache data locally for repeated analysis
    """
    
    def __init__(self, 
                 cache_file: str = "ietfdata.sqlite",
                 use_cache: bool = True,
                 log_level: str = "INFO"):
        """
        Initialize IETF data acquisition.
        
        Args:
            cache_file: SQLite cache file for ietfdata
            use_cache: Whether to use cached data or live queries
            log_level: Logging level
        """
        if not IETFDATA_AVAILABLE:
            raise ImportError("ietfdata library is required. Install with: pip install ietfdata")
        
        self.cache_file = cache_file
        self.use_cache = use_cache
        self.log_level = log_level
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        self.logger = logging.getLogger(__name__)
        
        # Initialize ietfdata components
        self._init_datatracker()
        self._init_mailarchive()
    
    def _init_datatracker(self):
        """Initialize DataTracker with appropriate backend."""
        if not IETFDATA_AVAILABLE or DataTracker is None:
            self.logger.error("DataTracker not available - ietfdata library not installed")
            self.datatracker = None
            return
            
        try:
            if self.use_cache:
                self.logger.info(f"Initializing DataTracker with cache: {self.cache_file}")
                # Use cache directory approach for new API
                cache_dir = os.path.dirname(self.cache_file) if self.cache_file else '.'
                self.datatracker = DataTracker(cache_dir=cache_dir)
            else:
                self.logger.info("Initializing DataTracker with live backend")
                self.datatracker = DataTracker(cache_dir=None)
        except Exception as e:
            self.logger.error(f"Failed to initialize DataTracker: {e}")
            self.datatracker = None
    
    def _init_mailarchive(self):
        """Initialize MailArchive3 with SQLite backend."""
        if not IETFDATA_AVAILABLE or MailArchive is None:
            self.logger.error("MailArchive not available - ietfdata library not installed")
            self.mailarchive = None
            return
            
        try:
            self.logger.info(f"Initializing MailArchive with cache: {self.cache_file}")
            self.mailarchive = MailArchive(sqlite_file=self.cache_file)
        except Exception as e:
            self.logger.error(f"Failed to initialize MailArchive: {e}")
            self.mailarchive = None
    
    def get_available_mailing_lists(self) -> List[str]:
        """
        Get list of available IETF mailing lists.
        
        Returns:
            List of mailing list names
        """
        if not self.mailarchive:
            self.logger.error("MailArchive not initialized")
            return []
        
        try:
            # Update mailing list names from IETF server
            self.mailarchive.update_mailing_list_names()
            
            # Get list of available mailing lists
            mailing_lists = list(self.mailarchive.mailing_list_names())
            self.logger.info(f"Found {len(mailing_lists)} mailing lists")
            return sorted(mailing_lists)
        
        except Exception as e:
            self.logger.error(f"Error getting mailing lists: {e}")
            return []
    
    def update_mailing_list_data(self, 
                                 mailing_list_names: List[str],
                                 force_update: bool = False) -> bool:
        """
        Update/download mailing list data from IETF servers.
        
        Args:
            mailing_list_names: List of mailing list names to update
            force_update: Whether to force update even if data exists
            
        Returns:
            True if successful, False otherwise
        """
        if not self.mailarchive:
            self.logger.error("MailArchive not initialized")
            return False
        
        try:
            for list_name in mailing_list_names:
                self.logger.info(f"Updating mailing list: {list_name}")
                self.mailarchive.update_mailing_list(list_name)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating mailing list data: {e}")
            return False
    
    def fetch_mailing_list_messages(self,
                                    mailing_list_names: List[str],
                                    start_date: str = "2020-01-01T00:00:00",
                                    end_date: str = "2024-12-31T23:59:59",
                                    max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch messages from specified IETF mailing lists.
        
        Args:
            mailing_list_names: List of mailing list names
            start_date: Start date in ISO format
            end_date: End date in ISO format
            max_messages: Maximum number of messages to fetch (None for all)
            
        Returns:
            List of normalized email dictionaries
        """
        if not self.mailarchive:
            self.logger.error("MailArchive not initialized")
            return []
        
        all_messages = []
        
        try:
            for list_name in mailing_list_names:
                self.logger.info(f"Fetching messages from {list_name}")
                
                # Get mailing list object first
                mailing_list = self.mailarchive.mailing_list(list_name)
                if not mailing_list:
                    self.logger.warning(f"No mailing list found for {list_name}")
                    continue
                
                # Get messages from the mailing list
                messages_iter = mailing_list.messages()
                
                # Handle case where messages iterator is None
                if messages_iter is None:
                    self.logger.warning(f"No messages iterator for {list_name}")
                    continue
                
                messages = list(messages_iter)
                
                self.logger.info(f"Found {len(messages)} messages in {list_name}")
                
                # Convert to normalized format
                for envelope in messages:
                    try:
                        normalized_msg = self._normalize_envelope(envelope, list_name)
                        if normalized_msg:
                            all_messages.append(normalized_msg)
                            
                            # Check max messages limit
                            if max_messages and len(all_messages) >= max_messages:
                                self.logger.info(f"Reached max messages limit: {max_messages}")
                                return all_messages
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing message: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error fetching mailing list messages: {e}")
        
        self.logger.info(f"Total messages fetched: {len(all_messages)}")
        return all_messages
    
    def fetch_messages(self, 
                      mailing_list: str,
                      start_date: str = "2023-01-01T00:00:00",
                      end_date: str = "2024-12-31T23:59:59",
                      max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch messages from a single IETF mailing list.
        This method is optimized for parallel processing.
        
        Args:
            mailing_list: Name of the mailing list
            start_date: Start date in ISO format
            end_date: End date in ISO format
            max_messages: Maximum number of messages to fetch (None for all)
            
        Returns:
            List of normalized email dictionaries
        """
        if not self.mailarchive:
            self.logger.error("MailArchive not initialized")
            return []
        
        messages = []
        
        try:
            self.logger.info(f"Fetching messages from {mailing_list}")
            
            # Get mailing list object first
            mailing_list_obj = self.mailarchive.mailing_list(mailing_list)
            if not mailing_list_obj:
                self.logger.warning(f"No mailing list found for {mailing_list}")
                return []
            
            # Get messages from the mailing list
            envelopes = list(mailing_list_obj.messages())
            
            self.logger.info(f"Found {len(envelopes)} messages in {mailing_list}")
            
            # Convert to normalized format
            for envelope in envelopes:
                try:
                    normalized_msg = self._normalize_envelope(envelope, mailing_list)
                    if normalized_msg:
                        messages.append(normalized_msg)
                        
                        # Check max messages limit
                        if max_messages and len(messages) >= max_messages:
                            self.logger.info(f"Reached max messages limit for {mailing_list}: {max_messages}")
                            break
                
                except Exception as e:
                    self.logger.warning(f"Error processing message in {mailing_list}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error fetching messages from {mailing_list}: {e}")
            return []
        
        self.logger.info(f"Successfully fetched {len(messages)} messages from {mailing_list}")
        return messages

    def _normalize_envelope(self, envelope, mailing_list_name: str) -> Optional[Dict[str, Any]]:
        """
        Convert ietfdata Envelope to normalized pipeline format.
        
        Args:
            envelope: ietfdata Envelope object
            mailing_list_name: Name of the mailing list
            
        Returns:
            Normalized email dictionary or None if conversion fails
        """
        try:
            # Extract basic message data
            from_addr = envelope.from_()
            to_addrs = envelope.to()
            cc_addrs = envelope.cc()
            
            # Convert Address objects to strings
            from_email = from_addr.addr_spec if from_addr else ""
            from_name = from_addr.display_name if from_addr else ""
            
            to_emails = [addr.addr_spec for addr in to_addrs] if to_addrs else []
            cc_emails = [addr.addr_spec for addr in cc_addrs] if cc_addrs else []
            
            # Get message content (headers and body)
            try:
                message_content = envelope.contents()
                body = self._extract_text_content(message_content)
            except:
                body = ""
            
            # Build normalized message
            normalized = {
                "message_id": envelope.message_id(),
                "from": from_email,
                "from_name": from_name,
                "to": to_emails,
                "cc": cc_emails,
                "subject": envelope.subject(),
                "date": envelope.date().isoformat(),
                "date_received": envelope.date_received().isoformat(),
                "body": body,
                "size": envelope.size(),
                "mailing_list": mailing_list_name,
                "list_name": mailing_list_name,  # Alias for compatibility
                "uid": envelope.uid(),
                "uidvalidity": envelope.uidvalidity(),
                
                # Reply relationship
                "in_reply_to": [msg.message_id() for msg in (envelope.in_reply_to() or [])],
                "replies": [msg.message_id() for msg in (envelope.replies() or [])],
                
                # Raw headers for reference
                "headers": {
                    "from": envelope.header("from"),
                    "to": envelope.header("to"),
                    "subject": envelope.header("subject"),
                    "date": envelope.header("date"),
                    "message-id": envelope.header("message-id"),
                    "in-reply-to": envelope.header("in-reply-to")
                }
            }
            
            return normalized
        
        except Exception as e:
            self.logger.warning(f"Error normalizing envelope: {e}")
            return None
    
    def _extract_text_content(self, message) -> str:
        """
        Extract plain text content from email message.
        
        Args:
            message: Email message object
            
        Returns:
            Plain text content
        """
        try:
            if hasattr(message, 'get_body'):
                # Try to get plain text body
                body = message.get_body(preferencelist=('plain', 'html'))
                if body:
                    return body.get_content()
            
            # Fallback: get payload as string
            if hasattr(message, 'get_payload'):
                payload = message.get_payload()
                if isinstance(payload, str):
                    return payload
            
            return ""
        
        except Exception as e:
            self.logger.warning(f"Error extracting text content: {e}")
            return ""
    
    def fetch_person_metadata(self, email_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch person metadata from IETF Datatracker.
        
        Args:
            email_addresses: List of email addresses to look up
            
        Returns:
            Dictionary mapping email -> person metadata
        """
        if not self.datatracker:
            self.logger.error("DataTracker not initialized")
            return {}
        
        person_metadata = {}
        
        try:
            for email_addr in email_addresses:
                try:
                    # Look up person by email
                    email_obj = self.datatracker.email_for_address(email_addr)
                    if email_obj and email_obj.person:
                        person = email_obj.person
                        
                        person_metadata[email_addr] = {
                            "name": getattr(person, 'name', ''),
                            "ascii_name": getattr(person, 'ascii', ''),
                            "biography": getattr(person, 'biography', ''),
                            "person_uri": str(getattr(person, 'resource_uri', '')),
                            "email_uri": str(getattr(email_obj, 'resource_uri', '')),
                            "active": getattr(email_obj, 'active', False),
                            "primary": getattr(email_obj, 'primary', False)
                        }
                
                except Exception as e:
                    self.logger.debug(f"No metadata found for {email_addr}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error fetching person metadata: {e}")
        
        self.logger.info(f"Fetched metadata for {len(person_metadata)} people")
        return person_metadata
    
    def enrich_with_person_metadata(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich messages with person metadata from IETF Datatracker.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of messages enriched with person metadata
        """
        if not self.datatracker:
            self.logger.warning("DataTracker not initialized, skipping person metadata enrichment")
            return messages
        
        try:
            self.logger.info("Enriching messages with person metadata...")
            
            # Extract unique email addresses
            unique_emails = set()
            for msg in messages:
                from_email = msg.get('from', '')
                if from_email:
                    unique_emails.add(from_email)
            
            self.logger.info(f"Found {len(unique_emails)} unique email addresses")
            
            # Fetch person data for each email
            person_cache = {}
            for email in unique_emails:
                try:
                    # Query person by email using the correct API
                    email_obj = self.datatracker.email_for_address(email)
                    if email_obj and email_obj.person:
                        person_cache[email] = email_obj.person
                except Exception as e:
                    self.logger.debug(f"Could not fetch person data for {email}: {e}")
                    continue
            
            # Enrich messages with person metadata
            enriched_messages = []
            for msg in messages:
                from_email = msg.get('from', '')
                if from_email in person_cache:
                    person = person_cache[from_email]
                    msg['person_name'] = getattr(person, 'name', None)
                    msg['person_ascii_name'] = getattr(person, 'ascii', None)
                    msg['person_biography'] = getattr(person, 'biography', None)
                
                enriched_messages.append(msg)
            
            self.logger.info(f"Enriched {len([m for m in enriched_messages if 'person_name' in m])} messages with person metadata")
            return enriched_messages
            
        except Exception as e:
            self.logger.error(f"Error enriching with person metadata: {e}")
            return messages

    def save_to_json(self, 
                     data: List[Dict[str, Any]], 
                     output_file: str,
                     pretty: bool = True) -> bool:
        """
        Save data to JSON file.
        
        Args:
            data: Data to save
            output_file: Output file path
            pretty: Whether to pretty-print JSON
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(data, f, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved {len(data)} records to {output_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
            return False
    
    def fetch_and_save_data(self,
                            mailing_lists: List[str],
                            output_file: str,
                            start_date: str = "2023-01-01T00:00:00",
                            end_date: str = "2024-12-31T23:59:59",
                            max_messages: Optional[int] = None,
                            update_lists: bool = True,
                            fetch_person_metadata: bool = True) -> bool:
        """
        Complete workflow to fetch IETF data and save to JSON.
        
        Args:
            mailing_lists: List of mailing list names
            output_file: Output JSON file path
            start_date: Start date for message retrieval
            end_date: End date for message retrieval
            max_messages: Maximum messages to fetch
            update_lists: Whether to update mailing list data first
            fetch_person_metadata: Whether to fetch person metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update mailing list data if requested
            if update_lists:
                self.logger.info("Updating mailing list data...")
                if not self.update_mailing_list_data(mailing_lists):
                    self.logger.warning("Failed to update some mailing list data")
            
            # Fetch messages
            self.logger.info("Fetching messages...")
            messages = self.fetch_mailing_list_messages(
                mailing_lists, start_date, end_date, max_messages
            )
            
            if not messages:
                self.logger.error("No messages fetched")
                return False
            
            # Fetch person metadata if requested
            if fetch_person_metadata:
                self.logger.info("Fetching person metadata...")
                unique_emails = set()
                for msg in messages:
                    unique_emails.add(msg.get('from', ''))
                    unique_emails.update(msg.get('to', []))
                    unique_emails.update(msg.get('cc', []))
                
                unique_emails.discard('')  # Remove empty emails
                person_data = self.fetch_person_metadata(list(unique_emails))
                
                # Add person metadata to messages
                for msg in messages:
                    from_email = msg.get('from', '')
                    if from_email in person_data:
                        msg['person_metadata'] = person_data[from_email]
            
            # Save to JSON
            return self.save_to_json(messages, output_file)
        
        except Exception as e:
            self.logger.error(f"Error in fetch_and_save_data workflow: {e}")
            return False
    
    def fetch_messages_sql(self, 
                          mailing_list: str,
                          start_date: str = "2024-01-01T00:00:00",
                          end_date: str = "2024-12-31T23:59:59",
                          max_messages: Optional[int] = None,
                          db_path: str = "cache/ietfdata.sqlite") -> List[Dict[str, Any]]:
        """
        Fetch messages directly from the SQLite database (bypassing ietfdata API).
        
        Args:
            mailing_list: Name of the mailing list
            start_date: Start date in ISO format
            end_date: End date in ISO format
            max_messages: Maximum number of messages to fetch
            db_path: Path to the SQLite database
            
        Returns:
            List of message dictionaries
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                m.message_num,
                m.mailing_list,
                m.uidvalidity,
                m.uid,
                m.message as message_blob,
                m.size,
                m.date_received,
                h.from_name,
                h.from_addr,
                h.subject,
                h.date,
                h.message_id,
                h.in_reply_to
            FROM ietf_ma_msg m
            JOIN ietf_ma_hdr h ON m.message_num = h.message_num
            WHERE m.mailing_list = ?
            AND h.date >= ?
            AND h.date <= ?
            ORDER BY h.date DESC
        """
        
        params = [mailing_list, start_date, end_date]
        
        if max_messages:
            query += " LIMIT ?"
            params.append(str(max_messages))
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            try:
                # Parse the message blob to extract body
                message_blob = row['message_blob']
                body = ""
                
                if message_blob:
                    try:
                        # Try to parse as email message
                        email_msg = email.message_from_bytes(message_blob)
                        body = self._extract_text_from_email(email_msg)
                    except Exception as e:
                        # If parsing fails, try as string
                        try:
                            body = message_blob.decode('utf-8', errors='ignore')
                        except:
                            body = str(message_blob)
                
                # Build normalized message
                message = {
                    "message_id": row['message_id'],
                    "from": row['from_addr'] or "",
                    "from_name": row['from_name'] or "",
                    "to": [],
                    "cc": [],
                    "subject": row['subject'] or "",
                    "date": row['date'],
                    "date_received": row['date_received'],
                    "body": body,
                    "size": row['size'] or 0,
                    "mailing_list": row['mailing_list'],
                    "list_name": row['mailing_list'],
                    "uid": row['uid'],
                    "uidvalidity": row['uidvalidity'],
                    "in_reply_to": [row['in_reply_to']] if row['in_reply_to'] else [],
                    "replies": [],
                    "headers": {
                        "from": row['from_addr'],
                        "subject": row['subject'],
                        "date": row['date'],
                        "message-id": row['message_id'],
                        "in-reply-to": row['in_reply_to']
                    }
                }
                
                messages.append(message)
                
            except Exception as e:
                print(f"Error processing message {row['message_id']}: {e}")
                continue
        
        conn.close()
        return messages
    
    def _extract_text_from_email(self, email_msg) -> str:
        """Extract plain text from an email message."""
        try:
            # Get plain text part
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == 'text/plain':
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            return payload.decode('utf-8', errors='ignore')
                        else:
                            return str(payload)
            else:
                if email_msg.get_content_type() == 'text/plain':
                    payload = email_msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        return payload.decode('utf-8', errors='ignore')
                    else:
                        return str(payload)
            
            # Fallback to any text content
            return str(email_msg.get_payload())
        except Exception as e:
            return ""

def main():
    """Command-line interface for IETF data acquisition."""
    import argparse
    
    parser = argparse.ArgumentParser(description="IETF Data Acquisition using ietfdata library")
    parser.add_argument("--lists", nargs="+", required=True,
                        help="Mailing list names to fetch")
    parser.add_argument("--output", "-o", required=True,
                        help="Output JSON file")
    parser.add_argument("--start-date", default="2023-01-01T00:00:00",
                        help="Start date (ISO format)")
    parser.add_argument("--end-date", default="2024-12-31T23:59:59",
                        help="End date (ISO format)")
    parser.add_argument("--max-messages", type=int,
                        help="Maximum messages to fetch")
    parser.add_argument("--cache-file", default="ietfdata.sqlite",
                        help="SQLite cache file")
    parser.add_argument("--no-cache", action="store_true",
                        help="Use live queries instead of cache")
    parser.add_argument("--no-update", action="store_true",
                        help="Skip updating mailing list data")
    parser.add_argument("--no-person-metadata", action="store_true",
                        help="Skip fetching person metadata")
    parser.add_argument("--list-available", action="store_true",
                        help="List available mailing lists and exit")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    
    args = parser.parse_args()
    
    # Initialize data acquisition
    try:
        data_acq = IETFDataAcquisition(
            cache_file=args.cache_file,
            use_cache=not args.no_cache,
            log_level=args.log_level
        )
        
        # List available mailing lists if requested
        if args.list_available:
            print("Available mailing lists:")
            lists = data_acq.get_available_mailing_lists()
            for mlist in lists[:50]:  # Show first 50
                print(f"  {mlist}")
            if len(lists) > 50:
                print(f"  ... and {len(lists) - 50} more")
            return
        
        # Fetch and save data
        success = data_acq.fetch_and_save_data(
            mailing_lists=args.lists,
            output_file=args.output,
            start_date=args.start_date,
            end_date=args.end_date,
            max_messages=args.max_messages,
            update_lists=not args.no_update,
            fetch_person_metadata=not args.no_person_metadata
        )
        
        if success:
            print(f"Successfully saved data to {args.output}")
        else:
            print("Failed to fetch and save data")
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
