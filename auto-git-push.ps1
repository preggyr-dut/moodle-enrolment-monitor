# auto-git-push.ps1
Set-Location -Path "C:\moodle-enrolment-monitor"

# Run your Python update script
python .\deploy_monitor.py update

# Add all changes (including new files)
git add -A

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    # Commit with timestamp
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Automated daily update: $date"
    
    # Push to remote
    git push origin main
    
    Write-Host "Changes committed and pushed successfully at $date" -ForegroundColor Green
} else {
    Write-Host "No changes to commit at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
}