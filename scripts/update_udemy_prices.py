import pandas as pd
import json
import re

def clean_price(price_str):
    if not price_str or not isinstance(price_str, str):
        return None
    # Extract numeric values like $10.99
    match = re.search(r'\$?(\d+\.\d+|\d+)', price_str)
    if match:
        return match.group(0)
    return price_str

def update_prices():
    csv_path = 'processed_data/final_courses_shuffled.csv'
    json_path = 'data/raw_udemy.json'
    
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Check if 'price' column exists, if not add it
    if 'price' not in df.columns:
        df['price'] = None
    
    print(f"Reading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        udemy_data = json.load(f)
    
    # Create lookup map for Udemy courses
    # Keys: (title_lower, url) for exact matching
    udemy_lookup = {}
    for item in udemy_data:
        title = item.get('title', '').lower().strip()
        url = item.get('url', '').strip()
        price = clean_price(item.get('current_price'))
        
        if title and url:
            udemy_lookup[(title, url)] = price

    print("Matching and updating prices...")
    updated_count = 0
    
    # Filter for Udemy rows in CSV
    udemy_mask = df['source_domain'] == 'udemy'
    coursera_mask = df['source_domain'] == 'coursera'
    
    # Update Udemy prices
    for idx in df[udemy_mask].index:
        title = str(df.at[idx, 'title']).lower().strip()
        link = str(df.at[idx, 'link']).strip()
        
        # Try to match
        if (title, link) in udemy_lookup:
            df.at[idx, 'price'] = udemy_lookup[(title, link)]
            updated_count += 1
    
    # Update Coursera prices
    df.loc[coursera_mask, 'price'] = 'Inscrivez-vous gratuitement'
            
    print(f"Successfully updated {updated_count} Udemy courses with price data.")
    print(f"Updated {sum(coursera_mask)} Coursera courses with 'Free' label.")
    
    # Save back to CSV
    df.to_csv(csv_path, index=False)
    print(f"Saved changes to {csv_path}")

if __name__ == "__main__":
    update_prices()
