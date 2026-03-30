#!/bin/bash
echo "Testing AWS STS Get-Caller-Identity..."
aws sts get-caller-identity
if [ $? -ne 0 ]; then
    echo "[ERROR] AWS CLI not configured or role invalid."
    exit 1
fi
echo "[SUCCESS] AWS Role validated."
