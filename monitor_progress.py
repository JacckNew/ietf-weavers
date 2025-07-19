#!/usr/bin/env python3
"""
Download Progress Monitor
========================

Monitor batch download progress and status
"""

import os
import time
import sys
from datetime import datetime

def monitor_download_progress():
    """Monitor download progress"""
    print("🔍 IETF Data Download Progress Monitor")
    print("=" * 60)
    
    # Check log file
    log_file = "batch_download.log"
    data_dir = "data"
    
    if os.path.exists(log_file):
        print(f"📋 Log file: {log_file}")
        
        # Read last few log lines
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print("\n📊 Latest logs (last 10 lines):")
        for line in lines[-10:]:
            print(f"  {line.strip()}")
    else:
        print("⚠️ Log file does not exist")
    
    # Check data directory
    if os.path.exists(data_dir):
        print(f"\n📁 Data directory: {data_dir}")
        files = os.listdir(data_dir)
        
        # Filter today's files
        today = datetime.now().strftime("%Y%m%d")
        today_files = [f for f in files if today in f]
        
        if today_files:
            print("🎯 Today's download files:")
            for file in today_files:
                file_path = os.path.join(data_dir, file)
                size = os.path.getsize(file_path)
                size_mb = size / (1024 * 1024)
                print(f"  {file}: {size_mb:.2f} MB")
        else:
            print("⏳ No download files for today yet")
    
    # Check cache directory
    cache_dir = "cache"
    if os.path.exists(cache_dir):
        print(f"\n💾 Cache directory: {cache_dir}")
        cache_files = os.listdir(cache_dir)
        
        for file in cache_files:
            if file.endswith('.sqlite'):
                file_path = os.path.join(cache_dir, file)
                size = os.path.getsize(file_path)
                size_gb = size / (1024 * 1024 * 1024)
                print(f"  {file}: {size_gb:.2f} GB")

if __name__ == "__main__":
    monitor_download_progress()
