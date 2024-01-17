import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Set up logging
logging.basicConfig(level=logging.INFO)


# Function to scrape quotes from a page and write to CSV
async def scrape_page(session, url, csv_writer):
    try:
        logging.info(f"Scraping {url}")
        html_content = await fetch_page(url)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract quotes based on the provided HTML structure
        quote_elements = soup.select('.entry-summary p')
        for quote_element in quote_elements:
            quote_text = quote_element.text.strip()

            # Extract additional details
            post_title = soup.select_one('.blog-entry-title a').text.strip()
            author = soup.select_one('.author-name').text.strip()

            # Check if the date element exists
            date_element = soup.select_one('time', class_='entry-date published')
            date_published = date_element.get('datetime') if date_element else None

            # Log the details
            logging.info(f"Quote: {quote_text}")
            logging.info(f"Title: {post_title}")
            logging.info(f"Author: {author}")
            logging.info(f"Date Published: {date_published}")

            # Write to CSV file
            csv_writer.writerow([quote_text, post_title, author, date_published])

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")


# Function to fetch HTML content of a page using Selenium
async def fetch_page(url):
    options = Options()
    options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    options.add_argument('--no-sandbox')  # Disable sandboxing for Linux
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        await asyncio.sleep(5)  # Give time for dynamic content to load (adjust as needed)
        content = driver.page_source
    finally:
        driver.quit()

    return content


# Function to scrape multiple pages of a website
async def scrape_website(base_url, max_pages):
    async with aiohttp.ClientSession() as session:
        csv_filename = 'quotes_selenium.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write the header row to the CSV file
            csv_writer.writerow(['Quote', 'Title', 'Author', 'Date Published'])

            tasks = []

            # Loop through pages and create tasks for scraping each page
            for page_num in range(1, max_pages + 1):
                url = f"{base_url}/page/{page_num}"
                task = scrape_page(session, url, csv_writer)
                tasks.append(task)

            # Execute tasks concurrently
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Set the base URL and the maximum number of pages to scrape
    base_url = "http://quotesnhumor.com"
    max_pages = 5  # number of pages to scrape

    # Set up and run the asyncio event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(scrape_website(base_url, max_pages))
    finally:
        loop.close()
