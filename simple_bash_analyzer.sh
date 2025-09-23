#!/bin/bash

echo "🔍 SIMPLE BASH SYNTAX ANALYZER"
echo "=============================="

total_errors=0

check_file() {
    local file="$1"
    local file_errors=0
    
    echo ""
    echo "📋 File: $file"
    echo "--------------------"
    
    # Pattern 1: Incomplete ${...} expansions
    local incomplete_braces=$(grep -n '\$\{[^}]*$' "$file" 2>/dev/null || true)
    if [[ -n "$incomplete_braces" ]]; then
        echo "❌ Incomplete variable expansion \${...}:"
        echo "$incomplete_braces"
        ((file_errors++))
    fi
    
    # Pattern 2: Incomplete $((...)) arithmetic  
    local incomplete_arith=$(grep -n '\$\(\([^)]*$' "$file" 2>/dev/null || true)
    if [[ -n "$incomplete_arith" ]]; then
        echo "❌ Incomplete arithmetic expansion \$((...):"
        echo "$incomplete_arith"
        ((file_errors++))
    fi
    
    # Pattern 3: Incomplete [[ conditions
    local incomplete_cond=$(grep -n 'if \[\[ [^]]*$' "$file" 2>/dev/null || true)
    if [[ -n "$incomplete_cond" ]]; then
        echo "❌ Incomplete conditional [[ ... ]]:"
        echo "$incomplete_cond"
        ((file_errors++))
    fi
    
    # Pattern 4: Incomplete [ conditions  
    local incomplete_test=$(grep -n 'if \[ [^]]*$' "$file" 2>/dev/null || true)
    if [[ -n "$incomplete_test" ]]; then
        echo "❌ Incomplete conditional [ ... ]:"
        echo "$incomplete_test"
        ((file_errors++))
    fi
    
    if [[ $file_errors -eq 0 ]]; then
        echo "✅ No syntax errors detected"
    else
        echo "❌ Found $file_errors syntax errors"
    fi
    
    total_errors=$((total_errors + file_errors))
    return $file_errors
}

# Check both workflow files
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [[ -f "$workflow" ]]; then
        check_file "$workflow"
    fi
done

echo ""
echo "🎯 SUMMARY: $total_errors total syntax errors found"

if [[ $total_errors -gt 0 ]]; then
    echo "❌ ANALYSIS FAILED - Syntax errors must be fixed before deployment"
    exit 1
else
    echo "✅ ANALYSIS PASSED - No syntax errors detected"
    exit 0
fi
