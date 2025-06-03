#!/usr/bin/env python3
"""
Prbal API Documentation AI Agent

This script consolidates the functionality of multiple API documentation tools into a single agent:
- analyze_and_update_api_docs.py: Basic API doc analysis and updating
- enhanced_api_docs_processor.py: Advanced processing with hierarchical structure
- toc_line_number_validator.py: TOC validation and line number correction

The AI Agent provides a unified interface for API documentation management with commands for:
- analyze: Analyze API documentation structure and implementation status
- process: Process and enhance API documentation with consistent formatting
- validate: Validate and correct table of contents entries and line numbers
- all: Perform all operations in sequence

Usage:
    python ai_gent.py analyze path/to/api-docs.md
    python ai_gent.py process path/to/api-docs.md
    python ai_gent.py validate path/to/api-docs.md
    python ai_gent.py all path/to/api-docs.md
    # Analyze API documentation
python ai_gent.py analyze

# Process and enhance documentation
python ai_gent.py process

# Validate TOC entries and line numbers
python ai_gent.py validate

# Perform all operations in sequence
python ai_gent.py all

# Specify a custom file path
python ai_gent.py analyze path/to/custom/api-docs.md
"""

import re
import os
import sys
import shutil
import argparse
from datetime import datetime
from collections import defaultdict


class ApiDocumentationAgent:
    """
    Master agent class that combines functionality from all API documentation scripts.
    Provides unified methods for analyzing, processing, and validating API documentation.
    """
    
    def __init__(self, filepath):
        """
        Initialize the API Documentation Agent with a path to the documentation file.
        
        Args:
            filepath (str): Path to the API documentation markdown file
        """
        self.filepath = os.path.abspath(filepath)
        self.content = ""
        self.content_lines = []
        self.sections = []
        self.headings = []
        self.toc_entries = []
        self.section_hierarchy = {"children": []}
        self.implementation_status = {"total": 0, "implemented": 0}
        self.toc_start_line = -1
        self.toc_end_line = -1
        self.output_filepath = None
        self.backup_filepath = None
        
    def load_file(self):
        """
        Load the markdown file content both as a string and as lines.
        
        Returns:
            bool: True if file loaded successfully, False otherwise
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                # Reset file pointer and read as lines
                f.seek(0)
                self.content_lines = f.readlines()
            print(f"Successfully loaded file: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
            
    def backup_original(self):
        """
        Create a backup of the original documentation file.
        
        Returns:
            str: Path to the backup file, or None if backup failed
        """
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        name, ext = os.path.splitext(basename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_filepath = os.path.join(dirname, f"{name}_backup_{timestamp}{ext}")
        
        try:
            shutil.copy2(self.filepath, self.backup_filepath)
            print(f"Created backup at: {self.backup_filepath}")
            return self.backup_filepath
        except Exception as e:
            print(f"Error creating backup: {e}")
            self.backup_filepath = None
            return None
            
    def find_toc_section(self):
        """
        Find the Table of Contents section in the document.
        
        Returns:
            bool: True if TOC section found, False otherwise
        """
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
    
    def extract_headings(self):
        """
        Extract all headings from the document with their line numbers, levels, and status.
        
        Returns:
            int: Number of headings found
        """
        heading_regex = r'^(#+)\s+(✅|❌)?\s*(.*?)(?:\(L-(\d+)\))?$'
        
        self.headings = []
        for i, line in enumerate(self.content_lines):
            heading_match = re.match(heading_regex, line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                status = heading_match.group(2) if heading_match.group(2) else '❌'
                title = heading_match.group(3).strip()
                line_num = i + 1  # 1-based line numbering
                
                self.headings.append({
                    'level': level,
                    'title': title,
                    'status': status,
                    'line_num': line_num
                })
                
                # Update implementation status counters
                self.implementation_status["total"] += 1
                if status == '✅':
                    self.implementation_status["implemented"] += 1
        
        print(f"Found {len(self.headings)} headings in the document")
        return len(self.headings)
    
    def extract_toc_entries(self):
        """
        Extract all entries from the Table of Contents with their status and line references.
        
        Returns:
            int: Number of TOC entries found
        """
        toc_entry_regex = r'^\s*-\s+\[(✅|❌)?\s*(.*?)\]\((.*?)\)(?:\(L-(\d+)\))?$'
        
        self.toc_entries = []
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
                    'indent_level': len(self.content_lines[i]) - len(self.content_lines[i].lstrip())
                })
        
        print(f"Found {len(self.toc_entries)} TOC entries")
        return len(self.toc_entries)
    
    def extract_sections(self):
        """
        Extract all sections with their content from the document.
        
        Returns:
            int: Number of sections found
        """
        section_pattern = r'^(#{1,6})\s+(✅|❌)?\s*(.*?)$(.*?)(?=^#{1,6}\s|$)'
        matches = re.finditer(section_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        self.sections = []
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
        
        print(f"Extracted {len(self.sections)} sections")
        return len(self.sections)
        
    def build_section_tree(self):
        """
        Build a hierarchical tree of sections for better TOC generation.
        
        Returns:
            dict: Root node of the section hierarchy
        """
        self.section_hierarchy = {"children": []}
        stack = [self.section_hierarchy]
        
        for heading in sorted(self.headings, key=lambda x: x["line_num"]):
            level = heading["level"]
            
            # Go up the stack until we find a parent with a lower level
            while len(stack) > 1 and stack[-1]["level"] >= level:
                stack.pop()
            
            # Create a new node
            node = {
                "level": level,
                "title": heading["title"],
                "status": heading["status"],
                "line_num": heading["line_num"],
                "children": []
            }
            
            # Add to parent's children
            stack[-1]["children"].append(node)
            
            # Push this node onto the stack
            stack.append(node)
        
        return self.section_hierarchy
    
    def validate_toc_entries(self):
        """
        Validate TOC entries against actual headings and check line number references.
        
        Returns:
            tuple: (missing_headings, incorrect_line_numbers)
        """
        # Create a lookup map for headings by title
        heading_map = {}
        for heading in self.headings:
            heading_map[heading['title'].lower()] = heading['line_num']
        
        missing_headings = []
        incorrect_line_numbers = []
        
        for entry in self.toc_entries:
            title_lower = entry['title'].lower()
            
            # Check if heading exists
            if title_lower not in heading_map:
                missing_headings.append(entry)
                entry['validation'] = '❌'  # Missing heading
                entry['actual_line'] = None
            else:
                actual_line = heading_map[title_lower]
                
                # Check if line number is correct
                if entry['stated_line'] is not None and entry['stated_line'] != actual_line:
                    incorrect_line_numbers.append((entry, actual_line))
                    entry['validation'] = '✅'  # Heading exists but line number is wrong
                else:
                    entry['validation'] = '✅'  # Heading exists with correct line number
                
                entry['actual_line'] = actual_line
        
        print(f"Found {len(missing_headings)} missing headings")
        print(f"Found {len(incorrect_line_numbers)} entries with incorrect line numbers")
        
        return missing_headings, incorrect_line_numbers
        
    def generate_updated_toc(self):
        """
        Generate an updated table of contents with correct line numbers and status markers.
        
        Returns:
            list: List of lines for the updated TOC
        """
        toc_lines = []
        
        # Function to recursively process the section hierarchy
        def process_hierarchy(node=None, depth=0):
            if node is None:
                node = self.section_hierarchy
                
            for child in node["children"]:
                # Skip the main title and TOC itself
                if depth == 0 and (child["title"] == "Table of Contents" or 
                                  "API Documentation" in child["title"]):
                    continue
                    
                # Create anchor from title
                anchor = child["title"].lower().replace(' ', '-')
                # Clean up special characters from anchor
                anchor = re.sub(r'[^\w\-]', '', anchor)
                
                # Add line number if available
                line_suffix = f"(L-{child.get('line_num', '')})" if 'line_num' in child else ""
                    
                # Add indentation based on depth
                indent = "  " * depth
                # Add TOC entry with status and line number
                toc_lines.append(f"{indent}- [{child['status']} {child['title']}](#{anchor}){line_suffix}")
                
                # Process children recursively
                if child["children"]:
                    process_hierarchy(child, depth + 1)
        
        # Generate TOC entries from section hierarchy
        process_hierarchy()
        
        return toc_lines
    
    def generate_updated_content(self):
        """
        Generate updated markdown content with consistent formatting.
        
        Returns:
            str: Updated document content as a string
        """
        # Start with document title and introduction
        output_lines = [
            "# Prbal API Documentation",
            "",
            "This document outlines the various API endpoints available in the Prbal backend system.",
            "",
            "## Table of Contents"
        ]
        
        # Add table of contents
        output_lines.extend(self.generate_updated_toc())
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
    
    def update_toc_in_original(self):
        """
        Update only the Table of Contents in the original file, preserving the rest.
        
        Returns:
            bool: True if the update was successful, False otherwise
        """
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
            print(f"Updated TOC in original file: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error updating TOC in original file: {e}")
            return False
    
    def save_updated_file(self, suffix="enhanced"):
        """
        Save the updated document to a new file with a timestamp suffix.
        
        Args:
            suffix (str): Suffix to add to the filename
            
        Returns:
            str: Path to the saved file, or None if save failed
        """
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        name, ext = os.path.splitext(basename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_filepath = os.path.join(dirname, f"{name}_{suffix}_{timestamp}{ext}")
        
        updated_content = self.generate_updated_content()
        
        try:
            with open(self.output_filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Saved {suffix} documentation to: {self.output_filepath}")
            return self.output_filepath
        except Exception as e:
            print(f"Error saving updated file: {e}")
            self.output_filepath = None
            return None
    
    #--------------------------#
    # High-level operations    #
    #--------------------------#
    
    def analyze(self):
        """
        Analyze the API documentation structure and implementation status.
        
        Returns:
            bool: True if analysis was successful
        """
        print("\n===== Analyzing API Documentation =====")
        
        if not self.load_file():
            return False
        
        # Extract headings and sections
        self.extract_headings()
        self.extract_sections()
        
        # Calculate implementation percentage
        implemented_percentage = 0
        if self.implementation_status["total"] > 0:
            implemented_percentage = (self.implementation_status["implemented"] / 
                                    self.implementation_status["total"] * 100)
        
        # Print analysis results
        print("\n----- Analysis Results -----")
        print(f"Total sections: {self.implementation_status['total']}")
        print(f"Implemented sections: {self.implementation_status['implemented']} ({implemented_percentage:.1f}%)")
        print(f"Not implemented sections: {self.implementation_status['total'] - self.implementation_status['implemented']} ({100 - implemented_percentage:.1f}%)")
        
        return True
    
    def process(self):
        """
        Process and enhance API documentation with consistent formatting.
        
        Returns:
            bool: True if processing was successful
        """
        print("\n===== Processing API Documentation =====")
        
        if not self.load_file():
            return False
        
        # Create backup
        backup_path = self.backup_original()
        if not backup_path:
            print("Warning: Failed to create backup. Continuing anyway.")
        
        # Extract document structure
        self.extract_headings()
        self.extract_sections()
        
        # Build section hierarchy for TOC generation
        self.build_section_tree()
        
        # Save updated file
        output_path = self.save_updated_file("enhanced")
        
        if output_path:
            print("\n----- Processing Complete -----")
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
    
    def validate(self):
        """
        Validate and correct table of contents entries and line numbers.
        
        Returns:
            bool: True if validation and correction was successful
        """
        print("\n===== Validating API Documentation TOC =====")
        
        if not self.load_file():
            return False
        
        self.extract_headings()
        
        if not self.find_toc_section():
            print("Error: Could not find Table of Contents section")
            return False
        
        self.extract_toc_entries()
        missing, incorrect = self.validate_toc_entries()
        
        # Print validation report
        print("\n----- TOC Validation Report -----")
        print(f"Total TOC entries: {len(self.toc_entries)}")
        print(f"Missing headings: {len(missing)}")
        print(f"Entries with incorrect line numbers: {len(incorrect)}")
        
        if missing:
            print("\nMissing Headings:")
            for entry in missing:
                print(f"  - {entry['title']} (in TOC at line {entry['toc_line']})")
        
        if incorrect:
            print("\nIncorrect Line Numbers:")
            for entry, actual_line in incorrect:
                print(f"  - {entry['title']}: stated L-{entry['stated_line']}, " +
                      f"actual L-{actual_line}")
        
        # Update the TOC in the original file
        if self.update_toc_in_original():
            print("\n✅ Successfully updated the TOC in the original file.")
            return True
        
        return False
    
    def execute_all(self):
        """
        Execute all operations: analyze, process, and validate.
        
        Returns:
            bool: True if all operations were successful
        """
        print("\n===== Executing All API Documentation Operations =====")
        
        # First analyze
        if not self.analyze():
            print("Error: Analysis failed, aborting remaining operations")
            return False
        
        # Then process
        if not self.process():
            print("Error: Processing failed, continuing with validation")
        
        # Finally validate
        if not self.validate():
            print("Error: Validation failed")
            return False
        
        print("\n✅ All operations completed successfully!")
        return True


#----------------------------------------#
# Command-line interface                 #
#----------------------------------------#

def get_default_api_doc_path():
    """
    Get the default path to the API documentation file.
    
    Returns:
        str: Absolute path to the API documentation file
    """
    # Try to find Prbal-API.md in postman subdirectory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_doc_path = os.path.join(script_dir, "postman", "Prbal-API.md")
    
    if os.path.exists(api_doc_path):
        return api_doc_path
    
    # If not found, try one level up
    parent_dir = os.path.dirname(script_dir)
    api_doc_path = os.path.join(parent_dir, "postman", "Prbal-API.md")
    
    if os.path.exists(api_doc_path):
        return api_doc_path
    
    return None


def print_header():
    """
    Print a stylized header for the program.
    """
    print("\n" + "=" * 60)
    print("               PRBAL API DOCUMENTATION AI AGENT")
    print("=" * 60)
    print("A unified tool for analyzing, processing, and validating API docs")
    print("-" * 60 + "\n")


def show_available_commands():
    """
    Display available commands in a formatted way.
    """
    # Use default path
    default_path = get_default_api_doc_path()
    if default_path:
        default_path_display = default_path
    else:
        default_path_display = "<Not found>"
    
    print("\n===== AVAILABLE OPERATIONS =====\n")
    print("1. Analyze API documentation")
    print("   Command: python ai_gent.py analyze")
    print("\n2. Process and enhance documentation")
    print("   Command: python ai_gent.py process")
    print("\n3. Validate TOC entries and line numbers")
    print("   Command: python ai_gent.py validate")
    print("\n4. Perform all operations in sequence")
    print("   Command: python ai_gent.py all")
    print("\n5. Specify a custom file path")
    print("   Command: python ai_gent.py <command> <filepath>")
    print("\n6. Interactive menu")
    print("   Command: python ai_gent.py --menu")
    
    print(f"\nCurrent API doc path: {default_path_display}")


def display_interactive_menu():
    """
    Display an interactive menu of options and get the user's choice.
    
    Returns:
        tuple: (command, custom_filepath)
    """
    # Use default path
    default_path = get_default_api_doc_path()
    if default_path:
        default_path_display = default_path
    else:
        default_path_display = "<Not found>"
    
    print("\n===== INTERACTIVE MENU =====\n")
    print("1. Analyze API documentation")
    print("2. Process and enhance documentation")
    print("3. Validate TOC entries and line numbers")
    print("4. Perform all operations in sequence")
    print("5. Specify a custom file path")
    print("6. Exit")
    
    print(f"\nCurrent API doc path: {default_path_display}")
    
    try:
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            return "analyze", None
        elif choice == "2":
            return "process", None
        elif choice == "3":
            return "validate", None
        elif choice == "4":
            return "all", None
        elif choice == "5":
            try:
                custom_path = input("\nEnter custom file path: ").strip()
                if not custom_path:
                    print("No path provided, using default.")
                    return "all", None
                elif not os.path.exists(custom_path):
                    print(f"Warning: Path '{custom_path}' does not exist.")
                    return "all", None
                else:
                    command = input("\nChoose command (analyze, process, validate, all): ").strip().lower()
                    if command in ["analyze", "process", "validate", "all"]:
                        return command, custom_path
                    else:
                        print("Invalid command. Using 'all' command.")
                        return "all", custom_path
            except (EOFError, KeyboardInterrupt):
                print("\nInput interrupted. Using default settings.")
                return "all", None
        elif choice == "6":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice. Defaulting to 'all' operation.")
            return "all", None
    
    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted. Defaulting to 'all' operation.")
        return "all", None


def main():
    """
    Main entry point for the script.
    """
    # Print program header
    print_header()
    
    # Check if arguments are provided
    if len(sys.argv) == 1:
        # No arguments, show simplified selection menu
        print("\n===== SELECT AN OPERATION =====\n")
        print("1️⃣ Analyze API documentation")
        print("   Run: python ai_gent.py analyze")
        print("\n2️⃣ Process and enhance documentation")
        print("   Run: python ai_gent.py process")
        print("\n3️⃣ Validate TOC entries and line numbers")
        print("   Run: python ai_gent.py validate")
        print("\n4️⃣ Perform all operations in sequence")
        print("   Run: python ai_gent.py all")
        print("\n5️⃣ Specify a custom file path")
        print("   Example: python ai_gent.py analyze path/to/custom/api-docs.md")
        print("\nPlease run one of the commands above to get started.")
        sys.exit(0)
    elif len(sys.argv) == 2 and sys.argv[1] == "--menu":
        # Interactive menu requested
        command, custom_filepath = display_interactive_menu()
    else:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(
            description="Prbal API Documentation AI Agent - Manage API documentation"
        )
        
        # Add command argument
        parser.add_argument(
            "command",
            choices=["analyze", "process", "validate", "all"],
            help="Command to execute (analyze, process, validate, or all)"
        )
        
        # Add optional file path argument
        parser.add_argument(
            "filepath",
            nargs="?",
            default=None,
            help="Path to the API documentation file (defaults to postman/Prbal-API.md)"
        )
        
        # Add menu flag
        parser.add_argument(
            "--menu",
            action="store_true",
            help="Show interactive menu"
        )
        
        # Parse arguments
        args = parser.parse_args()
        
        if args.menu:
            # Show interactive menu
            command, custom_filepath = display_interactive_menu()
        else:
            command = args.command
            custom_filepath = args.filepath
    
    # Determine the API documentation path
    if custom_filepath is None:
        api_doc_path = get_default_api_doc_path()
        if api_doc_path is None:
            print("Error: Could not find default API documentation file.")
            print("Please specify the file path explicitly.")
            return 1
    else:
        api_doc_path = custom_filepath
    
    print(f"Using API documentation file: {api_doc_path}")
    
    # Create agent instance
    agent = ApiDocumentationAgent(api_doc_path)
    
    # Execute the requested command
    success = False
    
    if command == "analyze":
        success = agent.analyze()
    elif command == "process":
        success = agent.process()
    elif command == "validate":
        success = agent.validate()
    elif command == "all":
        success = agent.execute_all()
    
    # Print next steps based on command
    if success:
        print("\nNext Steps:")
        if command == "analyze" or command == "all":
            print("1. Focus on implementing sections marked with ❌")
            print("2. Update implementation status markers as you complete sections")
        
        if command == "process" or command == "all":
            print("3. Review the enhanced documentation at:", agent.output_filepath)
        
        if command == "validate" or command == "all":
            print("4. Verify the updated TOC entries in the original file")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())