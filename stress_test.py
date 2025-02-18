import aiohttp
import asyncio
import time
from datetime import datetime
import json


BASE_HOST = "http://localhost:8000/edrop/" # Replace with endpoint
BASE_URL = f"{BASE_HOST}api/order/create"

REQUESTS_PER_SECOND = 20
TOTAL_DURATION = 60  # Duration in seconds
TEST_PAYLOAD = {
    'instrument': 'consent',
    'record': '999999', # this is a test record id hence it will not exist in the database
    'project_id': 'test',
    'project_url': 'http://test.com',
    'contact_complete': '2'
}

async def make_request(session, request_id):
    start_time = time.time()
    try:
        async with session.post(BASE_URL, data=TEST_PAYLOAD) as response:
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

async def run_load_test():
    results = []
    request_counter = 0
    
    # Calculate delay between requests
    delay = 1.0 / REQUESTS_PER_SECOND
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        while time.time() - start_time < TOTAL_DURATION:
            tasks = []
            batch_start = time.time()
            
            # Create a batch of requests
            task = asyncio.create_task(make_request(session, request_counter))
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
    print(f"Starting load test - {REQUESTS_PER_SECOND} requests/second for {TOTAL_DURATION} seconds")
    results = await run_load_test()
    
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