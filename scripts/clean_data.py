
import os
import json
import glob
import pandas as pd
import re
import numpy as np

# CONFIG
DATA_DIR = "data"
OUTPUT_PARQUET = os.path.join(DATA_DIR, "final_courses.parquet")
OUTPUT_CSV = os.path.join(DATA_DIR, "final_courses.csv")

def parse_reviews(val):
    """Parses '43K reviews' or '(123)' or 'N/A' into integer."""
    if pd.isna(val) or val == "N/A" or val == "":
        return 0
    
    val = str(val).lower().replace(",", "").replace("reviews", "").replace("ratings", "").strip("()")
    
    try:
        if "k" in val:
            return int(float(val.replace("k", "")) * 1000)
        if "m" in val:
            return int(float(val.replace("m", "")) * 1000000)
        return int(float(val))
    except:
        return 0

def parse_duration(val):
    """Parses '16.5 total hours' or '1 - 3 Months' into hours (approx)."""
    if pd.isna(val) or val == "N/A":
        return None
    val = str(val).lower()
    
    # Check for hours
    hours_match = re.search(r"(\d+(\.\d+)?)\s*total hours", val)
    if hours_match:
        return float(hours_match.group(1))
    
    # Check for months (Coursera often says '1 - 3 Months')
    # Assume 1 month ~ 4 weeks ~ 16 hours/week? Hard to guess.
    # Let's assume a standard 10 hours per 'Month' roughly for metadata purposes if not specified
    if "month" in val:
        # crude approximation: 1 month = 20 hours
        return 20.0
    
    if "week" in val:
        # 1 week = 5 hours
        return 5.0
        
    return None

def parse_level(val):
    """Encodes level: Beginner=1, Intermediate=2, Advanced=3, Mixed=0."""
    if pd.isna(val): return 0
    val = str(val).lower()
    
    if "beginner" in val: return 1
    if "intermediate" in val: return 2
    if "advanced" in val: return 3
    if "expert" in val: return 3
    return 0 # All Levels or Unknown

def clean_data():
    print("--- Starting Data Cleaning ---")
    
    # 1. Load Data
    # 1. Load Data
    files_to_load = {
        "coursera": os.path.join(DATA_DIR, "coursera_courses.json"),
        "udemy": os.path.join(DATA_DIR, "udemy_courses.json")
    }
    
    dfs = []
    for source, filepath in files_to_load.items():
        if os.path.exists(filepath):
            print(f"Loading {source} from {filepath}...")
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if data:
                        temp_df = pd.DataFrame(data)
                        temp_df["source_domain"] = source
                        dfs.append(temp_df)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
        else:
            print(f"Warning: File not found: {filepath}")

            
    if not dfs:
        print("No data found!")
        return

    df = pd.concat(dfs, ignore_index=True)
    initial_count = len(df)
    print(f"Loaded {initial_count} raw records.")
    
    # 2. Deduplicate
    # Drop duplicates by URL first
    df = df.drop_duplicates(subset=["link"])
    print(f"Removed {initial_count - len(df)} duplicates (based on URL). New count: {len(df)}")
    
    # 3. Normalize Columns
    
    # Rating
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    
    # Reviews
    df["num_ratings"] = df["reviews"].apply(parse_reviews)
    
    # Duration
    df["duration_hours"] = df["metadata"].apply(parse_duration).fillna(0.0)
    
    # Level (Encoded)
    df["level_enc"] = df["metadata"].apply(parse_level)
    
    # Title Cleaning
    df["title_clean"] = df["title"].str.lower().str.replace(r"[^\w\s]", "", regex=True)
    
    # Popularity Score (Simple heuristic: rating * log(1 + reviews))
    df["popularity_score"] = df["rating"] * np.log1p(df["num_ratings"])
    
    # ID Generation
    df["id"] = df.index.astype(str)
    
    # 4. Save
    print("Saving processed data...")
    # df.to_parquet(OUTPUT_PARQUET) # Missing dependencies
    df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Success! Saved {len(df)} cleaned records to {OUTPUT_CSV}")
    print(df[["title", "source_domain", "rating", "num_ratings", "duration_hours"]].head(10))

if __name__ == "__main__":
    clean_data()
