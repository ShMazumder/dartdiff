# package_diff_checker.py

import os
import difflib
from pathlib import Path
import argparse
import csv

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv("./env")

# Initialize Azure OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)


def compare_files(file1, file2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
    return diff, lines1, lines2

def get_all_files(base_dir):
    files = []
    for root, _, filenames in os.walk(base_dir):
        for name in filenames:
            full_path = Path(root) / name
            rel_path = full_path.relative_to(base_dir)
            files.append(rel_path)
    return files

def compare_directories(old_dir, new_dir, output_csv="diff_report.csv"):
    old_dir = Path(old_dir)
    new_dir = Path(new_dir)
    old_files = set(get_all_files(old_dir))
    new_files = set(get_all_files(new_dir))

    results = []

    # Check for modifications and removals
    for file in old_files:
        old_path = old_dir / file
        new_path = new_dir / file
        if new_path.exists():
            [diff, old_code, new_code] = compare_files(old_path, new_path)
            if diff:
                changes = analyze_changes_with_ai(old_code, new_code, diff)
                results.append([str(old_path), str(new_path), str(file), "Modification", f"{len(diff)} lines changed", changes])
        else:
            results.append([str(old_path), "N/A", str(file), "Removal", "File removed in new version", ''])

    # Check for additions
    for file in new_files - old_files:
        results.append(["N/A", str(new_dir / file), str(file), "Addition", "New file added", ''])

    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Old Version", "New Version", "File", "Category of Change", "Description", 'Diff'])
        writer.writerows(results)

    print(f"[✓] Report saved to {output_csv}")

def analyze_changes_with_ai(old_code, new_code, diff):
    """Query Azure OpenAI to categorize and describe changes"""
    prompt = f"""
    Compare these two versions of a python package source code and identify breaking API changes:
    
    OLD VERSION:
    {old_code[:2000]}... [truncated]
    
    NEW VERSION:
    {new_code[:2000]}... [truncated]
    
    Respond in this exact format:
    Category: [Parameter|Return Type|Function Removal|Data Structure|Dependency]
    Description: [concise technical description of the breaking change]
    Impact: [Low|Medium|High]
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical analyst specializing in API compatibility for Linux packages."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="gpt-4o-mini",
            temperature=0.3,  # Lower for more deterministic technical analysis
            max_tokens=500,
            top_p=0.9
        )
        return parse_ai_response(response.choices[0].message.content)
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return None

def parse_ai_response(response_text):
    """Extract structured data from AI response"""
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    result = {}
    
    for line in lines:
        if line.startswith("Category:"):
            result['category'] = line.split(":")[1].strip()
        elif line.startswith("Description:"):
            result['description'] = line.split(":")[1].strip()
        elif line.startswith("Impact:"):
            result['impact'] = line.split(":")[1].strip()
    
    return result if len(result) == 3 else None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two versions of a package.")
    parser.add_argument("old_dir", help="Path to old version of the package")
    parser.add_argument("new_dir", help="Path to new version of the package")
    args = parser.parse_args()

    compare_directories(args.old_dir, args.new_dir)
