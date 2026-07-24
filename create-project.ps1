# Create directories
$directories = @(
    "application/app",
    "application/tests",
    "helm",
    "terraform",
    "argocd",
    "monitoring"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

# Create files
$files = @(
    "application/app/main.py",
    "application/app/__init__.py",
    "application/tests/test_main.py",
    "application/requirements.txt",
    "application/Dockerfile",
    "application/.dockerignore",
    "Jenkinsfile"
)

foreach ($file in $files) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

Write-Host "Project structure created successfully."