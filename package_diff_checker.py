# package_diff_checker.py

import os
import difflib
from pathlib import Path
import argparse
import csv

def compare_files(file1, file2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
    return diff

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
            diff = compare_files(old_path, new_path)
            if diff:
                results.append([str(old_path), str(new_path), str(file), "Modification", f"{len(diff)} lines changed"])
        else:
            results.append([str(old_path), "N/A", str(file), "Removal", "File removed in new version"])

    # Check for additions
    for file in new_files - old_files:
        results.append(["N/A", str(new_dir / file), str(file), "Addition", "New file added"])

    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Old Version", "New Version", "File", "Category of Change", "Description"])
        writer.writerows(results)

    print(f"[✓] Report saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two versions of a package.")
    parser.add_argument("old_dir", help="Path to old version of the package")
    parser.add_argument("new_dir", help="Path to new version of the package")
    args = parser.parse_args()

    compare_directories(args.old_dir, args.new_dir)
