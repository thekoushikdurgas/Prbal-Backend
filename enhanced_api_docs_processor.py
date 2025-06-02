#!/usr/bin/env python3
"""
Enhanced Prbal API Documentation Processor

This script analyzes and improves the Prbal-API.md file with:
- Proper handling of headings and sections
- Accurate implementation status tracking
- Better content preservation
- Updated table of contents
- Improved formatting consistency
"""

import re
import os
import shutil
from datetime import datetime


class ApiDocProcessor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.content = ""
        self.sections = []
        self.section_hierarchy = {}
        self.implementation_status = {"total": 0, "implemented": 0}
        self.output_filepath = None

    def load_file(self):
        """Load the markdown file content"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
            print(f"Successfully loaded file: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def backup_original(self):
        """Create a backup of the original file"""
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        name, ext = os.path.splitext(basename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filepath = os.path.join(dirname, f"{name}_backup_{timestamp}{ext}")
        
        try:
            shutil.copy2(self.filepath, backup_filepath)
            print(f"Created backup at: {backup_filepath}")
            return backup_filepath
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None

    def parse_headings(self):
        """Parse headings and their sections from the content"""
        # Regular expression to match markdown headings with optional status markers
        heading_regex = r'^(#{1,6})\s+(✅|❌)?\s*(.*?)$'
        
        lines = self.content.split('\n')
        current_section = {"level": 0, "title": "", "status": None, "content": [], "line_num": -1}
        
        for i, line in enumerate(lines):
            heading_match = re.match(heading_regex, line)
            
            if heading_match:
                # If we were processing a section, finalize it before starting a new one
                if current_section["level"] > 0:
                    # Join content lines preserving newlines
                    content_text = '\n'.join(current_section["content"]).strip()
                    self.sections.append({
                        "level": current_section["level"],
                        "title": current_section["title"],
                        "status": current_section["status"],
                        "content": content_text,
                        "line_num": current_section["line_num"]
                    })
                
                # Extract heading components
                level = len(heading_match.group(1))
                status = heading_match.group(2) if heading_match.group(2) else '❌'
                title = heading_match.group(3).strip()
                
                # Start a new section
                current_section = {
                    "level": level,
                    "title": title,
                    "status": status,
                    "content": [],
                    "line_num": i
                }
                
                # Update implementation status
                self.implementation_status["total"] += 1
                if status == '✅':
                    self.implementation_status["implemented"] += 1
            
            elif current_section["level"] > 0:
                # Add this line to the current section's content
                current_section["content"].append(line)
        
        # Add the last section if applicable
        if current_section["level"] > 0:
            content_text = '\n'.join(current_section["content"]).strip()
            self.sections.append({
                "level": current_section["level"],
                "title": current_section["title"],
                "status": current_section["status"],
                "content": content_text,
                "line_num": current_section["line_num"]
            })
        
        # Sort sections by their line number to preserve document order
        self.sections.sort(key=lambda x: x["line_num"])
        
        print(f"Identified {len(self.sections)} sections in the document")
        print(f"Implementation status: {self.implementation_status['implemented']}/{self.implementation_status['total']} sections implemented")

    def build_section_tree(self):
        """Build a hierarchical tree of sections"""
        self.section_hierarchy = {"children": []}
        stack = [self.section_hierarchy]
        
        for section in self.sections:
            level = section["level"]
            
            # Go up the stack until we find a parent with a lower level
            while len(stack) > 1 and stack[-1]["level"] >= level:
                stack.pop()
            
            # Create a new node
            node = {
                "level": level,
                "title": section["title"],
                "status": section["status"],
                "content": section["content"],
                "children": []
            }
            
            # Add to parent's children
            stack[-1]["children"].append(node)
            
            # Push this node onto the stack
            stack.append(node)

    def generate_toc(self, node=None, depth=0):
        """Generate a table of contents with implementation status"""
        if node is None:
            node = self.section_hierarchy
        
        toc_lines = []
        
        for child in node["children"]:
            # Skip the main title and TOC itself
            if depth == 0 and (child["title"] == "Table of Contents" or 
                              "API Documentation" in child["title"]):
                continue
                
            # Create anchor
            anchor = child["title"].lower().replace(' ', '-')
            # Clean up special characters from anchor
            anchor = re.sub(r'[^\w\-]', '', anchor)
            
            # Add indentation based on depth
            indent = "  " * depth
            # Add TOC entry with status
            toc_lines.append(f"{indent}- [{child['status']} {child['title']}](#{anchor})")
            
            # Process children recursively
            if child["children"]:
                toc_lines.extend(self.generate_toc(child, depth + 1))
        
        return toc_lines

    def generate_updated_content(self):
        """Generate updated markdown content with consistent formatting"""
        # Start with document title and introduction
        output_lines = [
            "# Prbal API Documentation",
            "",
            "This document outlines the various API endpoints available in the Prbal backend system.",
            "",
            "## Table of Contents"
        ]
        
        # Add table of contents
        output_lines.extend(self.generate_toc())
        output_lines.append("")  # Add a blank line after TOC
        
        # Process each section preserving original content
        for section in self.sections:
            # Skip the main title and TOC
            if section["level"] == 1 and ("API Documentation" in section["title"] or 
                                         section["title"] == "Table of Contents"):
                continue
            
            # Add heading with status marker
            heading = '#' * section["level"]
            output_lines.append(f"{heading} {section['status']} {section['title']}")
            output_lines.append("")  # Add a blank line after heading
            
            # Add section content if available
            if section["content"]:
                output_lines.append(section["content"])
            else:
                output_lines.append("*Documentation for this section is under development.*")
            
            output_lines.append("")  # Add a blank line after section
        
        return '\n'.join(output_lines)

    def save_updated_file(self):
        """Save the updated document to a new file"""
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        name, ext = os.path.splitext(basename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_filepath = os.path.join(dirname, f"{name}_enhanced_{timestamp}{ext}")
        
        updated_content = self.generate_updated_content()
        
        try:
            with open(self.output_filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Saved enhanced documentation to: {self.output_filepath}")
            return True
        except Exception as e:
            print(f"Error saving updated file: {e}")
            return False

    def process(self):
        """Execute the full documentation processing workflow"""
        if not self.load_file():
            return False
        
        # Create backup
        backup_path = self.backup_original()
        if not backup_path:
            print("Warning: Failed to create backup. Continuing anyway.")
        
        # Parse document structure
        self.parse_headings()
        
        # Build section hierarchy for TOC generation
        self.build_section_tree()
        
        # Save updated file
        if self.save_updated_file():
            print("\n=== Processing Complete ===")
            print(f"Implementation Progress: {self.implementation_status['implemented']}/{self.implementation_status['total']} "
                  f"({self.implementation_status['implemented']/self.implementation_status['total']*100:.1f}%)")
            print("\nImprovements made:")
            print("1. Standardized heading format with implementation status markers")
            print("2. Regenerated table of contents with accurate links")
            print("3. Preserved original detailed content")
            print("4. Improved document structure consistency")
            print("5. Created backup of original file")
            
            return True
        
        return False


def main():
    """Main execution function"""
    api_doc_path = os.path.abspath("postman/Prbal-API.md")
    processor = ApiDocProcessor(api_doc_path)
    
    if processor.process():
        print("\nNext Steps:")
        print("1. Review the enhanced documentation at:", processor.output_filepath)
        print("2. Continue implementing endpoints marked with ❌")
        print("3. Update implementation status markers as you complete sections")
        print("4. Consider adding more detailed examples for implemented endpoints")


if __name__ == "__main__":
    main()
