#!/usr/bin/env python3
"""
Stress Test Script

This script performs load testing on the eDrop API endpoint by sending concurrent requests
at a specified rate for a specified duration.

Usage:
    python stress_test.py --host HOST_URL [options]

Options:
    --host      Base host URL (required)
    --rps       Requests per second (default: 20)
    --duration  Test duration in seconds (default: 60)

Examples:
    # Run against your eDrop host with default settings (20 rps, 60 seconds)
    python stress_test.py --host http://your-edrop-api-host/edrop/

    # Run with custom settings
    python stress_test.py --host http://your-edrop-api-host/edrop/ --rps 30 --duration 120

    # Run a quick test with lower values
    python stress_test.py --host http://your-edrop-api-host/edrop/ --rps 5 --duration 10

Results:
    - Prints real-time progress during the test
    - Shows summary statistics after completion
    - Saves detailed results to 'load_test_results.json'
"""

import aiohttp
import asyncio
import time
from datetime import datetime
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Run stress test for edrop API')
    parser.add_argument('--host', required=True,
                      help='Base host URL (required)')
    parser.add_argument('--rps', type=int, default=20,
                      help='Requests per second (default: 20)')
    parser.add_argument('--duration', type=int, default=60,
                      help='Total duration in seconds (default: 60)')
    return parser.parse_args()


# Test payload for the API requests
TEST_PAYLOAD = {
    'instrument': 'consent',
    'record': '999999', # this is a test record id hence it will not exist in the database
    'project_id': 'test',
    'project_url': 'http://test.com',
    'contact_complete': '2'
}

async def make_request(session, request_id, base_url):
    start_time = time.time()
    try:
        async with session.post(base_url, data=TEST_PAYLOAD) as response:
            duration = time.time() - start_time
            status = response.status
            try:
                text = await response.text()
            except:
                text = "Could not read response"
            
            return {
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'duration': duration,
                'response': text
            }
    except Exception as e:
        return {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'duration': time.time() - start_time,
            'response': str(e)
        }

async def run_load_test(base_url, requests_per_second, duration):
    results = []
    request_counter = 0
    
    # Calculate delay between requests
    delay = 1.0 / requests_per_second
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        while time.time() - start_time < duration:
            tasks = []
            batch_start = time.time()
            
            # Create a batch of requests
            task = asyncio.create_task(make_request(session, request_counter, base_url))
            tasks.append(task)
            request_counter += 1
            
            # Wait for the batch to complete
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Calculate sleep time to maintain rate
            elapsed = time.time() - batch_start
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            
            # Print progress
            print(f"\rRequests sent: {request_counter}, Elapsed time: {int(time.time() - start_time)}s", end='')
    
    return results

async def main():
    args = parse_args()
    
    base_url = f"{args.host}api/order/create"
    requests_per_second = args.rps
    duration = args.duration
    
    print(f"Starting load test - {requests_per_second} requests/second for {duration} seconds")
    print(f"Target URL: {base_url}")
    results = await run_load_test(base_url, requests_per_second, duration)
    
    # Analyze results
    total_requests = len(results)
    successful_requests = sum(1 for r in results if isinstance(r['status'], int) and 200 <= r['status'] < 300)
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print("\n\nTest Results:")
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Average Response Time: {avg_duration:.3f}s")
    
    # Save detailed results to file
    with open('load_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to load_test_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 