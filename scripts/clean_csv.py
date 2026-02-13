import pandas as pd
import os

def clean_shuffled_csv():
    path = 'processed_data/final_courses_shuffled.csv'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    print(f"Cleaning {path}...")
    
    # Read lines manually to handle bad formatting
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    header = lines[0]
    cleaned_lines = [header]
    garbage_count = 0
    
    for line in lines[1:]:
        parts = line.strip().split(',')
        
        # Check if line is one of those "19.99$" repetitions
        if len(parts) >= 10 and all(p.strip() == '19.99$' or p.strip() == 'Inscrivez-vous gratuitement' for p in parts[:5]):
            garbage_count += 1
            continue
            
        # Basic validation: should have around 16 columns (the header has 16)
        # title,partner,rating,reviews,metadata,link,category,scraped_at,source_domain,num_ratings,duration_hours,level_enc,title_clean,popularity_score,id,price
        if len(parts) < 10:
            garbage_count += 1
            continue
            
        cleaned_lines.append(line)
        
    print(f"Removed {garbage_count} garbage lines.")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    # Verify with pandas
    try:
        df = pd.read_csv(path)
        print(f"Pandas verify: {len(df)} rows loaded successfully.")
    except Exception as e:
        print(f"Pandas still failing: {e}")

if __name__ == "__main__":
    clean_shuffled_csv()
