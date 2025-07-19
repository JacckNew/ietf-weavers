#!/usr/bin/env python3
"""
IETF Data Download Time Estimator
=================================

Estimate the time required to complete all downloads based on current progress
"""

import os
import sqlite3
from datetime import datetime, timedelta
import json

def estimate_download_time():
    """Estimate download time"""
    print("⏰ IETF Data Download Time Estimation")
    print("=" * 80)
    
    # Current progress data
    start_time = datetime.strptime("2025-07-17 12:06:30", "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    
    print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Elapsed time: {elapsed_time}")
    
    # Database size
    db_path = "cache/ietfdata.sqlite"
    size_gb = 0
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        size_gb = size / (1024 * 1024 * 1024)
        print(f"💾 Current database size: {size_gb:.2f} GB")
    else:
        print("💾 Database file does not exist")
    
    # Tier definitions
    tiers = {
        1: {
            "name": "Core Technical Lists",
            "count": 10,
            "completed": 10,  # Just completed
            "description": "Most important technical components"
        },
        2: {
            "name": "Extended Technical Lists", 
            "count": 10,
            "completed": 0,
            "description": "Important extended features"
        },
        3: {
            "name": "Specialized Technical Lists",
            "count": 10,
            "completed": 0,
            "description": "Specialized applications"
        }
    }
    
    # Estimate remaining important lists
    additional_important = 50  # Estimate 50 more important lists
    
    # Actual total data: 1329 available mailing lists
    total_available = 1329
    
    # Current strategy: focus on 80 most important lists
    total_lists = sum(tier["count"] for tier in tiers.values()) + additional_important
    completed_lists = sum(tier["completed"] for tier in tiers.values())
    
    # Speed calculation
    lists_per_hour = completed_lists / (elapsed_time.total_seconds() / 3600)
    gb_per_hour = size_gb / (elapsed_time.total_seconds() / 3600)
    
    print(f"\n📊 Progress Statistics:")
    print(f"  Completed lists: {completed_lists}")
    print(f"  Planned total lists: {total_lists}")
    print(f"  Available total lists: {total_available}")
    print(f"  Completion ratio: {completed_lists/total_lists*100:.1f}%")
    
    # If user wants estimate for all 1329 lists
    if total_available > total_lists:
        full_hours = (total_available - completed_lists) / lists_per_hour
        full_completion = current_time + timedelta(hours=full_hours)
        full_size = size_gb * (total_available / completed_lists)
        print(f"\n🌐 Complete Dataset Estimate (all {total_available} lists):")
        print(f"  Estimated time: {full_hours:.1f} hours")
        print(f"  Estimated completion: {full_completion.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Estimated size: {full_size:.1f} GB")
    
    print(f"\n🚀 Download Speed:")
    print(f"  List processing speed: {lists_per_hour:.2f} lists/hour")
    print(f"  Data growth speed: {gb_per_hour:.2f} GB/hour")
    
    # Time estimation
    remaining_lists = total_lists - completed_lists
    estimated_hours = remaining_lists / lists_per_hour
    estimated_completion = current_time + timedelta(hours=estimated_hours)
    
    print(f"\n⏰ Time Estimation:")
    print(f"  Remaining lists: {remaining_lists}")
    print(f"  Estimated remaining time: {estimated_hours:.1f} hours")
    print(f"  Estimated completion time: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Data size estimation
    estimated_final_size = size_gb * (total_lists / completed_lists)
    print(f"  Estimated final size: {estimated_final_size:.1f} GB")
    
    # Tier-wise estimation
    print(f"\n📋 Tier Completion Estimation:")
    for tier_num, tier_info in tiers.items():
        if tier_info["completed"] < tier_info["count"]:
            remaining = tier_info["count"] - tier_info["completed"]
            tier_hours = remaining / lists_per_hour
            tier_completion = current_time + timedelta(hours=tier_hours)
            print(f"  Tier {tier_num} ({tier_info['name']}): {tier_hours:.1f} hours ({tier_completion.strftime('%m-%d %H:%M')})")
        else:
            print(f"  Tier {tier_num} ({tier_info['name']}): ✅ Completed")
    
    # Network and system considerations
    print(f"\n⚠️ Influencing Factors:")
    print(f"  • Network speed: may affect ±20% time")
    print(f"  • Server load: may affect ±30% time")
    print(f"  • Database performance: may slow down as size grows")
    print(f"  • Concurrent processes: currently 2 processes may speed up by 50%")
    
    # Optimization suggestions
    print(f"\n💡 Optimization Suggestions:")
    print(f"  • Consider batch downloads to avoid single oversized operations")
    print(f"  • Monitor disk space, reserve adequate space")
    print(f"  • Consider downloading during better network periods")
    
    return estimated_hours, estimated_final_size

if __name__ == "__main__":
    estimate_download_time()
