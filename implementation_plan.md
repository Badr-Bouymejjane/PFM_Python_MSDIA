# implementation_plan.md

# Goal
Execute the cleanup and project setup phase requested by the user. This involves consolidating scattered raw data, removing clutter, initializing version control, and creating documentation.

## User Review Required
- **Data Deletion**: The script `scripts/consolidate_data.py` will PERMANENTLY DELETE `raw_*.json` files after merging them.

## Proposed Changes

### Scripts
#### [NEW] [consolidate_data.py](file:///c:/Users/Badr/UB/0_Inbox/Full_PFM_Python/scripts/consolidate_data.py)
A one-off script to:
1. Glob `data/raw_coursera_*.json`.
2. Load and merge into `data/coursera_courses.json` (deduplicating by link).
3. Glob `data/raw_udemy_*.json`.
4. Load and merge into `data/udemy_courses.json` (deduplicating by link).
5. Delete the raw input files upon successful merge.

### Documentation
#### [NEW] [README.md](file:///c:/Users/Badr/UB/0_Inbox/Full_PFM_Python/README.md)
Project overview, installation instructions, usage guide, and features list.

#### [NEW] [project_docs.md](file:///c:/Users/Badr/UB/0_Inbox/Full_PFM_Python/project_docs.md)
More detailed developer documentation (architecture, file structure).

### Version Control
- Initialize `git` repository.
- Create `.gitignore` (ignoring `__pycache__`, `.env`, `.tmp`, but keeping `data/` as requested for sharing).

## Verification Plan

### Automated Tests
- Run `python scripts/consolidate_data.py` and verify:
    - `data/coursera_courses.json` exists and has data.
    - `data/udemy_courses.json` exists and has data.
    - `data/raw_*.json` files are gone.
- Run `python scripts/clean_data.py` to ensure the new JSON files are valid for processing.
- Run `python app.py` to ensure the dashboard still loads (sanity check).

### Manual Verification
- Check `README.md` for clarity.
- Check `git status` to ensure clean working tree.
