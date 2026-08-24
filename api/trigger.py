from http.server import BaseHTTPRequestHandler
import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Read APIFY_TOKEN from environment variables
        apify_token = os.getenv("APIFY_TOKEN")
        client = ApifyClient(apify_token)
        
        run_input = {
            "urls": [], 
            "keywords": "fresher B.Tech (software OR analyst OR developer OR trainee OR GET OR associate)",
            "location": "India",
            "datePosted": "past24Hours", 
            "companyIds": [],
            "under10Applicants": False,
            "autoConvertToAiSearch": True,
            "scrapeCompany": False,
            "limitPerSource": 27, 
            "splitByLocation": False,
        }
        
        try:
            # Start the actor asynchronously to return immediately under Vercel's 10s timeout limit
            # This triggers the scraper in the cloud
            client.actor("hKByXkMQaC5Qt9UMN").start(run_input=run_input)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Apify Scraper triggered successfully!")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Failed to trigger scraper: {e}".encode())
