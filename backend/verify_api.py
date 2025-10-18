#!/usr/bin/env python3
"""
API Verification Script
This script verifies that all authentication endpoints are properly configured.
"""

import requests
import json
from typing import Dict, Any

def test_api_endpoints():
    """Test that all API endpoints are accessible."""
    base_url = "http://localhost:8000"
    
    print("Verifying API Endpoints...")
    print("=" * 50)
    
    # Test basic API health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("Health check endpoint working")
        else:
            print(f"Health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Cannot connect to API: {e}")
        print("Make sure the server is running: uvicorn app.main:app --reload")
        return False
    
    # Test API root
    try:
        response = requests.get(f"{base_url}/api/v1/", timeout=5)
        if response.status_code == 200:
            print("API v1 root endpoint working")
        else:
            print(f"API v1 root failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"API v1 root failed: {e}")
        return False
    
    # Test OpenAPI documentation
    try:
        response = requests.get(f"{base_url}/api/v1/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            # Check for required authentication endpoints
            auth_endpoints = [
                "/auth/signup",
                "/auth/login", 
                "/auth/password/forgot",
                "/auth/password/reset",
                "/auth/logout"
            ]
            
            # Check for required user endpoints
            user_endpoints = [
                "/users/me",
                "/users/me/addresses"
            ]
            
            print("\nAuthentication Endpoints:")
            for endpoint in auth_endpoints:
                if endpoint in paths:
                    print(f"{endpoint}")
                else:
                    print(f"{endpoint} - Missing")
            
            print("\n👤 User Management Endpoints:")
            for endpoint in user_endpoints:
                if endpoint in paths:
                    print(f"{endpoint}")
                else:
                    print(f"{endpoint} - Missing")
            
            print(f"\nTotal endpoints documented: {len(paths)}")
            
        else:
            print(f"OpenAPI documentation failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"OpenAPI documentation failed: {e}")
        return False
    
    print("\nAPI verification complete!")
    return True

if __name__ == "__main__":
    test_api_endpoints()
