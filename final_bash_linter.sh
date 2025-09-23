#!/bin/bash

echo "🔍 PRODUCTION-READY BASH SYNTAX LINTER FOR WORKFLOWS"
echo "===================================================="
echo "Detects bash syntax errors that cause GitHub Actions failures"
echo ""

total_errors=0
total_warnings=0

analyze_bash_syntax() {
    local file="$1"
    local errors=0
    local warnings=0
    
    echo "📋 Analyzing: $file"
    echo "$(printf '%.50s' '------------------------------------------------')"
    
    # Critical Error 1: Incomplete variable expansions ${...
    local pattern1=$(grep -n '\$\{[^}]*$' "$file" 2>/dev/null || true)
    if [[ -n "$pattern1" ]]; then
        echo "❌ CRITICAL: Incomplete variable expansion \${...}"
        echo "$pattern1" | while read line; do echo "   $line"; done
        ((errors++))
    fi
    
    # Critical Error 2: Incomplete arithmetic $((...)
    local pattern2=$(grep -n '\$\(\([^)]*$' "$file" 2>/dev/null || true)
    if [[ -n "$pattern2" ]]; then
        echo "❌ CRITICAL: Incomplete arithmetic expansion \$((...))"
        echo "$pattern2" | while read line; do echo "   $line"; done
        ((errors++))
    fi
    
    # Critical Error 3: Incomplete [[ conditions
    local pattern3=$(grep -n 'if \[\[ [^]]*$' "$file" 2>/dev/null || true)
    if [[ -n "$pattern3" ]]; then
        echo "❌ CRITICAL: Incomplete conditional expression [[ ... ]]"
        echo "$pattern3" | while read line; do echo "   $line"; done
        ((errors++))
    fi
    
    # Critical Error 4: Incomplete [ conditions
    local pattern4=$(grep -n 'if \[ [^]]*$' "$file" 2>/dev/null || true)
    if [[ -n "$pattern4" ]]; then
        echo "❌ CRITICAL: Incomplete conditional expression [ ... ]"
        echo "$pattern4" | while read line; do echo "   $line"; done
        ((errors++))
    fi
    
    # Critical Error 5: Unmatched quotes in variable assignments (common pattern)
    local pattern5=$(grep -n '="[^"]*$' "$file" | grep -v '\\"$' | head -3 2>/dev/null || true)
    if [[ -n "$pattern5" ]]; then
        echo "⚠️  WARNING: Possible unclosed string assignments"
        echo "$pattern5" | while read line; do echo "   $line"; done
        ((warnings++))
    fi
    
    # Summary for this file
    if [[ $errors -eq 0 && $warnings -eq 0 ]]; then
        echo "✅ No issues found"
    elif [[ $errors -eq 0 ]]; then
        echo "⚠️  $warnings warning(s) found"
    else
        echo "❌ $errors critical error(s) and $warnings warning(s) found"
    fi
    
    total_errors=$((total_errors + errors))
    total_warnings=$((total_warnings + warnings))
    echo ""
}

# Find and analyze workflow files
workflow_count=0
for workflow_file in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [[ -f "$workflow_file" ]]; then
        analyze_bash_syntax "$workflow_file"
        ((workflow_count++))
    fi
done

if [[ $workflow_count -eq 0 ]]; then
    echo "📂 No workflow files found in .github/workflows/"
    exit 0
fi

# Final summary
echo "🎯 FINAL SUMMARY"
echo "================"
echo "Files analyzed: $workflow_count"
echo "Critical errors: $total_errors"
echo "Warnings: $total_warnings"
echo ""

if [[ $total_errors -gt 0 ]]; then
    echo "❌ LINTING FAILED"
    echo "   $total_errors critical bash syntax errors detected"
    echo "   These WILL cause workflow failures in GitHub Actions"
    echo "   Please fix all errors before committing"
    echo ""
    echo "💡 TIP: Use this linter as a pre-commit hook:"
    echo "   ln -s \$(pwd)/final_bash_linter.sh .git/hooks/pre-commit"
    exit 1
elif [[ $total_warnings -gt 0 ]]; then
    echo "⚠️  LINTING PASSED WITH WARNINGS"
    echo "   $total_warnings warnings detected"
    echo "   Review warnings to ensure they are intentional"
    exit 0
else
    echo "✅ LINTING PASSED"
    echo "   No bash syntax issues detected"
    echo "   Workflows should execute without syntax errors"
    exit 0
fi
