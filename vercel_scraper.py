import requests
import json
import time
from datetime import datetime
import os

def setup_output_file():
    """
    Create or get the output filename
    
    Returns:
        str: Filename for results
    """
    output_dir = 'search_results'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/output.json"
    
    # Initialize file if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    return filename

def setup_log_file():
    """
    Create or get the single log filename for all searches
    
    Returns:
        str: Filename for log
    """
    output_dir = 'search_results'
    os.makedirs(output_dir, exist_ok=True)
    
    log_filename = f"{output_dir}/scraper.log"
    
    return log_filename

def log_message(log_file, datetime_str, query, page, status, extra_info=""):
    """
    Write single-line message to log file
    
    Args:
        log_file (str): Log filename
        datetime_str (str): Datetime string (UTC)
        query (str): Search query
        page (int or str): Page number or status
        status (str): Status (SUCCESS, ERROR, RETRY, etc.)
        extra_info (str): Additional information
    """
    if extra_info:
        log_entry = f"{datetime_str} UTC | Query: {query} | Page: {page} | Status: {status} | {extra_info}\n"
    else:
        log_entry = f"{datetime_str} UTC | Query: {query} | Page: {page} | Status: {status}\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(log_entry.strip())

def extract_needed_fields(result):
    """
    Extract only the needed fields from a result entry
    
    Args:
        result (dict): Full result entry
    
    Returns:
        dict: Filtered result with only needed fields
    """
    agent = result.get('agent', {})
    
    return {
        'business_name': result.get('businessName', ''),
        'registration_id': result.get('registrationId', ''),
        'status': result.get('status', ''),
        'filing_date': result.get('filingDate', ''),
        'agent_name': agent.get('name', ''),
        'agent_address': agent.get('address', ''),
        'agent_email': agent.get('email', '')
    }

def append_results_to_file(filename, results):
    """
    Append new results to the JSON file
    
    Args:
        filename (str): Output filename
        results (list): List of filtered results to append
    """
    # Read existing data
    with open(filename, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    # Append new results
    existing_data.extend(results)
    
    # Write back
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

def fetch_page(query, page, session_id, log_file, max_retries=2):
    """
    Fetch a single page of search results with retry logic
    
    Args:
        query (str): Search query term
        page (int): Page number
        session_id (str): Search session ID
        log_file (str): Log file path
        max_retries (int): Maximum number of retries for non-session errors
    
    Returns:
        dict: JSON response from the API or None if error
        str: Error type ('timeout', '403', 'other', or None)
    """
    url = 'https://scraping-trial-test.vercel.app/api/search'
    
    params = {
        'q': query,
        'page': page
    }
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': f'https://scraping-trial-test.vercel.app/search/results?q={query}',
        'x-search-session': session_id
    }
    
    attempt = 0
    while attempt <= max_retries:
        try:
            datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Check for 403 status code specifically
            if response.status_code == 403:
                log_message(log_file, datetime_str, query, page, "ERROR", f"403 Forbidden - Session expired or ReCAPTCHA required")
                return None, '403'
            
            response.raise_for_status()
            
            data = response.json()
            
            # Check for recaptcha or session errors in response
            if 'error' in data:
                error_msg = data.get('error', '').lower()
                if 'recaptcha' in error_msg or 'session' in error_msg:
                    log_message(log_file, datetime_str, query, page, "ERROR", f"Session/ReCAPTCHA error: {data.get('error')}")
                    return None, '403'
            
            log_message(log_file, datetime_str, query, page, "SUCCESS", f"Retrieved {len(data.get('results', []))} results")
            return data, None
            
        except requests.exceptions.Timeout:
            datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if attempt >= max_retries:
                log_message(log_file, datetime_str, query, page, "ERROR", f"Timeout after {max_retries + 1} attempts")
                return None, 'timeout'
            log_message(log_file, datetime_str, query, page, "RETRY", f"Timeout, attempt {attempt + 1}/{max_retries + 1}")
            attempt += 1
            time.sleep(2)  # Wait before retry
            
        except requests.exceptions.RequestException as e:
            datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            error_str = str(e).lower()
            
            # Check if it's a 403 or recaptcha/session error
            if 'recaptcha' in error_str or 'session' in error_str or (hasattr(e, 'response') and e.response and e.response.status_code == 403):
                log_message(log_file, datetime_str, query, page, "ERROR", f"Session/ReCAPTCHA error: {e}")
                return None, '403'
            
            # Other errors - retry
            if attempt >= max_retries:
                log_message(log_file, datetime_str, query, page, "ERROR", f"Failed after {max_retries + 1} attempts: {e}")
                return None, 'other'
            log_message(log_file, datetime_str, query, page, "RETRY", f"Attempt {attempt + 1}/{max_retries + 1}: {e}")
            attempt += 1
            time.sleep(2)  # Wait before retry
    
    return None, 'other'

def fetch_all_pages(query, session_id, start_datetime, start_page=1, delay=1):
    """
    Fetch all pages of search results and append each page to file
    
    Args:
        query (str): Search query term
        session_id (str): Search session ID
        start_datetime (str): Start datetime string for filenames
        start_page (int): Starting page number (useful for resuming)
        delay (float): Delay between requests in seconds
    
    Returns:
        int: Total number of results collected
    """
    # Setup files
    output_file = setup_output_file()
    log_file = setup_log_file()
    
    print(f"Output file: {output_file}")
    print(f"Log file: {log_file}")
    print(f"Starting from page {start_page}\n")
    
    # Log session start
    datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    log_message(log_file, datetime_str, query, "START", "SESSION_START", f"Starting scrape for query: {query}")
    
    current_page = start_page
    total_pages = None
    total_results_collected = 0
    
    while True:
        # Fetch the page
        page_data, error_type = fetch_page(query, current_page, session_id, log_file)
        
        if page_data is None:
            if error_type == 'timeout' or error_type == '403':
                print("\n" + "="*60)
                print("SESSION EXPIRED OR TIMEOUT")
                print("Please provide a new session ID to continue.")
                print(f"Resume from page: {current_page}")
                print("="*60)
                
                # Ask for new session ID
                new_session_id = input("\nEnter new session ID (or 'quit' to stop): ").strip()
                
                if new_session_id.lower() == 'quit':
                    datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    log_message(log_file, datetime_str, query, current_page, "STOPPED", "User chose to quit")
                    break
                
                session_id = new_session_id
                datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                log_message(log_file, datetime_str, query, current_page, "NEW_SESSION", f"Entered new session ID, resuming from page {current_page}")
                continue
            else:
                datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                log_message(log_file, datetime_str, query, current_page, "STOPPED", "Failed after retries")
                break
        
        # Extract pagination info from first page
        if total_pages is None:
            total_pages = page_data.get('totalPages', 1)
            total_results = page_data.get('total', 0)
            print(f"Total pages: {total_pages}, Total results in database: {total_results}\n")
        
        # Extract and filter results
        raw_results = page_data.get('results', [])
        filtered_results = [extract_needed_fields(result) for result in raw_results]
        
        # Append to file immediately
        append_results_to_file(output_file, filtered_results)
        
        total_results_collected += len(filtered_results)
        print(f"Page {current_page} completed: {len(filtered_results)} results (Total so far: {total_results_collected})")
        
        # Check if we've reached the last page
        if current_page >= total_pages:
            datetime_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            log_message(log_file, datetime_str, query, f"1-{total_pages}", "COMPLETED", f"All pages fetched, total results: {total_results_collected}")
            print(f"\nCompleted! Fetched all {total_pages} pages.")
            break
        
        # Move to next page
        current_page += 1
        
        # Add delay to be respectful to the server
        if current_page <= total_pages:
            time.sleep(delay)
    
    return total_results_collected

def main():
    """
    Main function to run the scraper with user input
    """
    print("="*60)
    print("Web Scraper - Search Results Collector")
    print("="*60)
    
    # Get user input
    query = input("\nEnter search query: ").strip()
    if not query:
        print("Error: Query cannot be empty")
        return
    
    session_id = input("Enter session ID: ").strip()
    if not session_id:
        print("Error: Session ID cannot be empty")
        return
    
    start_page_input = input("Enter starting page (default: 1): ").strip()
    start_page = int(start_page_input) if start_page_input else 1
    
    delay_input = input("Enter delay between requests in seconds (default: 1): ").strip()
    delay = float(delay_input) if delay_input else 1.0
    
    # Generate start datetime for filenames (UTC)
    start_datetime = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "="*60)
    print("Starting scraper...")
    print("="*60 + "\n")
    
    # Run scraper
    total_collected = fetch_all_pages(
        query=query,
        session_id=session_id,
        start_datetime=start_datetime,
        start_page=start_page,
        delay=delay
    )
    
    print("\n" + "="*60)
    print("Scraping completed!")
    print(f"Total results collected: {total_collected}")
    print("="*60)

if __name__ == '__main__':
    main()