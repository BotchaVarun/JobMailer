import os
import json
from main import search_jobs, search_locations

def main():
    print("Searching for India location ID...")
    india_id = search_locations("India")
    print(f"Found location ID for India: {india_id}")
    
    # We will search with keywords targeting IT freshers with B.Tech
    keywords_list = [
        "fresher btech IT",
        "btech fresher software engineer",
        "entry level IT developer India"
    ]
    
    for kw in keywords_list:
        print(f"\nSearching jobs with keywords: '{kw}' in India...")
        result = search_jobs(keywords=kw, limit=10, location="India", format_output=False)
        
        if isinstance(result, dict) and "error" in result:
            print(f"Error searching for '{kw}': {result['error']}")
        elif isinstance(result, str):
            print(f"Error string returned: {result}")
        else:
            print(f"Found {result.get('count', 0)} jobs:")
            for idx, job in enumerate(result.get("jobs", []), 1):
                print(f"{idx}. {job['title']} at {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Date: {job['post_date']}")
                print(f"   URL: {job['url']}")
                print("-" * 40)

if __name__ == "__main__":
    main()
