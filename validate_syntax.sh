#!/bin/bash
# Extract just the summary step and validate its syntax

# Find start and end lines of the summary step
start_line=$(grep -n "Enhanced Build Summary with Accurate Reporting" .github/workflows/ci.yml | cut -d: -f1)
end_line=$((start_line + 200))  # Approximate end

echo "Extracting summary step from line $start_line..."

# Extract the run: | section
sed -n "${start_line},${end_line}p" .github/workflows/ci.yml | \
  sed -n '/run: |/,/^[[:space:]]*$/p' > temp_script.sh

echo "Checking syntax of extracted script..."
bash -n temp_script.sh 2>&1 || echo "Syntax errors found"

rm -f temp_script.sh
