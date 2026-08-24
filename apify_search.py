import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv("APIFY_TOKEN"))


# Prepare the Actor input without None fields that trigger validation errors
run_input = {
    "urls": [], 
    "keywords": "fresher B.Tech IT",
    "location": "India",
    "datePosted": "pastMonth", 
    "companyIds": [],
    "under10Applicants": False,
    "autoConvertToAiSearch": True,
    "scrapeCompany": False,
    "limitPerSource": 20, 
    "splitByLocation": False,
}

print("Starting the Apify Actor (hKByXkMQaC5Qt9UMN)...")
try:
    # Run the Actor and wait for it to finish
    run = client.actor("hKByXkMQaC5Qt9UMN").call(run_input=run_input)
    print(f"Actor run finished! Status: {run['status']}")
    print(f"Dataset ID: {run['defaultDatasetId']}")
    
    # Fetch and print Actor results
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"\nFound {len(items)} jobs:")
    
    # Save the results in a JSON file
    import json
    with open("scraped_jobs.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4, ensure_ascii=False)
        
    for idx, item in enumerate(items, 1):
        title = item.get("title", "No Title")
        # Try different possible structures of Apify output
        company = item.get("companyName") or item.get("company", {}).get("name") or "Unknown Company"
        location = item.get("location") or "Unknown Location"
        url = item.get("url") or item.get("link") or ""
        post_date = item.get("postedAt") or item.get("postDate") or "Unknown Date"
        
        print(f"{idx}. {title} at {company}")
        print(f"   Location: {location}")
        print(f"   Posted: {post_date}")
        print(f"   URL: {url}")
        print("-" * 40)
        
except Exception as e:
    print(f"An error occurred: {e}")
