
Write-Host "Setting up Git Repository..."

# 1. Initialize
if (-not (Test-Path .git)) {
    git init
    Write-Host "Initialized empty Git repository."
}

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial commit: Project cleanup and consolidation"

# 4. Rename branch to main
git branch -M main

# 5. Add Remote
# Remove existing origin if it exists to avoid errors on rerun
try {
    git remote remove origin 2>$null
} catch {}

git remote add origin git@github.com:Badr-Bouymejjane/PFM_Python_MSDIA.git
Write-Host "Added remote origin."

# 6. Push
Write-Host "Pushing to GitHub..."
git push -u origin main

Write-Host "Done!"
