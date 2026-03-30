@echo off
echo Testing AWS STS Get-Caller-Identity...
aws sts get-caller-identity
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AWS CLI not configured or role invalid.
    exit /b 1
)
echo [SUCCESS] AWS Role validated.
