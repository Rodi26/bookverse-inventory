#!/bin/bash

echo "🔍 COMPREHENSIVE BASH SYNTAX ANALYZER FOR GITHUB WORKFLOWS"
echo "=========================================================="

error_count=0
warning_count=0

# Function to analyze a single workflow file
analyze_workflow() {
    local file="$1"
    echo ""
    echo "📋 Analyzing: $file"
    echo "----------------------------------------"
    
    local file_errors=0
    
    # 1. Check for incomplete variable expansions ${...
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]]; then
            echo "❌ SYNTAX ERROR (Line $line_num): Incomplete variable expansion \${...}"
            echo "   Content: ${content}"
            ((file_errors++))
        fi
    done < <(grep -n '\$\{[^}]*$' "$file" 2>/dev/null || true)
    
    # 2. Check for incomplete arithmetic expansions $((..
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]]; then
            echo "❌ SYNTAX ERROR (Line $line_num): Incomplete arithmetic expansion \$((...))"
            echo "   Content: ${content}"
            ((file_errors++))
        fi
    done < <(grep -n '\$\(\([^)]*$' "$file" 2>/dev/null || true)
    
    # 3. Check for incomplete conditional expressions [[ ...
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]]; then
            echo "❌ SYNTAX ERROR (Line $line_num): Incomplete conditional [[ ... ]]"
            echo "   Content: ${content}"
            ((file_errors++))
        fi
    done < <(grep -n 'if \[\[ [^]]*$' "$file" 2>/dev/null || true)
    
    # 4. Check for incomplete single bracket conditions [ ...
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]]; then
            echo "❌ SYNTAX ERROR (Line $line_num): Incomplete conditional [ ... ]"
            echo "   Content: ${content}"
            ((file_errors++))
        fi
    done < <(grep -n 'if \[ [^]]*$' "$file" 2>/dev/null || true)
    
    # 5. Check for potentially incomplete string literals (warnings)
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]] && [[ ! "$content" =~ \\\"$ ]]; then
            echo "⚠️  WARNING (Line $line_num): Possible unclosed string literal"
            echo "   Content: ${content}"
            ((warning_count++))
        fi
    done < <(grep -n '"[^"]*$' "$file" 2>/dev/null | head -5 || true)
    
    # 6. Check for unmatched parentheses in command substitutions
    while IFS=: read -r line_num content; do
        if [[ -n "$line_num" ]]; then
            echo "❌ SYNTAX ERROR (Line $line_num): Unmatched parentheses in command substitution"
            echo "   Content: ${content}"
            ((file_errors++))
        fi
    done < <(grep -n '\$([^)]*$' "$file" 2>/dev/null || true)
    
    error_count=$((error_count + file_errors))
    
    if [[ $file_errors -eq 0 ]]; then
        echo "✅ No syntax errors found in $file"
    else
        echo "❌ Found $file_errors syntax errors in $file"
    fi
}

# Find and analyze all workflow files
workflow_files=()
while IFS= read -r -d '' file; do
    workflow_files+=("$file")
done < <(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | sort -z)

if [[ ${#workflow_files[@]} -eq 0 ]]; then
    echo "📂 No workflow files found in .github/workflows/"
    exit 0
fi

echo "📁 Found ${#workflow_files[@]} workflow file(s) to analyze"

for file in "${workflow_files[@]}"; do
    analyze_workflow "$file"
done

echo ""
echo "🎯 SUMMARY"
echo "=========="
echo "Workflow files analyzed: ${#workflow_files[@]}"
echo "Total syntax errors: $error_count"
echo "Total warnings: $warning_count"

if [[ $error_count -gt 0 ]]; then
    echo ""
    echo "❌ FAILED: Found $error_count bash syntax errors that will cause workflow failures"
    echo "   Please fix these errors before committing or deploying workflows"
    exit 1
elif [[ $warning_count -gt 0 ]]; then
    echo ""
    echo "⚠️  WARNINGS: Found $warning_count potential issues"
    echo "   Review warnings to ensure they are intentional"
    exit 0
else
    echo ""
    echo "✅ SUCCESS: No bash syntax errors detected"
    echo "   All workflow files appear to have valid bash syntax"
    exit 0
fi
