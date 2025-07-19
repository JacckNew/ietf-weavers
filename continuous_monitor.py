#!/usr/bin/env python3
"""
Continuous Download Progress Monitor
===================================

Continuously monitor download progress until completion
"""

import time
import os
from datetime import datetime

def continuous_monitor():
    """Continuously monitor download progress"""
    print("📡 Continuous Download Progress Monitor")
    print("=" * 60)
    
    tier1_lists = ['cfrg', 'quic', 'tls', 'oauth', 'dnsop', 'v6ops', 'rtgwg', 'tsvwg', 'saag', 'netmod']
    
    while True:
        print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - Checking progress...")
        
        # Check log file
        log_file = "batch_download.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find lists that have started processing
            started_lists = []
            completed_lists = []
            
            for line in lines:
                if "Updating mailing list:" in line:
                    list_name = line.split("Updating mailing list: ")[1].strip()
                    if list_name not in started_lists:
                        started_lists.append(list_name)
                
                # Look for completion markers
                if "completed successfully" in line.lower():
                    for lst in tier1_lists:
                        if lst in line:
                            if lst not in completed_lists:
                                completed_lists.append(lst)
            
            # Status display
            print(f"✅ Completed: {len(completed_lists)}/10")
            print(f"🔄 Started: {len(started_lists)}/10")
            
            # Show latest lines
            print("📋 Latest logs:")
            for line in lines[-3:]:
                if "INFO" in line:
                    print(f"  {line.strip()}")
            
            # Check if completed
            if len(started_lists) >= 10:
                print("\n🎉 First tier download may be completed!")
                break
            
            # Check cache size
            cache_path = "cache/ietfdata.sqlite"
            if os.path.exists(cache_path):
                size = os.path.getsize(cache_path)
                size_gb = size / (1024 * 1024 * 1024)
                print(f"💾 Cache size: {size_gb:.2f} GB")
        
        # Wait 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    try:
        continuous_monitor()
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
