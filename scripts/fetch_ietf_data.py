#!/usr/bin/env python3
"""
IETF Data Fetcher
=================

This script fetches IETF mailing list messages by directly querying the SQLite database.
It provides high-performance parallel data acquisition with multi-threading support.

Usage:
    python fetch_ietf_data.py --lists ietf cfrg --max-messages 500 --threads 4
    python fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --end-date 2024-12-31T23:59:59
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import email
import email.utils
from email.message import EmailMessage

def connect_to_db(db_path: str) -> sqlite3.Connection:
    """Connect to the IETF SQLite database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

def fetch_messages_from_db(db_path: str, 
                          mailing_list: str,
                          start_date: str = "2024-01-01T00:00:00",
                          end_date: str = "2024-12-31T23:59:59",
                          max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch messages directly from the SQLite database.
    
    Args:
        db_path: Path to the SQLite database
        mailing_list: Name of the mailing list
        start_date: Start date in ISO format
        end_date: End date in ISO format
        max_messages: Maximum number of messages to fetch
        
    Returns:
        List of message dictionaries
    """
    conn = connect_to_db(db_path)
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
                    body = extract_text_from_email(email_msg)
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
                "to": [],  # Will be populated later if needed
                "cc": [],  # Will be populated later if needed
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
                "replies": [],  # Will be populated later if needed
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

def extract_text_from_email(email_msg) -> str:
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

def fetch_single_list_sql(args) -> tuple:
    """Fetch messages from a single mailing list using SQL."""
    db_path, mailing_list, start_date, end_date, max_messages = args
    
    try:
        print(f"🔄 Starting {mailing_list}...")
        messages = fetch_messages_from_db(
            db_path, mailing_list, start_date, end_date, max_messages
        )
        print(f"✅ Completed {mailing_list}: {len(messages)} messages")
        return mailing_list, messages, True
    except Exception as e:
        print(f"❌ Error fetching {mailing_list}: {e}")
        return mailing_list, [], False

def parallel_fetch_sql(db_path: str,
                      mailing_lists: List[str],
                      start_date: str,
                      end_date: str,
                      max_messages: Optional[int] = None,
                      max_workers: int = 4) -> Dict[str, List[Dict]]:
    """
    Fetch IETF data from multiple mailing lists in parallel using SQL.
    """
    print(f"🚀 Starting parallel SQL fetch with {max_workers} threads...")
    print(f"📋 Fetching from {len(mailing_lists)} mailing lists: {', '.join(mailing_lists)}")
    print(f"📅 Date range: {start_date} to {end_date}")
    if max_messages:
        print(f"📊 Max messages per list: {max_messages}")
    print("=" * 80)
    
    # Prepare arguments for each thread
    fetch_args = [
        (db_path, list_name, start_date, end_date, max_messages)
        for list_name in mailing_lists
    ]
    
    results = {}
    start_time = datetime.now()
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_list = {
            executor.submit(fetch_single_list_sql, args): args[1] 
            for args in fetch_args
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_list):
            list_name = future_to_list[future]
            try:
                list_name, messages, success = future.result()
                results[list_name] = messages
                if not success:
                    print(f"⚠️  Failed to fetch data from {list_name}")
            except Exception as e:
                print(f"❌ Exception in thread for {list_name}: {e}")
                results[list_name] = []
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("=" * 80)
    print(f"✅ Parallel SQL fetch completed in {duration:.2f} seconds")
    print(f"📊 Total messages fetched: {sum(len(msgs) for msgs in results.values())}")
    print(f"⚡ Average speed: {sum(len(msgs) for msgs in results.values()) / duration:.2f} messages/second")
    
    return results

def main():
    """Main entry point for SQL-based IETF data fetching."""
    parser = argparse.ArgumentParser(description="Fetch IETF data using direct SQL queries")
    parser.add_argument("--lists", nargs="+", required=True, help="Mailing list names to fetch")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--start-date", default="2024-01-01T00:00:00", help="Start date")
    parser.add_argument("--end-date", default="2024-12-31T23:59:59", help="End date")
    parser.add_argument("--max-messages", type=int, help="Max messages per list")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    parser.add_argument("--db-path", default="cache/ietfdata.sqlite", help="Database path")
    
    args = parser.parse_args()
    
    # Set default output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"data/ietf_sql_{timestamp}.json"
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    try:
        # Fetch data using SQL
        results = parallel_fetch_sql(
            db_path=args.db_path,
            mailing_lists=args.lists,
            start_date=args.start_date,
            end_date=args.end_date,
            max_messages=args.max_messages,
            max_workers=args.threads
        )
        
        # Combine all messages
        all_messages = []
        for list_name, messages in results.items():
            all_messages.extend(messages)
        
        # Save to JSON
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_messages, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n🎉 Successfully saved {len(all_messages)} messages to {args.output}")
        print("\nNext steps:")
        print(f"  1. Review the data: head -n 20 {args.output}")
        print(f"  2. Run analysis: python src/main.py {args.output}")
        print("  3. Open visualization: open visualisation/index.html")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
