#!/usr/bin/env python3
"""
Prbal API Documentation Table of Contents Validator and Updater

This script validates and updates the Table of Contents in the Prbal-API.md file by:
1. Extracting all headings with their actual line numbers
2. Comparing TOC entries with actual headings
3. Marking entries as ✅ (found with correct line number) or ❌ (missing/incorrect)
4. Updating the original MD file with the corrected TOC
"""

import re
import os
from collections import defaultdict

class TocValidator:
    def __init__(self, filepath):
        self.filepath = filepath
        self.content_lines = []
        self.headings = []  # List of (level, title, status, line_num)
        self.toc_entries = []  # List of (title, anchor, line_num_in_toc, stated_line_num)
        self.toc_start_line = -1
        self.toc_end_line = -1
        self.missing_headings = []
        self.incorrect_line_numbers = []

    def load_file(self):
        """Load the markdown file content as lines"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content_lines = f.readlines()
            print(f"Successfully loaded file with {len(self.content_lines)} lines: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def extract_headings(self):
        """Extract all headings from the document with their line numbers"""
        heading_regex = r'^(#+)\s+(✅|❌)?\s*(.*?)(?:\(L-(\d+)\))?$'
        
        for i, line in enumerate(self.content_lines):
            heading_match = re.match(heading_regex, line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                status = heading_match.group(2) if heading_match.group(2) else None
                title = heading_match.group(3).strip()
                line_num = i + 1  # 1-based line numbering
                
                self.headings.append((level, title, status, line_num))
        
        print(f"Found {len(self.headings)} headings in the document")

    def find_toc_section(self):
        """Find the Table of Contents section in the document"""
        for i, line in enumerate(self.content_lines):
            if "## Table of Contents" in line:
                self.toc_start_line = i + 1  # Line after "## Table of Contents"
                break
        
        if self.toc_start_line == -1:
            print("Could not find Table of Contents section")
            return False
        
        # Find the end of TOC (next heading or blank line followed by heading)
        for i in range(self.toc_start_line, len(self.content_lines)):
            line = self.content_lines[i].strip()
            if line.startswith('#') or (not line and i+1 < len(self.content_lines) and self.content_lines[i+1].strip().startswith('#')):
                self.toc_end_line = i
                break
        
        if self.toc_end_line == -1:
            self.toc_end_line = len(self.content_lines)
        
        print(f"Table of Contents found from line {self.toc_start_line} to {self.toc_end_line}")
        return True

    def extract_toc_entries(self):
        """Extract all entries from the Table of Contents with any line numbers"""
        toc_entry_regex = r'^\s*-\s+\[(✅|❌)?\s*(.*?)\]\((.*?)\)(?:\(L-(\d+)\))?$'
        
        for i in range(self.toc_start_line, self.toc_end_line):
            line = self.content_lines[i].strip()
            toc_match = re.match(toc_entry_regex, line)
            
            if toc_match:
                status = toc_match.group(1) if toc_match.group(1) else None
                title = toc_match.group(2).strip()
                anchor = toc_match.group(3)
                line_ref = int(toc_match.group(4)) if toc_match.group(4) else None
                
                self.toc_entries.append({
                    'title': title,
                    'anchor': anchor,
                    'toc_line': i + 1,  # 1-based line numbering
                    'stated_line': line_ref,
                    'status': status,
                    'indent_level': len(line) - len(line.lstrip())
                })
        
        print(f"Found {len(self.toc_entries)} TOC entries")

    def validate_toc_entries(self):
        """Validate TOC entries against actual headings"""
        heading_map = {}
        for level, title, status, line_num in self.headings:
            heading_map[title.lower()] = line_num
        
        for entry in self.toc_entries:
            title_lower = entry['title'].lower()
            
            # Check if heading exists
            if title_lower not in heading_map:
                self.missing_headings.append(entry)
                entry['validation'] = '❌'  # Missing heading
                entry['actual_line'] = None
            else:
                actual_line = heading_map[title_lower]
                
                # Check if line number is correct
                if entry['stated_line'] is not None and entry['stated_line'] != actual_line:
                    self.incorrect_line_numbers.append((entry, actual_line))
                    entry['validation'] = '✅'  # Heading exists but line number is wrong
                else:
                    entry['validation'] = '✅'  # Heading exists with correct line number
                
                entry['actual_line'] = actual_line
        
        print(f"Found {len(self.missing_headings)} missing headings")
        print(f"Found {len(self.incorrect_line_numbers)} entries with incorrect line numbers")

    def generate_updated_toc(self):
        """Generate updated TOC content with validation status and correct line numbers"""
        updated_toc_lines = []
        
        for entry in self.toc_entries:
            indent = ' ' * entry['indent_level']
            line_suffix = f"(L-{entry['actual_line']})" if entry['actual_line'] else ""
            
            # Format: - [✅/❌ Title](#anchor)(L-123)
            toc_line = f"{indent}- [{entry['validation']} {entry['title']}]({entry['anchor']}){line_suffix}"
            updated_toc_lines.append(toc_line)
        
        return updated_toc_lines

    def update_file(self):
        """Update the original file with the corrected TOC"""
        updated_toc_lines = self.generate_updated_toc()
        
        # Replace TOC section in the original file
        new_content_lines = (
            self.content_lines[:self.toc_start_line] +
            [line + '\n' for line in updated_toc_lines] +
            self.content_lines[self.toc_end_line:]
        )
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_content_lines)
            print(f"Updated file saved to: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error saving updated file: {e}")
            return False

    def print_validation_report(self):
        """Print a validation report with details of missing/incorrect headings"""
        print("\n=== TOC Validation Report ===")
        print(f"Total TOC entries: {len(self.toc_entries)}")
        print(f"Missing headings: {len(self.missing_headings)}")
        print(f"Entries with incorrect line numbers: {len(self.incorrect_line_numbers)}")
        
        if self.missing_headings:
            print("\nMissing Headings:")
            for entry in self.missing_headings:
                print(f"  - {entry['title']} (in TOC at line {entry['toc_line']})")
        
        if self.incorrect_line_numbers:
            print("\nIncorrect Line Numbers:")
            for entry, actual_line in self.incorrect_line_numbers:
                print(f"  - {entry['title']}: stated L-{entry['stated_line']}, " +
                      f"actual L-{actual_line}")

    def validate_and_update(self):
        """Run the complete validation and update process"""
        if not self.load_file():
            return False
        
        self.extract_headings()
        
        if not self.find_toc_section():
            return False
        
        self.extract_toc_entries()
        self.validate_toc_entries()
        
        self.print_validation_report()
        
        if self.update_file():
            print("\n✅ Successfully updated the TOC in the original file.")
            return True
        
        return False

def main():
    """Main function to run the validator"""
    api_doc_path = os.path.abspath("postman/Prbal-API.md")
    validator = TocValidator(api_doc_path)
    validator.validate_and_update()

if __name__ == "__main__":
    main()
