
import os
import json
import glob

# CONFIG
DATA_DIR = "data"

def consolidate_files(source_name, pattern):
    print(f"--- Consolidating {source_name} ---")
    files = glob.glob(os.path.join(DATA_DIR, pattern))
    
    if not files:
        print(f"No files found matching {pattern}")
        return

    merged_data = []
    seen_links = set()
    
    # Load existing master file if it exists to preserve data
    master_file = os.path.join(DATA_DIR, f"{source_name}_courses.json")
    if os.path.exists(master_file):
        try:
            with open(master_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
                print(f"Loaded {len(existing)} existing records from {master_file}")
                for item in existing:
                    merged_data.append(item)
                    seen_links.add(item.get('link'))
        except Exception as e:
            print(f"Error reading existing master file: {e}")

    # Process new files
    files_processed = 0
    for file_path in files:
        if os.path.normpath(file_path) == os.path.normpath(master_file):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            count = 0
            for item in data:
                link = item.get('link')
                if link and link not in seen_links:
                    merged_data.append(item)
                    seen_links.add(link)
                    count += 1
            
            print(f"Merged {count} new records from {os.path.basename(file_path)}")
            files_processed += 1
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Save Master File
    print(f"Saving {len(merged_data)} total records to {master_file}...")
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2)

    # Delete processed files
    print("Deleting raw files...")
    for file_path in files:
        if os.path.normpath(file_path) != os.path.normpath(master_file):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
    
    print(f"Completed {source_name}. Processed {files_processed} files.\n")

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found.")
        return

    # Consolidate Coursera
    consolidate_files("coursera", "raw_coursera_*.json")
    
    # Consolidate Udemy
    consolidate_files("udemy", "raw_udemy_*.json")
    
    print("All consolidation complete.")

if __name__ == "__main__":
    main()
