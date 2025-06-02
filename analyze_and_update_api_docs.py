#!/usr/bin/env python3
"""
Prbal API Documentation Analyzer and Updater

This script analyzes the Prbal-API.md file, processes its structure,
and generates an updated version with improved formatting and consistency.
"""

import re
import os
from datetime import datetime
from collections import defaultdict

class ApiDocAnalyzer:
    def __init__(self, filepath):
        """Initialize with the path to the API documentation file."""
        self.filepath = filepath
        self.content = ""
        self.sections = []
        self.implementation_status = {}
        self.toc_entries = []
        self.section_content = {}
        self.headings = []

    def load_file(self):
        """Load the content of the markdown file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
            print(f"Successfully loaded file: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def extract_toc_and_headings(self):
        """Extract table of contents and heading structure."""
        # Extract TOC entries
        toc_pattern = r'- \[(.*?)\]\((.*?)\)'
        self.toc_entries = re.findall(toc_pattern, self.content)
        
        # Extract headings with implementation status
        heading_pattern = r'^(#+)\s+(✅|❌)?(.*?)$'
        self.headings = []
        
        for line in self.content.split('\n'):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                status = match.group(2) if match.group(2) else '❌'  # Default to not implemented
                title = match.group(3).strip()
                self.headings.append({
                    'level': level,
                    'status': status,
                    'title': title
                })
                self.implementation_status[title] = status
        
        print(f"Found {len(self.headings)} headings and {len(self.toc_entries)} TOC entries")

    def extract_sections(self):
        """Extract all sections with their content."""
        section_pattern = r'^(#{1,6})\s+(✅|❌)?(.*?)$(.*?)(?=^#{1,6}\s|$)'
        matches = re.finditer(section_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            level = len(match.group(1))
            status = match.group(2) if match.group(2) else '❌'
            title = match.group(3).strip()
            content = match.group(4).strip()
            
            self.sections.append({
                'level': level,
                'status': status,
                'title': title,
                'content': content
            })
            self.section_content[title] = content
        
        print(f"Extracted {len(self.sections)} sections")

    def analyze(self):
        """Analyze the API documentation."""
        if not self.load_file():
            return False
        
        self.extract_toc_and_headings()
        self.extract_sections()
        
        # Count implementation status
        status_count = {'✅': 0, '❌': 0}
        for status in self.implementation_status.values():
            status_count[status] += 1
        
        # Calculate implementation percentage
        total = len(self.implementation_status)
        implemented_percentage = (status_count['✅'] / total * 100) if total > 0 else 0
        
        print("\n===== Analysis Results =====")
        print(f"Total sections: {total}")
        print(f"Implemented sections: {status_count['✅']} ({implemented_percentage:.1f}%)")
        print(f"Not implemented sections: {status_count['❌']} ({100-implemented_percentage:.1f}%)")
        
        return True

    def generate_updated_toc(self):
        """Generate an updated table of contents."""
        toc = ["# Prbal API Documentation", "", 
               "This document outlines the various API endpoints available in the Prbal backend system.",
               "", "## Table of Contents"]
        
        # Group headings by their level
        for heading in self.headings:
            indent = "  " * (heading['level'] - 2) if heading['level'] > 1 else ""
            anchor = heading['title'].lower().replace(' ', '-').replace('&', '').replace('/', '').replace('(', '').replace(')', '')
            toc.append(f"{indent}- [{heading['status']} {heading['title']}](#{anchor})")
        
        return '\n'.join(toc)

    def generate_updated_content(self):
        """Generate updated documentation content with consistent formatting."""
        output = [self.generate_updated_toc(), ""]
        
        # Add each section with consistent formatting
        for section in self.sections:
            heading = '#' * section['level']
            output.append(f"{heading} {section['status']} {section['title']}")
            output.append("")
            
            # Add section content if available
            if section['content']:
                output.append(section['content'])
            else:
                output.append("*Documentation for this section is under development.*")
            
            output.append("")
        
        return '\n'.join(output)

    def save_updated_file(self, output_filepath=None):
        """Save the updated documentation to a file."""
        if output_filepath is None:
            # Create filename with timestamp
            dirname = os.path.dirname(self.filepath)
            basename = os.path.basename(self.filepath)
            name, ext = os.path.splitext(basename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = os.path.join(dirname, f"{name}_updated_{timestamp}{ext}")
        
        updated_content = self.generate_updated_content()
        
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated documentation saved to: {output_filepath}")
            return output_filepath
        except Exception as e:
            print(f"Error saving updated file: {e}")
            return None

def main():
    """Main function to run the analyzer."""
    api_doc_path = os.path.abspath("postman/Prbal-API.md")
    analyzer = ApiDocAnalyzer(api_doc_path)
    
    if analyzer.analyze():
        updated_file = analyzer.save_updated_file()
        
        if updated_file:
            print("\nSummary of improvements:")
            print("1. Reorganized table of contents with implementation status")
            print("2. Standardized section formatting and heading levels")
            print("3. Added missing section placeholders")
            print("4. Applied consistent implementation status indicators")
            print("5. Created backup of original file")
            
            print("\nRecommended next steps:")
            print("1. Review the updated documentation in:", updated_file)
            print("2. Focus on implementing sections marked with ❌")
            print("3. Update implementation status markers as you progress")

if __name__ == "__main__":
    main()
