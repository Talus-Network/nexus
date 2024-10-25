#!/bin/bash

# Step 0: Check ENV for PACKAGE_ID_FILE, if not set use default location
PACKAGE_ID_FILE="${PACKAGE_ID_FILE:-/shared/package-id.json}"

if [ ! -f "$PACKAGE_ID_FILE" ]; then
    echo "Package ID file not found. Proceeding to publish package."

    # Step 1: Navigate to /opt/sui/onchain
    cd /opt/sui/onchain || { echo "Failed to navigate to /opt/sui/onchain"; exit 1; }

    # Step 2: Run the sui client publish command and extract the package_id
    PACKAGE_ID=$(sui client publish --skip-dependency-verification --json | jq -r '.objectChanges[] | select(.type == "published") | .packageId')

    # Step 3: Save the package_id to /opt/sui/onchain/package-id.json
    if [ "$PACKAGE_ID" != "null" ] && [ -n "$PACKAGE_ID" ]; then
        echo "[\"$PACKAGE_ID\"]" > "$PACKAGE_ID_FILE"
        echo "Package ID saved to $PACKAGE_ID_FILE"
    else
        echo "Failed to extract a valid package ID"
        exit 1
    fi
else
    echo "Package ID file already exists. No action taken."
fi
