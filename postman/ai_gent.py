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
import chromadb
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
        self.db_client = None
        self.db_collection_name = None # Store the name for reference
        self.db_path = None # Store the path for reference
        
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
    
    def save_current_content_in_place(self):
        """
        Saves the current self.content_lines back to self.filepath.
        Returns True on success, False on failure.
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.writelines(self.content_lines)
            print(f"Successfully saved changes to: {self.filepath}")
            return True
        except Exception as e:
            print(f"Error saving file {self.filepath}: {e}")
            return False
    
    def _identify_missing_sections_from_toc(self):
        """
        Identifies TOC entries that do not have a corresponding heading in the document.
        Returns a list of toc_entry dictionaries that are missing.
        """
        missing_sections = []
        if not self.headings:
            # This should ideally be populated by analyze_document_structure before calling this
            print("Warning: Headings not populated before checking for missing sections.")
            self.extract_headings()

        # Normalize actual heading titles for robust comparison
        # For now, simple lowercase and strip. Consider anchor generation for more robustness.
        actual_heading_titles = {h['title'].lower().strip(): h for h in self.headings}

        for toc_entry in self.toc_entries:
            toc_title_normalized = toc_entry['title'].lower().strip()
            if toc_title_normalized not in actual_heading_titles:
                # Further check: sometimes TOC might have extra details not in heading
                # e.g. TOC: "User Profile (GET)", Heading: "User Profile"
                # This basic check might yield false positives if titles aren't exact enough.
                # For now, we rely on titles being reasonably close or identical after normalization.
                missing_sections.append(toc_entry)
        return missing_sections

    def _append_new_section_markdown(self, section_title, toc_level_guess=2):
        """
        Appends markdown for a new section to self.content_lines.
        Uses a guessed level for the heading (e.g., 2 for ##).
        """
        heading_prefix = '#' * toc_level_guess
        # Add newlines for spacing
        new_section_md_lines = [
            "\n",  # Ensure a blank line before the new section
            f"{heading_prefix} [❌] {section_title}\n",
            "\n",
            "(Content to be added for this new section.)\n",
            "\n",
            "---\n"
        ]
        self.content_lines.extend(new_section_md_lines)
        print(f"Placeholder for section '{section_title}' appended to content.")
    
    def start_interactive_processing(self):
        """
        Starts the processing sequence for UI interaction: 
        backs up, analyzes, and identifies missing TOC sections.
        Returns a list of missing_toc_section dictionaries.
        """
        print("\n===== Starting Interactive Document Processing =====")
        backup_path = self.backup_original()
        if not backup_path:
            print("Warning: Failed to create backup. Continuing anyway.")
        
        self.analyze_document_structure()
        missing_sections = self._identify_missing_sections_from_toc()
        
        if missing_sections:
            print(f"Identified {len(missing_sections)} TOC entries potentially missing sections.")
        else:
            print("No missing sections identified from TOC initially.")
        return missing_sections

    def add_missing_sections_and_reanalyze(self, titles_to_create):
        """
        Appends specified sections, saves, reloads, re-analyzes, 
        and returns a new list of missing TOC sections.
        Args:
            titles_to_create (list of str): List of section titles to create.
        Returns:
            list: Updated list of missing_toc_section dictionaries.
        """
        if not titles_to_create:
            print("No titles provided to create sections.")
            return self._identify_missing_sections_from_toc() # Return current state

        print(f"Attempting to add {len(titles_to_create)} new section(s)...")
        for title in titles_to_create:
            self._append_new_section_markdown(title, toc_level_guess=2)
        
        try:
            # Save changes to the current working file
            if not self.save_current_content_in_place():
                print("Error: Failed to save intermediate changes after adding sections.")
                # Fallback or error handling: what should be returned?
                # For now, try to proceed with current in-memory state for re-analysis
                # but this indicates a potential issue.
            else:
                print(f"Successfully saved intermediate changes to: {self.filepath}")

            # Reload and re-analyze the modified file
            if not self.load_file():
                print("Critical Error: Failed to reload file after adding sections. Aborting process.")
                return [] # Indicate critical failure
            self.analyze_document_structure() # Re-parses everything
            print("Re-analyzed document structure after adding sections.")
        except Exception as e:
            print(f"Error saving or reloading file after adding section(s): {e}")
            print("Aborting addition process.")
            return [] # Indicate critical failure

        # Return the new list of missing sections
        return self._identify_missing_sections_from_toc()

    def finalize_processing_after_interactive(self):
        """
        Performs final processing steps after interactive section additions are complete.
        Formats headings, updates TOC, saves enhanced file, and updates ChromaDB.
        Returns:
            bool: True if final processing was successful.
        """
        print("\n===== Finalizing Document Processing =====")
        # Document structure should be up-to-date from the last add_missing_sections_and_reanalyze call
        # or start_interactive_processing if no sections were added.
        
        self.format_headings() # Ensure headings are consistently formatted
        self.extract_sections()    # Re-extract based on final content
        self.build_section_tree()  # Re-build based on final sections

        # save_updated_file handles TOC regeneration and saving with "enhanced" suffix.
        # It also calls add_sections_to_chromadb internally if the TOC was updated.
        if self.save_updated_file(suffix="enhanced"):
            print(f"Final processed document saved to: {self.output_filepath}")
            # Ensure ChromaDB is updated with the final state, even if TOC wasn't the primary change.
            # save_updated_file calls update_toc_in_original which calls add_sections_to_chromadb.
            # If save_updated_file didn't trigger a TOC update (e.g., TOC was already perfect but sections were added),
            # we might need an explicit update. However, analyze_document_structure and section extraction
            # should prepare self.sections correctly for the existing ChromaDB update logic in save_updated_file.
            print("ChromaDB should be updated via save_updated_file call.")
            return True
        else:
            print("Failed to save the final processed document.")
            return False

    def process_and_save(self):
        """
        Process and enhance API documentation. (CLI Version - Retains original interactive loop)
        For Streamlit, use start_interactive_processing, add_missing_sections_and_reanalyze, 
        and finalize_processing_after_interactive separately.
        
        Returns:
            bool: True if processing was successful
        """
        print("\n===== Processing API Documentation (CLI Mode) =====")
        
        # Create backup
        backup_path = self.backup_original()
        if not backup_path:
            print("Warning: Failed to create backup. Continuing anyway.")
        
        self.analyze_document_structure()

        # --- Interactive Loop for Missing Sections (Retained for CLI compatibility) ---
        while True:
            missing_toc_sections = self._identify_missing_sections_from_toc()

            if not missing_toc_sections:
                print("All TOC entries appear to have corresponding sections in the document.")
                break

            print("\nThe following TOC entries do not have corresponding sections in the document:")
            for i, toc_item in enumerate(missing_toc_sections):
                print(f"  {i + 1}. {toc_item['title']}")
            
            print("\nOptions:")
            print("  [number] - Create the specified missing section.")
            print("  [a]      - Create all listed missing sections (appended to end).")
            print("  [s]      - Skip creating these sections and continue processing.")
            print("  [q]      - Quit processing and return to main menu.")
            
            user_choice = input("Enter your choice: ").strip().lower()

            if user_choice == 'q':
                print("Processing aborted by user.")
                return False
            if user_choice == 's':
                print("Skipping creation of missing sections for now.")
                break

            sections_to_create_this_iteration = []
            if user_choice == 'a':
                sections_to_create_this_iteration = missing_toc_sections
            elif user_choice.isdigit():
                try:
                    choice_idx = int(user_choice) - 1
                    if 0 <= choice_idx < len(missing_toc_sections):
                        sections_to_create_this_iteration = [missing_toc_sections[choice_idx]]
                    else:
                        print("Invalid number. Please try again.")
                        continue
                except ValueError:
                    print("Invalid input. Please enter a number, 'a', 's', or 'q'.")
                    continue
            else:
                print("Invalid choice. Please try again.")
                continue

            if not sections_to_create_this_iteration:
                continue

            for toc_item_to_create in sections_to_create_this_iteration:
                self._append_new_section_markdown(toc_item_to_create['title'], toc_level_guess=2)
            
            try:
                if not self.save_current_content_in_place():
                     print("Error: Failed to save intermediate changes after adding sections.")
                     return False # Critical error
                print(f"Successfully saved intermediate changes to: {self.filepath}")

                if not self.load_file():
                    print("Critical Error: Failed to reload file after adding sections. Aborting process.")
                    return False
                self.analyze_document_structure()
                print("Re-analyzed document structure after adding sections.")
            except Exception as e:
                print(f"Error saving or reloading file after adding section(s): {e}")
                print("Aborting process to prevent data corruption.")
                return False
        # --- End of Interactive Loop for Missing Sections ---

        # Final processing steps
        print("\nProceeding with final document processing...")
        return self.finalize_processing_after_interactive()

    #--------------------------#
    # High-level operations    #
    #--------------------------#
    
    def analyze(self):
        """
        Analyze the API documentation structure and implementation status,
        store results in ChromaDB, and print detailed analysis.

        Returns:
            bool: True if analysis was successful
        """
        print("\n===== Analyzing API Documentation =====")

        if not self.load_file():
            return False

        # Ensure TOC and sections are extracted
        self.find_toc_section() # Needed for self.toc_entries
        self.extract_toc_entries()
        self.extract_headings() # Needed for self.sections and status
        self.extract_sections()

        try:
            # Initialize ChromaDB
            file_dir = os.path.dirname(self.filepath)
            self.db_path = os.path.join(file_dir, "api_docs_db")
            # Sanitize filename for collection name
            base_filename = os.path.basename(self.filepath)
            sanitized_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename)
            self.db_collection_name = f"docs_{sanitized_filename}"
            
            print(f"Initializing ChromaDB at: {self.db_path}")
            print(f"Using collection: {self.db_collection_name}")
            
            self.db_client = chromadb.PersistentClient(path=self.db_path)
            collection = self.db_client.get_or_create_collection(name=self.db_collection_name)

            # Prepare data for ChromaDB
            toc_documents = []
            toc_metadatas = []
            toc_ids = []

            print("\n----- Table of Contents (TOC) Analysis -----")
            print(f"Found {len(self.toc_entries)} TOC entries.")
            for i, entry in enumerate(self.toc_entries):
                # Basic indentation to level (approximate)
                level = entry.get('indent_level', 0) // 2 + 1 
                print(f"  - Title: '{entry['title']}', TOC Line: {entry['toc_line']}, Level: {level}, Stated Line: {entry.get('stated_line', 'N/A')}, Status: {entry.get('status', 'N/A')}")
                toc_ids.append(f"toc_{self.db_collection_name}_{entry['toc_line']}")
                toc_documents.append(entry['title']) # Using title as the document content for now
                toc_metadatas.append({
                    "type": "toc_entry",
                    "title": entry['title'],
                    "toc_line": entry['toc_line'],
                    "stated_line": entry.get('stated_line'),
                    "status": entry.get('status'),
                    "anchor": entry.get('anchor'),
                    "indent_level": entry.get('indent_level')
                })
            
            if toc_ids:
                collection.add(ids=toc_ids, documents=toc_documents, metadatas=toc_metadatas)
                print(f"Stored/Updated {len(toc_ids)} TOC entries in ChromaDB.")

            section_documents = []
            section_metadatas = []
            section_ids = []

            print("\n----- Document Section Analysis -----")
            print(f"Found {len(self.sections)} sections (based on headings).")
            for i, section in enumerate(self.sections):
                print(f"  - Title: '{section['title']}', Doc Line: {section['start_line']}, Level: {section['level']}, Status: {section['status']}")
                section_ids.append(f"section_{self.db_collection_name}_{section['start_line']}")
                # Using a snippet of content or just title for 'document'
                # For simplicity, using title. For actual semantic search, content snippet is better.
                section_documents.append(section['title'])
                section_metadatas.append({
                    "type": "section",
                    "title": section['title'],
                    "start_line": section['start_line'],
                    "end_line": section.get('end_line', section['start_line'] + len(section.get('content',[]))),
                    "level": section['level'],
                    "status": section['status']
                })
            
            if section_ids:
                collection.add(ids=section_ids, documents=section_documents, metadatas=section_metadatas)
                print(f"Stored/Updated {len(section_ids)} document sections in ChromaDB.")

        except Exception as e:
            print(f"Error during ChromaDB integration: {e}")
            print("Analysis will continue without database storage for this run.")

        # Calculate and print implementation percentage (from existing logic)
        implemented_percentage = 0
        if self.implementation_status["total"] > 0:
            implemented_percentage = (self.implementation_status["implemented"] /
                                    self.implementation_status["total"] * 100)

        print("\n----- Overall Implementation Status -----")
        print(f"Total trackable items (headings): {self.implementation_status['total']}")
        print(f"Implemented items: {self.implementation_status['implemented']} ({implemented_percentage:.1f}%)")
        print(f"Not implemented items: {self.implementation_status['total'] - self.implementation_status['implemented']} ({100 - implemented_percentage:.1f}%)")
        
        if self.db_path and self.db_collection_name:
            print(f"\nAnalysis data stored/updated in local vector database:")
            print(f"  DB Path: {self.db_path}")
            print(f"  Collection: {self.db_collection_name}")

        return True
    
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


def display_interactive_menu(current_api_doc_path_display):
    """
    Display an interactive menu of options and get the user's choice.

    Args:
        current_api_doc_path_display (str): The path of the API doc currently being used.

    Returns:
        tuple: (command, data) where command can be 'analyze', 'process', 'validate', 'all',
               'set_path', 'exit', or None. Data is the custom_filepath if command is 'set_path'.
    """
    print("\n===== INTERACTIVE MENU =====\n")
    print("1. Analyze API documentation")
    print("2. Process and enhance documentation")
    print("3. Validate TOC entries and line numbers")
    print("4. Perform all operations in sequence")
    print("5. Specify a custom file path")
    print("6. Exit")

    print(f"\nCurrent API doc path: {current_api_doc_path_display}")

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
            custom_path = input("\nEnter custom file path: ").strip()
            if not custom_path:
                print("No path provided. Current path remains unchanged.")
                return None, None  # Signal to redisplay menu
            elif not os.path.exists(custom_path):
                print(f"Error: Path '{custom_path}' does not exist. Please try again.")
                return None, None  # Signal to redisplay menu
            else:
                print(f"API documentation path set to: {custom_path}")
                return "set_path", custom_path
        elif choice == "6":
            return "exit", None
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")
            return None, None  # Signal to redisplay menu

    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted. Returning to menu.")
        return None, None  # Signal to redisplay menu


def execute_agent_command(command_to_execute, doc_path):
    """
    Creates an ApiDocumentationAgent instance and executes a specified command.

    Args:
        command_to_execute (str): The command to run ('analyze', 'process', 'validate', 'all').
        doc_path (str): The path to the API documentation file.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    if not doc_path or not os.path.exists(doc_path):
        print(f"Error: API documentation file path is not set or invalid: {doc_path}")
        print("Please specify a valid file path.")
        return False

    print(f"\nProcessing file: {doc_path} for command: {command_to_execute}")
    agent = ApiDocumentationAgent(doc_path)
    success = False

    if command_to_execute == "analyze":
        success = agent.analyze()
    elif command_to_execute == "process":
        success = agent.process()
    elif command_to_execute == "validate":
        success = agent.validate()
    elif command_to_execute == "all":
        success = agent.execute_all()
    
    if success:
        print("\nOperation completed successfully.")
        print("Next Steps:")
        if command_to_execute == "analyze":
            print("- Focus on implementing sections marked with ❌")
            print("- Update implementation status markers as you complete sections")
        
        elif command_to_execute == "process":
            if agent.output_filepath:
                 print(f"- Review the enhanced documentation at: {agent.output_filepath}")
            if agent.backup_filepath:
                print(f"- Original file backed up at: {agent.backup_filepath}")

        elif command_to_execute == "validate":
            print(f"- The Table of Contents in '{doc_path}' may have been updated.")
            if agent.backup_filepath:
                print(f"- Original file (before validation) backed up at: {agent.backup_filepath}")
            print("- Verify the updated TOC entries in the modified file.")

        elif command_to_execute == "all": 
            if agent.output_filepath: 
                 print(f"- Review the fully processed and validated documentation at: {agent.output_filepath}")
            if agent.backup_filepath:
                print(f"- Original file backed up at: {agent.backup_filepath}")
            print("- Focus on implementing sections marked with ❌ (based on analysis).")
    else:
        print("\nOperation failed or was interrupted.")
    
    print("-" * 50) # Separator
    return success

def main():
    """
    Main entry point for the script.
    Handles CLI arguments for one-shot execution or enters an interactive menu loop.
    """
    print_header()
    
    parser = argparse.ArgumentParser(
        description="Prbal API Documentation AI Agent - Manage API documentation"
    )
    parser.add_argument(
        "command",
        nargs="?", 
        choices=["analyze", "process", "validate", "all"],
        help="Command to execute (analyze, process, validate, or all). Omit for interactive menu."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default=None,
        help="Path to the API documentation file. Omit for interactive menu or to use default."
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Force interactive menu mode."
    )
    args = parser.parse_args()

    # If a command is given via CLI (and not just --menu to override)
    if args.command and not args.menu:
        cli_api_doc_path = args.filepath if args.filepath else get_default_api_doc_path()
        if not cli_api_doc_path:
            print("Error: Could not find or determine default API documentation file for CLI execution.")
            print("Please specify the file path explicitly or ensure it's in the default location.")
            return 1
        
        success = execute_agent_command(args.command, cli_api_doc_path)
        return 0 if success else 1

    # Interactive loop mode (no command given, or --menu is present)
    else:
        api_doc_path = args.filepath if args.filepath and os.path.exists(args.filepath) else get_default_api_doc_path()

        while True:
            current_path_display = ""
            if api_doc_path and os.path.exists(api_doc_path):
                current_path_display = api_doc_path
            elif api_doc_path: # Path is set but doesn't exist
                current_path_display = f"{api_doc_path} (File not found)"
            else: # Path is None or default also not found
                default_from_func = get_default_api_doc_path()
                if default_from_func and os.path.exists(default_from_func):
                    api_doc_path = default_from_func # Auto-load default if not set and found
                    current_path_display = api_doc_path
                elif default_from_func:
                    current_path_display = f"{default_from_func} (Default file not found)"
                else:
                    current_path_display = "<File path not set - Default path could not be determined>"
            
            menu_command, menu_data = display_interactive_menu(current_path_display)

            if menu_command == "exit":
                print("Exiting AI Gent. Goodbye!")
                break
            elif menu_command == "set_path":
                api_doc_path = menu_data 
            elif menu_command in ["analyze", "process", "validate", "all"]:
                if not api_doc_path or not os.path.exists(api_doc_path):
                    print(f"Error: API documentation file path is not set or is invalid.")
                    print(f"Current path: '{current_path_display}'")
                    print("Please specify a valid file path using option 5 from the menu.")
                    print("-" * 50)
                    continue 
                
                execute_agent_command(menu_command, api_doc_path)
            
            elif menu_command is None: 
                print("-" * 50)
                continue # Redisplay menu (error/info message handled by display_interactive_menu)
            else: 
                print(f"Internal error: Unknown menu command '{menu_command}'. Please report this.")
                print("-" * 50)
                continue
        return 0



if __name__ == "__main__":
    sys.exit(main())