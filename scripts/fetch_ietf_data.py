#!/usr/bin/env python3
"""
IETF Data Acquisition Script
============================

Standalone script to fetch IETF mailing list data using the glasgow-ipl/ietfdata library.
This script can be used independently to gather IETF data before running the main analysis pipeline.

Usage:
    python fetch_ietf_data.py --lists ietf cfrg --output data/ietf_recent.json
    python fetch_ietf_data.py --list-available
    python fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --max-messages 1000
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add agent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'agent'))

try:
    from agent.data_acquisition import IETFDataAcquisition
except ImportError as e:
    print(f"Error importing data acquisition module: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def main():
    """Main entry point for IETF data acquisition."""
    parser = argparse.ArgumentParser(
        description="Fetch IETF mailing list data using ietfdata library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List available mailing lists
    python fetch_ietf_data.py --list-available

    # Fetch recent data from popular lists
    python fetch_ietf_data.py --lists ietf cfrg --output data/ietf_recent.json

    # Fetch specific date range with limit
    python fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --max-messages 1000

    # Fetch with custom cache location
    python fetch_ietf_data.py --lists ietf --cache-file custom_cache.sqlite

Popular IETF mailing lists to try:
    ietf, cfrg, quic, tls, oauth, httpbis, dnsop, v6ops, rtgwg, lamps
        """
    )
    
    # Required arguments
    parser.add_argument("--lists", nargs="+", 
                        help="Mailing list names to fetch (required unless --list-available)")
    parser.add_argument("--output", "-o", 
                        help="Output JSON file (default: data/ietf_data_TIMESTAMP.json)")
    
    # Date range options
    parser.add_argument("--start-date", 
                        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00"),
                        help="Start date (ISO format, default: 1 year ago)")
    parser.add_argument("--end-date", 
                        default=datetime.now().strftime("%Y-%m-%dT23:59:59"),
                        help="End date (ISO format, default: now)")
    
    # Limits and filters
    parser.add_argument("--max-messages", type=int,
                        help="Maximum messages to fetch (default: unlimited)")
    
    # Cache options
    parser.add_argument("--cache-file", default="ietfdata.sqlite",
                        help="SQLite cache file (default: ietfdata.sqlite)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Use live queries instead of cache (slower)")
    parser.add_argument("--no-update", action="store_true",
                        help="Skip updating mailing list data from server")
    parser.add_argument("--no-person-metadata", action="store_true",
                        help="Skip fetching person metadata from Datatracker")
    
    # Information options
    parser.add_argument("--list-available", action="store_true",
                        help="List available mailing lists and exit")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (default: INFO)")
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    try:
        # Initialize data acquisition
        print("Initializing IETF data acquisition...")
        data_acq = IETFDataAcquisition(
            cache_file=args.cache_file,
            use_cache=not args.no_cache,
            log_level=args.log_level
        )
        
        # List available mailing lists if requested
        if args.list_available:
            print("\\nFetching available IETF mailing lists...")
            lists = data_acq.get_available_mailing_lists()
            
            print(f"\\nFound {len(lists)} mailing lists:")
            print("=" * 50)
            
            # Show popular lists first
            popular_lists = ['ietf', 'cfrg', 'quic', 'tls', 'oauth', 'httpbis', 
                           'dnsop', 'v6ops', 'rtgwg', 'lamps', 'anima', 'spring']
            
            print("Popular lists:")
            for mlist in popular_lists:
                if mlist in lists:
                    print(f"  {mlist}")
            
            print("\\nAll available lists:")
            for i, mlist in enumerate(sorted(lists)):
                if i % 5 == 0:
                    print()
                print(f"  {mlist:<20}", end="")
            print()
            
            print(f"\\nTotal: {len(lists)} mailing lists")
            print("\\nUse --lists option to specify which lists to fetch")
            return 0
        
        # Validate required arguments
        if not args.lists:
            parser.error("--lists is required (or use --list-available to see options)")
        
        # Set default output file
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = f"data/ietf_data_{timestamp}.json"
        
        # Print configuration
        print("\\nConfiguration:")
        print("=" * 50)
        print(f"Mailing lists: {', '.join(args.lists)}")
        print(f"Date range: {args.start_date} to {args.end_date}")
        print(f"Output file: {args.output}")
        print(f"Cache file: {args.cache_file}")
        print(f"Use cache: {not args.no_cache}")
        if args.max_messages:
            print(f"Max messages: {args.max_messages}")
        print("=" * 50)
        
        # Fetch and save data
        print("\\nStarting data acquisition...")
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
            print(f"\\n✅ Successfully saved IETF data to {args.output}")
            print("\\nNext steps:")
            print(f"  1. Review the data: head -n 20 {args.output}")
            print(f"  2. Run analysis: python src/main.py {args.output}")
            print("  3. Open visualization: open visualisation/index.html")
            return 0
        else:
            print("\\n❌ Failed to fetch and save data")
            return 1
    
    except ImportError:
        print("Error: ietfdata library not available")
        print("Install with: pip install ietfdata")
        return 1
    
    except KeyboardInterrupt:
        print("\\n🛑 Interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
