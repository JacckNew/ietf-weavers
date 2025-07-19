#!/usr/bin/env python3
"""
IETF Data Batch Downloader
==========================

Systematically download historical data from IETF core technical mailing lists.
Uses a tiered strategy with support for resumable downloads and error recovery.

Usage:
    python batch_download.py --tier 1      # Download tier 1 core lists
    python batch_download.py --tier 2      # Download tier 2 extended lists
    python batch_download.py --all         # Download all important lists
    python batch_download.py --custom cfrg quic tls  # Custom list selection
"""

import sys
import os
import json
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.data_acquisition import IETFDataAcquisition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchDownloader:
    """Batch download IETF mailing list data"""
    
    def __init__(self, cache_file: str = "cache/ietfdata.sqlite", output_dir: str = "data"):
        self.cache_file = cache_file
        self.output_dir = output_dir
        self.acquisition = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Tiered mailing list definitions
        self.tier_lists = {
            1: {
                "name": "core_technical_lists",
                "lists": [
                    'cfrg',      # Crypto Research Group
                    'quic',      # QUIC Protocol
                    'tls',       # TLS Security
                    'oauth',     # OAuth Authentication
                    'dnsop',     # DNS Operations
                    'v6ops',     # IPv6 Operations
                    'rtgwg',     # Routing Working Group
                    'tsvwg',     # Transport Services WG
                    'saag',      # Security Area Advisory Group
                    'netmod',    # Network Modeling
                ]
            },
            2: {
                "name": "extended_technical_lists",
                "lists": [
                    'netconf',   # Network Configuration
                    'opsawg',    # Operations & Management Area WG
                    'anima',     # Autonomic Networking
                    'spring',    # Source Packet Routing
                    'ace',       # Authentication and Authorization for Constrained Environments
                    'http',      # HTTP
                    'httpapi',   # HTTP API
                    'mmusic',    # Multiparty Multimedia Session
                    'iptel',     # IP Telephony
                    'sip',       # Session Initiation Protocol
                ]
            },
            3: {
                "name": "specialized_technical_lists",
                "lists": [
                    'bmwg',      # Benchmarking Working Group
                    'dhcwg',     # DHCP Working Group
                    'isis-wg',   # ISIS Working Group
                    'krb-wg',    # Kerberos Working Group
                    'tewg',      # Traffic Engineering WG
                    'asrg',      # Anti-Spam Research Group
                    'hiprg',     # Host Identity Protocol Research Group
                    'iccrg',     # Congestion Control Research Group
                    'icnrg',     # Information-Centric Networking Research Group
                    'nfvrg',     # Network Function Virtualization Research Group
                ]
            }
        }
    
    def initialize_acquisition(self):
        """Initialize data acquisition engine"""
        try:
            self.acquisition = IETFDataAcquisition(
                cache_file=self.cache_file,
                use_cache=True,
                log_level="INFO"
            )
            logger.info("✅ Data acquisition engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Data acquisition engine initialization failed: {e}")
            return False
    
    def get_available_lists(self) -> List[str]:
        """Get available mailing lists"""
        if not self.acquisition:
            logger.error("Data acquisition engine not initialized")
            return []
        
        try:
            lists = self.acquisition.get_available_mailing_lists()
            logger.info(f"📋 Found {len(lists)} available mailing lists")
            return lists
        except Exception as e:
            logger.error(f"Failed to get mailing lists: {e}")
            return []
    
    def download_lists(self, lists: List[str], tier_name: str = "") -> bool:
        """Download specified mailing lists"""
        if not self.acquisition:
            logger.error("Data acquisition engine not initialized")
            return False
        
        if not lists:
            logger.warning("No mailing lists specified for download")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tier_suffix = f"_{tier_name}" if tier_name else ""
        
        logger.info(f"🚀 Starting download of {tier_name} ({len(lists)} lists)")
        logger.info(f"📋 Lists: {', '.join(lists)}")
        
        try:
            # Update mailing list data
            logger.info("🔄 Updating mailing list data...")
            success = self.acquisition.update_mailing_list_data(
                mailing_list_names=lists,
                force_update=False
            )
            
            if not success:
                logger.error("❌ Failed to update mailing list data")
                return False
            
            logger.info("✅ Mailing list data update completed")
            
            # Get message data
            logger.info("📨 Fetching email messages...")
            messages = self.acquisition.fetch_mailing_list_messages(
                mailing_list_names=lists,
                start_date="1992-01-01T00:00:00",
                end_date="2025-12-31T23:59:59"
            )
            
            if not messages:
                logger.warning("⚠️ No message data retrieved")
                return False
            
            logger.info(f"✅ Successfully retrieved {len(messages)} messages")
            
            # Save data
            filename = f"ietf_batch{tier_suffix}_{timestamp}.json"
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Data saved to: {output_path}")
            
            # Statistics
            self.print_statistics(messages, lists)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error occurred during download: {e}")
            return False
    
    def print_statistics(self, messages: List[Dict[str, Any]], lists: List[str]):
        """Print download statistics"""
        list_stats = {}
        for msg in messages:
            list_name = msg.get('list_name', 'unknown')
            list_stats[list_name] = list_stats.get(list_name, 0) + 1
        
        logger.info(f"\n📈 Download Statistics:")
        logger.info(f"📊 Total: {len(messages)} messages")
        logger.info(f"📋 Lists involved: {len(list_stats)}")
        
        logger.info("\n📊 Statistics by list:")
        for list_name in sorted(list_stats.keys()):
            count = list_stats[list_name]
            logger.info(f"  {list_name}: {count} messages")
    
    def download_tier(self, tier: int) -> bool:
        """Download mailing lists from specified tier"""
        if tier not in self.tier_lists:
            logger.error(f"❌ Invalid tier: {tier}")
            return False
        
        tier_info = self.tier_lists[tier]
        tier_name = tier_info["name"]
        lists = tier_info["lists"]
        
        return self.download_lists(lists, f"tier{tier}_{tier_name}")
    
    def download_all_tiers(self) -> bool:
        """Download mailing lists from all tiers"""
        all_lists = []
        for tier_info in self.tier_lists.values():
            all_lists.extend(tier_info["lists"])
        
        # Remove duplicates
        all_lists = list(set(all_lists))
        
        return self.download_lists(all_lists, "all_tiers")

def main():
    parser = argparse.ArgumentParser(description="IETF Data Batch Downloader")
    parser.add_argument('--tier', type=int, choices=[1, 2, 3],
                        help='Download mailing lists from specified tier')
    parser.add_argument('--all', action='store_true',
                        help='Download all important mailing lists')
    parser.add_argument('--custom', nargs='+',
                        help='Custom selection of mailing lists to download')
    parser.add_argument('--output-dir', default='data',
                        help='Output directory (default: data)')
    parser.add_argument('--cache-file', default='cache/ietfdata.sqlite',
                        help='SQLite cache file path')
    parser.add_argument('--list-available', action='store_true',
                        help='List all available mailing lists')
    
    args = parser.parse_args()
    
    # Create downloader
    downloader = BatchDownloader(
        cache_file=args.cache_file,
        output_dir=args.output_dir
    )
    
    # Initialize data acquisition engine
    if not downloader.initialize_acquisition():
        logger.error("❌ Initialization failed, exiting program")
        return 1
    
    # List available mailing lists
    if args.list_available:
        lists = downloader.get_available_lists()
        if lists:
            logger.info(f"\n📋 Available mailing lists ({len(lists)}):")
            for i, list_name in enumerate(sorted(lists), 1):
                logger.info(f"  {i:3d}. {list_name}")
        return 0
    
    # Execute download
    success = False
    
    if args.tier:
        success = downloader.download_tier(args.tier)
    elif args.all:
        success = downloader.download_all_tiers()
    elif args.custom:
        success = downloader.download_lists(args.custom, "custom")
    else:
        parser.print_help()
        return 1
    
    if success:
        logger.info("🎉 Download completed!")
        return 0
    else:
        logger.error("❌ Download failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
