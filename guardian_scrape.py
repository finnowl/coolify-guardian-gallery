import requests
import json
import re
import os

# The series page you want to track
SERIES_URL = 'https://www.theguardian.com/news/series/ten-best-photographs-of-the-day'

def get_recent_article_ids(url, num_articles=3):
    """
    Step 1: Scrapes the series page to find the most recent gallery URLs.
    """
    print(f"Scraping {url} for the latest galleries...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to load page: {e}")
        return []

    # Regex to find links containing /gallery/ or /pictures/
    pattern = r'href="([^"]*(?:/gallery/|/pictures/)[^"]*)"'
    raw_urls = re.findall(pattern, response.text)

    article_ids = []

    for raw_url in raw_urls:
        # Clean the URL
        article_id = raw_url.replace('https://www.theguardian.com', '')
        article_id = article_id.split('?')[0].split('#')[0].strip('/')

        if article_id and article_id not in article_ids:
            article_ids.append(article_id)
            print(f"Found gallery: {article_id}")

        if len(article_ids) >= num_articles:
            break

    return article_ids

def extract_photos_from_article(article_id):
    """
    Step 2: Downloads the article's webpage and extracts the photos using regex.
    Includes data cleaning for captions, credits, and iPad-optimized resolutions.
    """
    print(f"  -> Extracting photos from HTML: {article_id}")
    url = f"https://www.theguardian.com/{article_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

        photos_data = []
        seen_urls = set()

        # Grab everything inside every <figure> on the page.
        figures = re.findall(r'<figure[^>]*>(.*?)</figure>', html, re.DOTALL)

        for fig in figures:
            # Look for Guardian image CDN URLs inside the figure
            img_matches = re.findall(r'(https://i\.guim\.co\.uk/img/media/[^"\'\s]+)', fig)

            if img_matches:
                raw_img_url = img_matches[-1].replace('&amp;', '&')

                # --- ADJUSTMENT 2: Set width to 2000 for Guardian CDN max ---
                img_url = re.sub(r'width=\d+', 'width=2000', raw_img_url)

                # Base URL for deduplication
                base_url = img_url.split('?')[0]

                if base_url not in seen_urls:
                    seen_urls.add(base_url)

                    # Extract the caption (with fallback)
                    caption_match = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', fig, re.DOTALL)
                    raw_caption = caption_match.group(1) if caption_match else ""

                    # If figcaption is empty, fallback to the image alt text
                    if not raw_caption or raw_caption.strip() == "":
                        alt_match = re.search(r'<img[^>]*alt="([^"]+)"', fig)
                        if alt_match:
                            raw_caption = alt_match.group(1)

                    if raw_caption:
                        # Replace HTML tags with a SPACE to prevent words from mashing together
                        clean_caption = re.sub(r'<[^>]+>', ' ', raw_caption).strip()
                        # Clean up erratic spaces/newlines
                        clean_caption = re.sub(r'\s+', ' ', clean_caption)
                    else:
                        clean_caption = "No caption provided"

                    # Separate the credit from the caption
                    credit = ""

                    # Quietly remove the stray "Share" button text from the end if it exists
                    clean_caption = re.sub(r'\s*Share\s*$', '', clean_caption)

                    # Search for Photograph:, Image:, or Credit: near the end of the text
                    credit_match = re.search(r'(?:Photograph|Image|Credit):\s*(.*)$', clean_caption, flags=re.IGNORECASE)

                    if credit_match:
                        # Save the credit part
                        credit = credit_match.group(1).strip()
                        # Erase the credit part from the main caption
                        clean_caption = re.sub(r'\s*(?:Photograph|Image|Credit):\s*.*$', '', clean_caption, flags=re.IGNORECASE).strip()

                    # --- NEW ADJUSTMENT: Ensure the caption ends with a full stop ---
                    if clean_caption and not clean_caption.endswith(('.', '!', '?')):
                        clean_caption += '.'

                    # Add the source URL and save
                    photos_data.append({
                        'url': img_url,
                        'caption': clean_caption,
                        'credit': credit,
                        'source_url': url
                    })

        print(f"     Found {len(photos_data)} photos in this article.")
        return photos_data

    except Exception as e:
        print(f"  -> Error fetching webpage for {article_id}: {e}")
        return []

# --- Main Script Execution ---

if __name__ == "__main__":
    latest_ids = get_recent_article_ids(SERIES_URL, num_articles=3)

    all_photos = []

    json_path = "latest_guardian_photos.json"

    if latest_ids:
        for article_id in latest_ids:
            photos = extract_photos_from_article(article_id)
            all_photos.extend(photos)

        if all_photos:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(all_photos, f, indent=4, ensure_ascii=False)
            print(f"\nSuccess! Saved a total of {len(all_photos)} photos to 'photos.json'")
        else:
            print("\nNo photos could be extracted from the articles.")
    else:
        print("\nCould not find any gallery links on that page.")