#!/usr/bin/env python3
"""
Download Status Checker
=======================

Check current download status and completion progress
"""

import sqlite3
import os
from datetime import datetime

def check_download_status():
    """Check current download status"""
    print("📊 IETF Data Download Status Check")
    print("=" * 60)
    
    # Check cache database
    db_path = "cache/ietfdata.sqlite"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get mailing list information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"📋 Database table count: {len(tables)}")
            
            # Check mailing list count
            if ('mailing_list_info',) in tables:
                cursor.execute("SELECT COUNT(*) FROM mailing_list_info")
                list_count = cursor.fetchone()[0]
                print(f"📧 Retrieved mailing lists: {list_count}")
            
            # Check total message count
            if ('messages',) in tables:
                cursor.execute("SELECT COUNT(*) FROM messages")
                msg_count = cursor.fetchone()[0]
                print(f"✉️ Total messages retrieved: {msg_count}")
                
                # Statistics by date
                cursor.execute("""
                    SELECT date(timestamp) as date, COUNT(*) as count 
                    FROM messages 
                    GROUP BY date(timestamp) 
                    ORDER BY date DESC 
                    LIMIT 10
                """)
                recent_dates = cursor.fetchall()
                
                if recent_dates:
                    print("\n📅 Recent message date distribution:")
                    for date, count in recent_dates:
                        print(f"  {date}: {count} messages")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
    
    # Check log file
    log_file = "batch_download.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Statistics of processing status by list
        print("\n🔍 Log analysis:")
        
        # Find lists that have started processing
        started_lists = []
        for line in lines:
            if "Updating mailing list:" in line:
                list_name = line.split("Updating mailing list: ")[1].strip()
                if list_name not in started_lists:
                    started_lists.append(list_name)
        
        print(f"📋 Lists that have started processing: {started_lists}")
        
        # Find latest activity
        print("\n🔄 Latest activity:")
        for line in lines[-5:]:
            if "INFO" in line:
                print(f"  {line.strip()}")
    
    print("\n" + "=" * 60)
    print("💡 Tip: Download may take several hours, please be patient")

if __name__ == "__main__":
    check_download_status()
