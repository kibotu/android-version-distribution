#!/usr/bin/env python3
"""
Updates the embedded CSV data in index.html with the latest android_versions_report.csv
"""

import re
from pathlib import Path

def update_html_with_csv():
    """Update the embedded CSV data in index.html"""
    
    script_dir = Path(__file__).parent
    csv_file = script_dir / 'android_versions_report.csv'
    html_file = script_dir / 'index.html'
    
    # Read CSV data
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    csv_content = csv_file.read_text()
    
    # Remove Property ID line for security (keep only in source CSV)
    csv_lines = csv_content.split('\n')
    filtered_lines = [line for line in csv_lines if not line.strip().startswith('# Property ID:')]
    csv_content = '\n'.join(filtered_lines)
    
    # Read HTML file
    if not html_file.exists():
        print(f"❌ HTML file not found: {html_file}")
        return False
    
    html_content = html_file.read_text()
    
    # Pattern to match the embedded CSV data section
    # Match the opening tag, any whitespace/content, and the closing tag
    pattern = r'(<script type="text/plain" id="csvData">\s*)(.*?)(\s*</script>)'
    
    # Replace the CSV data
    def replace_csv(match):
        return f'<script type="text/plain" id="csvData">\n{csv_content.strip()}\n</script>'
    
    updated_html = re.sub(pattern, replace_csv, html_content, flags=re.DOTALL, count=1)
    
    # Check if replacement was successful
    if updated_html == html_content:
        print("⚠️  Warning: CSV data section not found in HTML file")
        return False
    
    # Write updated HTML
    html_file.write_text(updated_html)
    print(f"✓ Updated embedded CSV data in {html_file.name}")
    return True

if __name__ == '__main__':
    success = update_html_with_csv()
    exit(0 if success else 1)

