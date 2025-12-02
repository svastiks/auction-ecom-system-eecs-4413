#!/usr/bin/env python3
"""
Simple load test script using Python requests library.
Generates performance data for response time vs arrival rate.
Can be used if JMeter is not available.
"""

import requests
import time
import threading
import statistics
from collections import defaultdict
from datetime import datetime
import json
import sys

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Graphs will not be generated.")


class LoadTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def make_request(self, endpoint, method="GET", **kwargs):
        """Make a single HTTP request."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        # Extract headers if provided
        headers = kwargs.pop('headers', {})
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5, headers=headers, **kwargs)
            elif method == "POST":
                json_data = kwargs.pop('json', None)
                response = requests.post(url, json=json_data, timeout=5, headers=headers, **kwargs)
            else:
                response = requests.request(method, url, timeout=5, headers=headers, **kwargs)
            
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            return {
                'status_code': response.status_code,
                'elapsed_ms': elapsed,
                'success': response.status_code < 400,
                'endpoint': endpoint
            }
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return {
                'status_code': 0,
                'elapsed_ms': elapsed,
                'success': False,
                'error': str(e),
                'endpoint': endpoint
            }
    
    def get_test_data(self):
        """Get valid IDs from API for testing endpoints that require them."""
        test_data = {
            'auction_ids': [],
            'item_ids': [],
            'auth_token': None,
        }
        
        try:
            # Get catalogue items to find item_ids
            response = requests.get(f"{self.base_url}/api/v1/catalogue/items?limit=10", timeout=5)
            if response.status_code == 200:
                items = response.json()
                test_data['item_ids'] = [item.get('item_id') for item in items if item.get('item_id')]
            
            # Search for auctions to get auction_ids (use a generic keyword)
            search_response = requests.post(
                f"{self.base_url}/api/v1/auction/search",
                json={"keyword": "a", "skip": 0, "limit": 10},
                timeout=5
            )
            if search_response.status_code == 200:
                search_data = search_response.json()
                test_data['auction_ids'] = [item.get('auction_id') for item in search_data.get('items', []) if item.get('auction_id')]
            else:
                # Try without keyword (optional parameter)
                try:
                    search_response2 = requests.post(
                        f"{self.base_url}/api/v1/auction/search",
                        json={"skip": 0, "limit": 10},
                        timeout=5
                    )
                    if search_response2.status_code == 200:
                        search_data = search_response2.json()
                        test_data['auction_ids'] = [item.get('auction_id') for item in search_data.get('items', []) if item.get('auction_id')]
                except:
                    pass
            
            # Try to login with test credentials (may not exist, that's ok)
            try:
                login_response = requests.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": "user", "password": "12345678a!"},
                    timeout=5
                )
                if login_response.status_code == 200:
                    test_data['auth_token'] = login_response.json().get('access_token')
                    print(f"  ✓ Login successful")
            except Exception as e:
                print(f"  ⚠ Login failed: {e}")
                
        except Exception as e:
            print(f"Warning: Could not fetch test data: {e}")
        
        return test_data
    
    def run_load_test(self, arrival_rate, duration=60, endpoints=None, test_data=None):
        """Run load test at specified arrival rate for duration seconds."""
        if endpoints is None:
            # Default endpoints - some may return 404 if IDs don't exist, that's ok for load testing
            endpoints = [
                ("/health", "GET"),
                ("/api/v1/", "GET"),
                ("/api/v1/catalogue/items?limit=20", "GET"),
                ("/api/v1/catalogue/categories", "GET"),
                ("/api/v1/auction/search", "POST", {"json": {"keyword": "test", "skip": 0, "limit": 20}}),
            ]
            
            # Add endpoints that need IDs if we have them
            if test_data:
                # Add auction search (public, no auth needed) - use valid keyword
                endpoints.append(("/api/v1/auction/search", "POST", {"json": {"keyword": "a", "skip": 0, "limit": 20}}))
                
                # Add auction detail endpoints if we have IDs
                for auction_id in test_data.get('auction_ids', [])[:2]:  # Use max 2 IDs
                    if auction_id:
                        endpoints.append((f"/api/v1/auction/{auction_id}", "GET"))
                        endpoints.append((f"/api/v1/auction/{auction_id}/bids", "GET"))
                
                # Add item detail endpoints if we have IDs
                for item_id in test_data.get('item_ids', [])[:2]:  # Use max 2 IDs
                    if item_id:
                        endpoints.append((f"/api/v1/auction/items/{item_id}", "GET"))
                
                # Add auth endpoints
                endpoints.append(("/api/v1/auth/login", "POST", {"json": {"username": "user", "password": "12345678a!"}}))
                
                # Add authenticated endpoints if we have token
                if test_data.get('auth_token'):
                    headers = {"Authorization": f"Bearer {test_data['auth_token']}"}
                    endpoints.append(("/api/v1/users/me/bids", "GET", {"headers": headers}))
                    endpoints.append(("/api/v1/orders", "GET", {"headers": headers}))
        
        results = []
        stop_time = time.time() + duration
        request_interval = 1.0 / arrival_rate
        
        def worker():
            while time.time() < stop_time:
                for endpoint_config in endpoints:
                    if isinstance(endpoint_config, tuple):
                        if len(endpoint_config) == 2:
                            endpoint, method = endpoint_config
                            kwargs = {}
                        elif len(endpoint_config) == 3:
                            endpoint, method, kwargs = endpoint_config
                        else:
                            continue
                    else:
                        continue
                    
                    result = self.make_request(endpoint, method, **kwargs)
                    result['timestamp'] = time.time()
                    results.append(result)
                    time.sleep(request_interval)
        
        # Start threads (one thread per request per second)
        threads = []
        for _ in range(min(arrival_rate, 10)):  # Limit threads
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        return results
    
    def calculate_stats(self, results):
        """Calculate statistics from results."""
        if not results:
            return {}
        
        response_times = [r['elapsed_ms'] for r in results if r['success']]
        errors = [r for r in results if not r['success']]
        
        if not response_times:
            return {
                'mean': 0,
                'median': 0,
                'p95': 0,
                'p99': 0,
                'error_rate': 100.0,
                'throughput': 0
            }
        
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        return {
            'mean': statistics.mean(sorted_times),
            'median': sorted_times[n // 2] if n > 0 else 0,
            'p95': sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0],
            'p99': sorted_times[int(n * 0.99)] if n > 1 else sorted_times[-1],
            'min': min(sorted_times),
            'max': max(sorted_times),
            'error_rate': (len(errors) / len(results)) * 100 if results else 0,
            'throughput': len(response_times) / (results[-1]['timestamp'] - results[0]['timestamp']) if len(results) > 1 else 0,
            'total_requests': len(results),
            'successful_requests': len(response_times),
            'failed_requests': len(errors)
        }
    
    def generate_report(self, all_results, output_dir="results"):
        """Generate performance report and graphs."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Aggregate results by arrival rate
        summary = []
        for arrival_rate, results in all_results.items():
            stats = self.calculate_stats(results)
            summary.append({
                'arrival_rate': arrival_rate,
                **stats
            })
        
        # Save summary to JSON
        with open(f"{output_dir}/performance_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate markdown report
        report = self.generate_markdown_report(summary)
        with open(f"{output_dir}/performance_report.md", 'w') as f:
            f.write(report)
        
        # Generate graph if matplotlib is available
        if HAS_MATPLOTLIB and summary:
            self.generate_graph(summary, output_dir)
        
        return summary
    
    def generate_markdown_report(self, summary):
        """Generate markdown performance report."""
        report = "# Performance Test Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "## Response Time as Function of Arrival Rate\n\n"
        report += "| Arrival Rate (req/s) | Mean RT (ms) | Median RT (ms) | P95 RT (ms) | P99 RT (ms) | Error Rate (%) | Throughput (req/s) |\n"
        report += "|---------------------|--------------|----------------|-------------|-------------|----------------|-------------------|\n"
        
        for item in summary:
            report += f"| {item['arrival_rate']} | {item['mean']:.2f} | {item['median']:.2f} | "
            report += f"{item['p95']:.2f} | {item['p99']:.2f} | "
            report += f"{item['error_rate']:.2f} | {item['throughput']:.2f} |\n"
        
        return report
    
    def generate_graph(self, summary, output_dir):
        """Generate response time vs arrival rate graph."""
        rates = [s['arrival_rate'] for s in summary]
        mean_rts = [s['mean'] for s in summary]
        p95_rts = [s['p95'] for s in summary]
        p99_rts = [s['p99'] for s in summary]
        
        plt.figure(figsize=(10, 6))
        plt.plot(rates, mean_rts, 'o-', label='Mean Response Time', linewidth=2, markersize=6)
        plt.plot(rates, p95_rts, 's-', label='P95 Response Time', linewidth=2, markersize=6)
        plt.plot(rates, p99_rts, '^-', label='P99 Response Time', linewidth=2, markersize=6)
        plt.xlabel('Arrival Rate (requests/second)', fontsize=12, fontweight='bold')
        plt.ylabel('Response Time (milliseconds)', fontsize=12, fontweight='bold')
        plt.title('Response Time as a Function of Arrival Rate', fontsize=14, fontweight='bold')
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.xscale('log')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/response_time_vs_arrival_rate.png", dpi=300, bbox_inches='tight')
        print(f"✓ Graph saved to {output_dir}/response_time_vs_arrival_rate.png")
        plt.close()


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Allow shorter test duration for quick verification
    quick_test = "--quick" in sys.argv or "-q" in sys.argv
    if quick_test:
        arrival_rates = [1, 5]  # Just test 2 rates quickly
        test_duration = 5  # 5 seconds per test
        print("🧪 QUICK TEST MODE: Short duration for endpoint verification")
    else:
        arrival_rates = [1, 5, 10, 25, 50, 100]
        test_duration = 30  # seconds per test
    
    print(f"Starting load tests against {base_url}")
    print(f"Test duration: {test_duration}s per arrival rate")
    print(f"Arrival rates: {arrival_rates}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"ERROR: Server returned status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to server at {base_url}")
        print(f"Error: {e}")
        sys.exit(1)
    
    tester = LoadTester(base_url)
    
    # Get test data (IDs, auth tokens) before running tests
    print("Fetching test data (auction IDs, item IDs, auth tokens)...")
    test_data = tester.get_test_data()
    print(f"  Found {len(test_data.get('auction_ids', []))} auction IDs")
    print(f"  Found {len(test_data.get('item_ids', []))} item IDs")
    if test_data.get('auth_token'):
        print(f"  Authentication token obtained")
    print()
    
    all_results = {}
    
    for rate in arrival_rates:
        print(f"Testing at {rate} req/s...", end=" ", flush=True)
        results = tester.run_load_test(rate, duration=test_duration, test_data=test_data)
        all_results[rate] = results
        stats = tester.calculate_stats(results)
        print(f"✓ Mean RT: {stats['mean']:.2f}ms, Error Rate: {stats['error_rate']:.2f}%")
    
    print("\nGenerating report...")
    summary = tester.generate_report(all_results)
    
    print("\n✓ Performance test complete!")
    print(f"  Report: results/performance_report.md")
    print(f"  Data: results/performance_summary.json")
    if HAS_MATPLOTLIB:
        print(f"  Graph: results/response_time_vs_arrival_rate.png")


if __name__ == "__main__":
    main()

