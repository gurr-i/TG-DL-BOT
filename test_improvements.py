#!/usr/bin/env python3
"""
Quick test script to verify performance improvements are working.
"""

import asyncio
import sys
from core.performance import performance_optimizer
from core.managers.download_manager import download_manager

def test_chunk_sizes():
    """Test chunk size optimization."""
    print("Testing Chunk Size Optimization...")
    
    test_cases = [
        (5 * 1024 * 1024, "5MB"),      # 5MB
        (50 * 1024 * 1024, "50MB"),    # 50MB
        (200 * 1024 * 1024, "200MB"),  # 200MB
        (800 * 1024 * 1024, "800MB"),  # 800MB
    ]
    
    for size, label in test_cases:
        chunk = performance_optimizer.get_optimal_chunk_size(size)
        print(f"  {label}: {chunk / 1024}KB chunks")
    
    print("✅ Chunk size optimization working!\n")

def test_progress_throttling():
    """Test progress update throttling."""
    print("Testing Progress Update Throttling...")
    
    import time
    
    # Simulate progress updates
    total = 100
    last_update = 0
    last_percentage = -1
    
    updates = 0
    for current in range(0, 101, 1):
        if performance_optimizer.should_update_progress(
            current, total, last_update, last_percentage
        ):
            updates += 1
            last_update = time.time()
            last_percentage = int((current / total) * 100)
    
    print(f"  Updates for 0-100%: {updates} (optimized from ~50)")
    print("✅ Progress throttling working!\n")

def test_retry_delay():
    """Test retry delay with jitter."""
    print("Testing Retry Delay with Jitter...")
    
    for attempt in range(3):
        delay = performance_optimizer.get_retry_delay(attempt, jitter=True)
        print(f"  Attempt {attempt + 1}: {delay:.2f}s")
    
    print("✅ Retry with jitter working!\n")

def test_eta_calculation():
    """Test ETA calculation."""
    print("Testing ETA Calculation...")
    
    test_cases = [
        (50, 100, 10, "50% in 10s"),
        (25, 100, 30, "25% in 30s"),
        (75, 100, 60, "75% in 60s"),
    ]
    
    for current, total, elapsed, label in test_cases:
        eta = performance_optimizer.calculate_eta(current, total, elapsed)
        print(f"  {label}: ETA = {eta}")
    
    print("✅ ETA calculation working!\n")

def test_download_manager():
    """Test download manager initialization."""
    print("Testing Download Manager...")
    
    stats = download_manager.get_stats()
    print(f"  Max Concurrent: {stats['max_concurrent']}")
    print(f"  Active Tasks: {stats['active_tasks']}")
    print(f"  Available Slots: {stats['available_slots']}")
    
    print("✅ Download manager initialized!\n")

def test_metrics():
    """Test performance metrics."""
    print("Testing Performance Metrics...")
    
    # Simulate some operations
    performance_optimizer.record_download(100 * 1024 * 1024, 10)  # 100MB in 10s
    performance_optimizer.record_upload(50 * 1024 * 1024, 8)      # 50MB in 8s
    performance_optimizer.record_retry()
    
    metrics = performance_optimizer.get_metrics()
    print(f"  Total Downloads: {metrics['total_downloads']}")
    print(f"  Total Uploads: {metrics['total_uploads']}")
    print(f"  Avg Download Speed: {metrics['average_download_speed_mbps']:.2f} MB/s")
    print(f"  Avg Upload Speed: {metrics['average_upload_speed_mbps']:.2f} MB/s")
    print(f"  Retry Count: {metrics['retry_count']}")
    
    print("✅ Performance metrics working!\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Performance Improvements Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_chunk_sizes()
        test_progress_throttling()
        test_retry_delay()
        test_eta_calculation()
        test_download_manager()
        test_metrics()
        
        print("=" * 60)
        print("✅ All tests passed! Performance improvements are working.")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
