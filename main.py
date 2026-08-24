from fastmcp import FastMCP
import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("mcp-linkedin")
logger = logging.getLogger(__name__)

def get_host():
    """Returns the configured RapidAPI host name"""
    return os.getenv("RAPIDAPI_HOST", "linkedin-job-search-api.p.rapidapi.com")

def get_client():
    """Returns an httpx client configured for the LinkedIn Data API"""
    headers = {
        'x-rapidapi-key': os.getenv("RAPIDAPI_KEY"),
        'x-rapidapi-host': get_host()
    }
    return httpx.Client(headers=headers)

@mcp.tool()
def search_jobs(keywords: str, limit: int = 10, location: str = 'Israel', format_output: bool = True) -> dict:
    """
    Search for jobs on LinkedIn and return as a dictionary.
    
    :param keywords: Job search keywords
    :param limit: Maximum number of job results
    :param location: Location filter
    :param format_output: Whether to return formatted string or raw dictionary
    :return: Dictionary of job listings or formatted string
    """
    host = get_host()
    client = get_client()
    
    if host == "linkedin-job-search-api.p.rapidapi.com":
        # Format the query parameters
        encoded_keywords = keywords.replace(" ", "%20")
        encoded_location = location.replace(" ", "%20")
        
        url = f"https://{host}/active-jb?title={encoded_keywords}&location={encoded_location}"
        
        try:
            response = client.get(url)
            print(f"Status code: {response.status_code}")
            
            data = response.json()
            if isinstance(data, dict) and not data.get("success", True):
                error_msg = f"API Error: {data.get('message', 'Unknown error')}"
                return {"error": error_msg} if not format_output else error_msg
            
            jobs_list = []
            raw_jobs = data if isinstance(data, list) else data.get("jobs", [])
            for job in raw_jobs[:limit]:
                job_dict = {
                    "id": str(job.get("id")),
                    "title": job.get("title", "Unknown Title"),
                    "company": job.get("organization", "Unknown Company"),
                    "company_logo": job.get("org_logo_permalink"),
                    "location": job.get("location", "Unknown Location"),
                    "url": job.get("url", ""),
                    "post_date": job.get("posted_at", "Unknown Date"),
                    "reference_id": None
                }
                jobs_list.append(job_dict)
            
            result = {
                "query": {
                    "keywords": keywords,
                    "location": location
                },
                "count": len(jobs_list),
                "jobs": jobs_list
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error: {e}")
            error_msg = f"Error searching jobs: {e}"
            return {"error": error_msg} if not format_output else error_msg
    else:
        location_id = search_locations(location)

        # Format the query parameters
        encoded_keywords = keywords.replace(" ", "%20")
        encoded_location = location_id.replace(" ", "%20")
        
        url = f"https://{host}/search-jobs?keywords={encoded_keywords}&locationId={encoded_location}&datePosted=pastMonth&sort=mostRelevant"
        
        try:
            response = client.get(url)
            print(f"Status code: {response.status_code}")
            
            data = response.json()
            
            if not data.get("success"):
                error_msg = f"API Error: {data.get('message', 'Unknown error')}"
                return {"error": error_msg} if not format_output else error_msg
            
            # Store jobs in a list of dictionaries
            jobs_list = []
            for job in data.get("data", [])[:limit]:
                job_dict = {
                    "id": job.get("id"),
                    "title": job.get("title", "Unknown Title"),
                    "company": job.get("company", {}).get("name", "Unknown Company"),
                    "company_logo": job.get("company", {}).get("logo"),
                    "location": job.get("location", "Unknown Location"),
                    "url": job.get("url", ""),
                    "post_date": job.get("postAt", "Unknown Date"),
                    "reference_id": job.get("referenceId")
                }
                jobs_list.append(job_dict)
            
            result = {
                "query": {
                    "keywords": keywords,
                    "location": location
                },
                "count": len(jobs_list),
                "jobs": jobs_list
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error: {e}")
            error_msg = f"Error searching jobs: {e}"
            return {"error": error_msg} if not format_output else error_msg
        

@mcp.tool()
def get_job_details(job_id: str) -> str:
    """
    Get detailed information about a specific LinkedIn job posting.
    
    :param job_id: The LinkedIn job ID
    :return: Detailed job information
    """
    host = get_host()
    client = get_client()
    
    if host == "linkedin-job-search-api.p.rapidapi.com":
        url = f"https://{host}/job/detail?job_id={job_id}"
    else:
        url = f"https://{host}/get-job-details?id={job_id}"
    
    try:
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        
        data = response.json()
        if host == "linkedin-job-search-api.p.rapidapi.com":
            return data
        else:
            if not data.get("success"):
                return f"API Error: {data.get('message', 'Unknown error')}"
            
            job_data = data.get("data", {})
            return job_data
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error fetching job details: {e}"
    
@mcp.tool()
def search_locations(keyword: str) -> str:
    """
    Search for LinkedIn location IDs by keyword.
    
    :param keyword: Location keyword to search for
    :return: ID of the first matching location or the keyword itself
    """
    host = get_host()
    if host == "linkedin-job-search-api.p.rapidapi.com":
        return keyword

    client = get_client()
    
    # Format the query parameter
    encoded_keyword = keyword.replace(" ", "%20")
    
    url = f"https://{host}/search-locations?keyword={encoded_keyword}"
    
    try:
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        
        data = response.json()
        
        if not data.get("success"):
            return f"API Error: {data.get('message', 'Unknown error')}"
        
        items = data.get("data", {}).get("items", [])
        
        if not items:
            return f"No locations found matching '{keyword}'"
        
        # Get the first location's ID
        first_location = items[0]
        full_id = first_location.get("id", "")
        
        # Extract the numeric ID from "urn:li:geo:104243116" format
        if ":" in full_id:
            location_id = full_id.split(":")[-1]
        else:
            location_id = full_id
        print(f"Location ID: {location_id}")
        return location_id
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error searching locations: {e}"

    
if __name__ == "__main__":
    mcp.run(transport='stdio')
