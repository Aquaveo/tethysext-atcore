$sourcePath = "source"
$buildPath = "build/html"
$watchedDirectory = "/home/aquadev/tethysext-atcore/tethysext"

sphinx-autobuild $sourcePath $buildPath

function Watch-DirectoryRecursively($dir) {
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $dir
    $watcher.Filter = "*.py"  # Monitor Python files
    $watcher.IncludeSubdirectories = $true
    $watcher.EnableRaisingEvents = $true

    while ($true) {
        $event = Wait-Event -Timeout 1
        if ($event -ne $null) {
            Write-Host "Change detected in $dir. Rebuilding documentation..."
            sphinx-build $sourcePath $buildPath
            Remove-Event $event.SourceIdentifier
        }
    }
}

function Start-WatchRecursively {
    Watch-DirectoryRecursively $watchedDirectory
    $subdirs = Get-ChildItem -Path $watchedDirectory -Directory
    foreach ($subdir in $subdirs) {
        Watch-DirectoryRecursively $subdir.FullName
    }
}


Start-WatchRecursively





