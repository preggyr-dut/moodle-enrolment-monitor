# auto-git-push-with-logging.ps1
$logFile = "C:\moodle-enrolment-monitor\git-automation.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$message)
    "$timestamp - $message" | Out-File -FilePath $logFile -Append
    Write-Host $message
}

try {
    Set-Location -Path "C:\moodle-enrolment-monitor"
    Write-Log "Starting automated git push"
    
    # Run Python update
    Write-Log "Running deploy_monitor.py update"
    python .\deploy_monitor.py update 2>&1 | Out-File -FilePath $logFile -Append
    
    # Add all changes
    git add -A
    
    # Check status
    $status = git status --porcelain
    if ($status) {
        $commitMsg = "Automated daily update: $timestamp"
        git commit -m $commitMsg
        
        # Push changes
        git push origin main 2>&1 | Out-File -FilePath $logFile -Append
        Write-Log "Successfully committed and pushed changes"
    } else {
        Write-Log "No changes to commit"
    }
    
    Write-Log "Process completed successfully"
} catch {
    Write-Log "ERROR: $_"
}