#!/usr/bin/env python3
"""
IETF Data Download Progress Report
==================================

Generate detailed download progress report
"""

import os
import sqlite3
from datetime import datetime

def generate_progress_report():
    """Generate detailed progress report"""
    print("📊 IETF Data Download Progress Report")
    print("=" * 80)
    print(f"🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # First tier list definition
    tier1_lists = ['cfrg', 'quic', 'tls', 'oauth', 'dnsop', 'v6ops', 'rtgwg', 'tsvwg', 'saag', 'netmod']
    
    # Check log file
    log_file = "batch_download.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Analyze logs
        started_lists = []
        current_processing = None
        
        for line in lines:
            if "Updating mailing list:" in line:
                list_name = line.split("Updating mailing list: ")[1].strip()
                if list_name not in started_lists:
                    started_lists.append(list_name)
                current_processing = list_name
            elif "mailarchive3:update:" in line and current_processing:
                # Continue processing current list
                pass
        
        # Status statistics
        completed = []
        in_progress = []
        
        for lst in tier1_lists:
            if lst in started_lists:
                # Check if completed
                list_completed = False
                for i, line in enumerate(lines):
                    if f"Updating mailing list: {lst}" in line:
                        # Look for subsequent start of next list
                        for j in range(i+1, len(lines)):
                            if "Updating mailing list:" in lines[j]:
                                next_list = lines[j].split("Updating mailing list: ")[1].strip()
                                if next_list != lst:
                                    list_completed = True
                                    break
                        break
                
                if list_completed:
                    completed.append(lst)
                else:
                    in_progress.append(lst)
        
        # Display progress
        print(f"🎯 Tier 1 (Core Technical Lists) - {len(completed)}/{len(tier1_lists)} completed")
        print()
        
        if completed:
            print("✅ Completed:")
            for lst in completed:
                print(f"  • {lst}")
        print()
        
        if in_progress:
            print("🔄 In Progress:")
            for lst in in_progress:
                print(f"  • {lst}")
        print()
        
        pending = [lst for lst in tier1_lists if lst not in started_lists]
        if pending:
            print("⏳ Pending:")
            for lst in pending:
                print(f"  • {lst}")
        print()
        
        # Latest activity
        print("📋 Latest Activity:")
        for line in lines[-5:]:
            if "INFO" in line:
                timestamp = line.split(" - INFO - ")[0]
                message = line.split(" - INFO - ")[1].strip()
                print(f"  {timestamp}: {message}")
        
    # Database statistics
    print("\n" + "=" * 80)
    print("💾 Database Statistics")
    
    db_path = "cache/ietfdata.sqlite"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        size_gb = size / (1024 * 1024 * 1024)
        print(f"📊 Cache size: {size_gb:.2f} GB")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📋 Database table count: {len(tables)}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
    
    print("\n" + "=" * 80)
    print("💡 Tips:")
    print("  • Tier 1 download estimated to take 1-2 hours")
    print("  • Tier 2 download will start automatically after completion")
    print("  • Full download may result in 10-20GB database")
    print()

if __name__ == "__main__":
    generate_progress_report()
