import os
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")       # e.g., yourgmail@gmail.com
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "") # Your App Password (not your main password)
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", SENDER_EMAIL)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

client = ApifyClient(APIFY_TOKEN)
ACTOR_ID = "hKByXkMQaC5Qt9UMN"

def load_sent_jobs():
    """Load previously emailed job IDs to prevent duplicate notifications"""
    if os.path.exists("sent_jobs.json"):
        try:
            with open("sent_jobs.json", "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_sent_jobs(sent_jobs):
    """Save emailed job IDs to sent_jobs.json"""
    try:
        with open("sent_jobs.json", "w") as f:
            json.dump(list(sent_jobs), f)
    except Exception as e:
        print(f"Failed to save sent jobs list: {e}")

def is_relevant_job(job):
    """Filter out senior roles, check IT relevance, and ensure job was posted in the last 24h"""
    title = job.get("title", "").lower()
    
    # 1. Strict Date Check (Today or Yesterday only)
    posted_at_str = job.get("postedAt") or job.get("postDate") or ""
    if not posted_at_str:
        return False
    try:
        # Apify date format is usually YYYY-MM-DD
        posted_date = datetime.strptime(posted_at_str[:10], "%Y-%m-%d").date()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        if posted_date not in [today, yesterday]:
            return False
    except Exception:
        return False

    # 2. Exclude senior/experienced roles
    senior_keywords = ["senior", "sr.", "lead", "manager", "director", "architect", "principal", "expert", "5+ years", "3+ years"]
    if any(word in title for word in senior_keywords):
        return False
        
    # 3. Exclude non-IT/Network roles
    role_keywords = ["software", "developer", "engineer", "analyst", "trainee", "get", "programmer", "it", "tech", "data", "qa", "test", "cloud", "associate", "intern", "system", "operations", "support", "network", "networking"]
    if not any(word in title for word in role_keywords):
        return False
        
    return True

def run_scraper_and_email():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching Apify scraper with refined filters...")
    
    run_input = {
        "urls": [], 
        "keywords": "fresher B.Tech (software OR analyst OR developer OR trainee OR GET OR associate OR network OR networking OR cloud)",
        "location": "India",
        "datePosted": "past24Hours", # Retrieve only jobs posted in the past 24 hours
        "companyIds": [],
        "under10Applicants": False,
        "autoConvertToAiSearch": True,
        "scrapeCompany": False,
        "limitPerSource": 27, # Max jobs to scrape per run to stay within free tier budget
        "splitByLocation": False,
    }

    try:
        # Run Actor
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        if run.get("status") != "SUCCEEDED":
            print(f"Scraper did not succeed. Status: {run.get('status')}")
            return
        
        # Get dataset items
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            print("No jobs found in the last 24 hours.")
            return
        
        # Load previously sent job IDs
        sent_jobs = load_sent_jobs()
        
        # Apply local relevancy filters and filter out already sent jobs
        new_jobs = []
        for job in items:
            job_id = str(job.get("id"))
            if job_id not in sent_jobs and is_relevant_job(job):
                new_jobs.append(job)
                sent_jobs.add(job_id)
        
        print(f"Scraped {len(items)} raw jobs, {len(new_jobs)} are new and passed the fresher IT filter.")
        if new_jobs:
            send_jobs_email(new_jobs)
            save_sent_jobs(sent_jobs)
        else:
            print("No new relevant fresher IT jobs remained after filtering.")
        
    except Exception as e:
        print(f"Error during scraper/email execution: {e}")


def send_jobs_email(jobs):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("SMTP Credentials not configured. Skipping email sending.")
        print(f"Jobs scraped count: {len(jobs)}")
        return

    # Parse multiple recipients
    receivers = [r.strip() for r in RECEIVER_EMAIL.split(",") if r.strip()]
    if not receivers:
        print("No valid receiver emails found.")
        return

    # Build Email Body
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"LinkedIn Fresher IT Jobs Update - {datetime.now().strftime('%d %b %Y')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(receivers)

    html_content = """
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; }
          .job-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
          .job-title { color: #0073b1; font-size: 18px; font-weight: bold; text-decoration: none; }
          .job-meta { color: #555; font-size: 14px; margin-top: 5px; }
          .apply-btn { display: inline-block; padding: 8px 15px; background-color: #0073b1; color: #fff; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 10px; }
        </style>
      </head>
      <body>
        <h2>New B.Tech IT Fresher Job Openings in India</h2>
        <p>Here are the latest jobs scraped from LinkedIn:</p>
    """

    for job in jobs:
        title = job.get("title", "No Title")
        company = job.get("companyName") or job.get("company", {}).get("name") or "Unknown Company"
        location = job.get("location") or "Unknown Location"
        url = job.get("url") or job.get("link") or "#"
        posted = job.get("postedAt") or job.get("postDate") or "Recent"

        html_content += f"""
        <div class="job-card">
          <a class="job-title" href="{url}">{title}</a>
          <div class="job-meta">
            <strong>Company:</strong> {company} | <strong>Location:</strong> {location}<br>
            <strong>Posted:</strong> {posted}
          </div>
          <a class="apply-btn" href="{url}">View Job & Apply</a>
        </div>
        """

    html_content += """
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, 'html'))

    # SMTP Send
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receivers, msg.as_string())
        print(f"Email sent successfully to {len(receivers)} recipients!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def run_scheduler_loop():
    print("Scheduler loop started. Monitoring active times...")
    print("Schedule: Tuesday, Wednesday, Thursday at 10:00 AM, 1:00 PM, and 6:00 PM.")
    
    # Track the last execution hour and day to prevent multiple runs within the same hour window
    last_run_day = -1
    last_run_hour = -1

    while True:
        now = datetime.now()
        day_of_week = now.weekday()  # Monday is 0, Tuesday is 1, Wednesday is 2, Thursday is 3, Friday is 4...
        hour = now.hour
        minute = now.minute

        # Check if day is Tuesday (1), Wednesday (2), or Thursday (3)
        if day_of_week in [1, 2, 3]:
            # Target hours: 10:00 AM (10), 1:00 PM (13), 6:00 PM (18)
            if hour in [10, 13, 18] and minute >= 0:
                # Prevent running multiple times in the same hour window
                if last_run_day != day_of_week or last_run_hour != hour:
                    run_scraper_and_email()
                    last_run_day = day_of_week
                    last_run_hour = hour
                    
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    run_scheduler_loop()
