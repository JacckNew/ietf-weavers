#!/usr/bin/env python3
"""
IETF Core Lists Downloader
==========================

Download historical data from IETF core technical mailing lists, 
using the ietfdata library to fetch data from IETF servers.

Usage:
    python download_core_lists.py --batch 1
    python download_core_lists.py --batch 2
    python download_core_lists.py --all
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.data_acquisition import IETFDataAcquisition

def main():
    parser = argparse.ArgumentParser(description="Download IETF core technical mailing lists")
    parser.add_argument('--batch', type=int, choices=[1, 2, 3, 4], 
                        help='Download specific batch (1-4)')
    parser.add_argument('--all', action='store_true',
                        help='Download all core lists')
    parser.add_argument('--output-dir', default='data',
                        help='Output directory for downloaded data')
    parser.add_argument('--cache-file', default='cache/ietfdata.sqlite',
                        help='SQLite cache file path')
    
    args = parser.parse_args()
    
    # Define core technical lists, divided into 4 batches
    core_batches = {
        1: ['cfrg', 'quic', 'tls', 'oauth', 'dnsop'],           # Security and protocols
        2: ['v6ops', 'rtgwg', 'tsvwg', 'opsawg', 'netmod'],     # Network operations
        3: ['netconf', 'saag', 'anima', 'spring', 'ace'],       # Management and automation
        4: ['httpapi', 'http', 'mmusic', 'iptel', 'sip']        # Applications and multimedia
    }
    
    # Determine which lists to download
    if args.all:
        lists_to_download = []
        for batch_lists in core_batches.values():
            lists_to_download.extend(batch_lists)
    elif args.batch:
        lists_to_download = core_batches[args.batch]
    else:
        parser.error("Please specify --batch <number> or --all")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"🚀 IETF Core Technical Lists Downloader")
    print(f"📋 Preparing to download {len(lists_to_download)} mailing lists: {', '.join(lists_to_download)}")
    print(f"💾 Cache file: {args.cache_file}")
    print(f"📁 Output directory: {args.output_dir}")
    print("=" * 80)
    
    # Initialize data acquisition engine
    try:
        acquisition = IETFDataAcquisition(
            cache_file=args.cache_file,
            use_cache=True,
            log_level="INFO"
        )
    except Exception as e:
        print(f"❌ Failed to initialize data acquisition engine: {e}")
        print("💡 Please ensure ietfdata library is installed: pip install ietfdata")
        return 1
    
    # Update mailing list data
    print("🔄 Updating mailing list data from IETF server...")
    success = acquisition.update_mailing_list_data(
        mailing_list_names=lists_to_download,
        force_update=False
    )
    
    if not success:
        print("❌ Failed to update mailing list data")
        return 1
    
    print("✅ Mailing list data update completed")
    
    # Get message data
    print("📨 Fetching email messages...")
    messages = acquisition.fetch_mailing_list_messages(
        mailing_list_names=lists_to_download,
        start_date="1992-01-01T00:00:00",
        end_date="2025-12-31T23:59:59"
    )
    
    if not messages:
        print("⚠️ No message data retrieved")
        return 1
    
    print(f"✅ Successfully retrieved {len(messages)} messages")
    
    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.batch:
        filename = f"core_lists_batch{args.batch}_{timestamp}.json"
    else:
        filename = f"core_lists_all_{timestamp}.json"
    
    output_path = os.path.join(args.output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Data saved to: {output_path}")
    print(f"📊 Total: {len(messages)} messages")
    
    # Display statistics by list
    list_stats = {}
    for msg in messages:
        list_name = msg.get('list_name', 'unknown')
        list_stats[list_name] = list_stats.get(list_name, 0) + 1
    
    print("\n📈 Statistics by list:")
    for list_name, count in sorted(list_stats.items()):
        print(f"  {list_name}: {count} messages")
    
    print("\n🎉 Download completed!")
    print(f"💡 Next step: python src/main.py {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
