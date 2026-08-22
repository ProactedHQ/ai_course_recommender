#!/usr/bin/env python3
"""
Improved KUCCPS Institutions Scraper (2026)
============================================
Uses BeautifulSoup for reliable parsing with pagination support.
Fetches ALL ~499 institutions from https://students.kuccps.net/institutions/

Usage:
    python scrape_kuccps_institutions.py

Output:
    institutions_data.json - Contains all scraped institution data
"""

import json
import sys
import requests
from bs4 import BeautifulSoup
import warnings

# Suppress InsecureRequestWarning when accessing sites with SSL certificate issues
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_URL = "https://students.kuccps.net/institutions/"


def scrape_all_institutions():
    """
    Scrapes all institutions from KUCCPS website with pagination support.
    
    Returns:
        list: List of institution dictionaries
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    })
    
    institutions = []
    page = 1
    
    print("🌐 Starting scrape of all institutions...")
    print(f"   URL: {BASE_URL}\n")
    
    try:
        while True:
            print(f"   📄 Fetching page {page}...", end=" ")
            
            # Fetch page (disable SSL verification for government sites with cert issues)
            # Note: verify=False is needed because of SSL certificate issues with Kenyan govt sites
            params = {'page': page} if page > 1 else {}
            response = session.get(BASE_URL, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table
            table = soup.find('table')
            if not table:
                print("⚠️")
                print("   ⚠️  No table found—site structure may have changed")
                break
            
            # Get all rows (skip header row)
            rows = table.find_all('tr')[1:]
            if not rows:
                print("(no data)")
                break
            
            page_added = 0
            for row in rows:
                cells = row.find_all('td')
                
                # Expected columns: #, KEY, NAME, CATEGORY, INST_TYPE, PARENT, LOCATION
                if len(cells) < 7:
                    continue
                
                # Extract and clean cell data (skip the # column)
                clean_cells = [cell.get_text(strip=True) for cell in cells[1:]]
                
                code, name, category, inst_type_raw, parent, location = clean_cells
                
                # Skip invalid entries
                if not code or not name:
                    continue
                
                # Map institution type to our model choices
                # Model expects: PUBLIC, PRIVATE, TVET
                inst_type = 'TVET'  # Default
                
                if 'University' in category:
                    if 'Public' in inst_type_raw:
                        inst_type = 'PUBLIC'
                    elif 'Private' in inst_type_raw:
                        inst_type = 'PRIVATE'
                elif 'Public' in inst_type_raw and 'University' in inst_type_raw:
                    inst_type = 'PUBLIC'
                elif 'Private' in inst_type_raw and 'University' in inst_type_raw:
                    inst_type = 'PRIVATE'
                
                institutions.append({
                    'code': code,
                    'name': name,
                    'category': category,
                    'institution_type': inst_type,
                    'parent_ministry': parent,
                    'location': location
                })
                page_added += 1
            
            print(f"✓ ({page_added} institutions)")
            
            # Check for next page button
            next_btn = soup.find('a', string='Next')
            if not next_btn or 'disabled' in next_btn.get('class', []):
                print("\n   ℹ️  No more pages found")
                break
            
            page += 1
        
        print(f"\n✅ Successfully scraped {len(institutions)} institutions total")
        return institutions
        
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out")
        print("   Network issue or server unresponsive")
        return get_fallback_institutions()
    
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        return get_fallback_institutions()
    
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        return get_fallback_institutions()
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("   Falling back to hardcoded data...")
        return get_fallback_institutions()


def get_fallback_institutions():
    """
    Returns hardcoded fallback institution data if scraping fails.
    
    Returns:
        list: List of institution dictionaries
    """
    print("\n⚠️  Using fallback data (21 institutions)")
    return [
        {"code": "UON", "name": "University of Nairobi", "institution_type": "PUBLIC", "location": "Nairobi", "category": "Public University"},
        {"code": "KU", "name": "Kenyatta University", "institution_type": "PUBLIC", "location": "Nairobi", "category": "Public University"},
        {"code": "JKUAT", "name": "Jomo Kenyatta University of Agriculture and Technology", "institution_type": "PUBLIC", "location": "Juja", "category": "Public University"},
        {"code": "MOI", "name": "Moi University", "institution_type": "PUBLIC", "location": "Eldoret", "category": "Public University"},
        {"code": "EGU", "name": "Egerton University", "institution_type": "PUBLIC", "location": "Njoro", "category": "Public University"},
        {"code": "MASENO", "name": "Maseno University", "institution_type": "PUBLIC", "location": "Maseno", "category": "Public University"},
        {"code": "MMU", "name": "Multimedia University of Kenya", "institution_type": "PUBLIC", "location": "Nairobi", "category": "Public University"},
        {"code": "TUK", "name": "Technical University of Kenya", "institution_type": "PUBLIC", "location": "Nairobi", "category": "Public University"},
        {"code": "TUM", "name": "Technical University of Mombasa", "institution_type": "PUBLIC", "location": "Mombasa", "category": "Public University"},
        {"code": "DKUT", "name": "Dedan Kimathi University of Technology", "institution_type": "PUBLIC", "location": "Nyeri", "category": "Public University"},
        {"code": "STRATH", "name": "Strathmore University", "institution_type": "PRIVATE", "location": "Nairobi", "category": "Private University"},
        {"code": "USIU", "name": "United States International University - Africa", "institution_type": "PRIVATE", "location": "Nairobi", "category": "Private University"},
        {"code": "CUEA", "name": "Catholic University of Eastern Africa", "institution_type": "PRIVATE", "location": "Nairobi", "category": "Private University"},
        {"code": "DAYSTAR", "name": "Daystar University", "institution_type": "PRIVATE", "location": "Nairobi", "category": "Private University"},
        {"code": "KABARAK", "name": "Kabarak University", "institution_type": "PRIVATE", "location": "Nakuru", "category": "Private University"},
        {"code": "KABETE", "name": "Kabete National Polytechnic", "institution_type": "TVET", "location": "Nairobi", "category": "TVET"},
        {"code": "NAIROBI_TTI", "name": "Nairobi Technical Training Institute", "institution_type": "TVET", "location": "Nairobi", "category": "TVET"},
        {"code": "RVTTI", "name": "Rift Valley Technical Training Institute", "institution_type": "TVET", "location": "Eldoret", "category": "TVET"},
        {"code": "KENYA_POLY", "name": "Kenya Coast National Polytechnic", "institution_type": "TVET", "location": "Mombasa", "category": "TVET"},
        {"code": "MERU_POLY", "name": "Meru National Polytechnic", "institution_type": "TVET", "location": "Meru", "category": "TVET"},
        {"code": "KMTC", "name": "Kenya Medical Training College", "institution_type": "TVET", "location": "Nairobi", "category": "TVET"},
    ]


def save_to_json(data, filename="institutions_data.json"):
    """
    Saves institution data to JSON file.
    
    Args:
        data (list): List of institution dictionaries
        filename (str): Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {filename}")


def display_sample(data, num=5):
    """
    Displays sample institutions for verification.
    
    Args:
        data (list): List of institution dictionaries
        num (int): Number of samples to display
    """
    print(f"\n📋 Sample institutions (first {min(num, len(data))} of {len(data)}):")
    print("-" * 80)
    
    for i, inst in enumerate(data[:num], 1):
        print(f"\n{i}. {inst['name']}")
        print(f"   Code: {inst['code']}")
        print(f"   Type: {inst['institution_type']}")
        print(f"   Location: {inst['location']}")
        print(f"   Category: {inst.get('category', 'N/A')}")


def display_statistics(data):
    """
    Displays statistics about scraped institutions.
    
    Args:
        data (list): List of institution dictionaries
    """
    from collections import Counter
    
    print(f"\n📊 Statistics:")
    print("-" * 80)
    print(f"   Total Institutions: {len(data)}")
    
    # Count by type
    types = Counter(inst['institution_type'] for inst in data)
    print(f"\n   By Type:")
    for inst_type, count in types.items():
        print(f"     • {inst_type}: {count}")
    
    # Count by location (top 10)
    locations = Counter(inst['location'] for inst in data)
    print(f"\n   Top 10 Locations:")
    for location, count in locations.most_common(10):
        print(f"     • {location}: {count}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("KUCCPS Institutions Scraper (BeautifulSoup Edition)")
    print("=" * 80 + "\n")
    
    # Scrape institutions
    institutions = scrape_all_institutions()
    
    if not institutions:
        print("\n❌ No data scraped. Exiting.")
        sys.exit(1)
    
    # Save to JSON
    save_to_json(institutions)
    
    # Display samples and statistics
    display_sample(institutions)
    display_statistics(institutions)
    
    print("\n" + "=" * 80)
    print("✅ Scraping Complete!")
    print("=" * 80 + "\n")
    
    # Warn if we didn't get close to expected number
    if len(institutions) < 400:
        print("⚠️  WARNING: Expected ~499 institutions, but only got", len(institutions))
        print("   This might indicate:")
        print("   • Pagination didn't work correctly")
        print("   • Site structure has changed")
        print("   • Network issues during scraping")
        print()
    
    print("Next steps:")
    print("1. Review 'institutions_data.json' to verify data accuracy")
    print("2. If count looks good (~499), run: python manage.py seed_data")
    print()
