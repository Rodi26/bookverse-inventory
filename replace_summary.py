#!/usr/bin/env python3
import sys

def replace_summary_step():
    with open('.github/workflows/ci.yml', 'r') as f:
        lines = f.readlines()
    
    # Find the start and end of the summary step
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if 'Enhanced Build Summary (bookverse-devops pattern)' in line:
            start_line = i
        elif start_line is not None and 'force_app_version=true' in line and 'create an application version' in line:
            end_line = i
            break
    
    if start_line is None or end_line is None:
        print("Could not find summary step boundaries")
        return False
    
    print(f"Replacing lines {start_line + 1} to {end_line + 1}")
    
    # Read the new step content
    with open('enhanced_summary_step.txt', 'r') as f:
        new_step = f.read()
    
    # Replace the section
    new_lines = lines[:start_line] + [new_step + '\n'] + lines[end_line + 1:]
    
    # Write back
    with open('.github/workflows/ci.yml', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Summary step replaced successfully")
    return True

if __name__ == '__main__':
    replace_summary_step()
