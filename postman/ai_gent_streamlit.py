import streamlit as st
import os
import sys
from io import StringIO
import tempfile
# from ai_gent import ApiDocumentationAgent, get_default_api_doc_path
import re
# import os
# import sys
import shutil
# import argparse
from datetime import datetime
import chromadb
# from collections import defaultdict



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
# --- Helper to capture print statements ---
class StreamlitLogCapture:
    def __init__(self):
        self.buffer = StringIO()
        self.old_stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self.buffer
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout

    def get_value(self):
        return self.buffer.getvalue()

    def clear(self):
        self.buffer.truncate(0)
        self.buffer.seek(0)

# --- Main App ---

# Custom CSS to adjust dialog width
custom_dialog_css = """
<style>
/* Target the main dialog container. Streamlit's internal classes can change, so this might need adjustment. */
/* This targets the div that directly contains the dialog's content box */
div[data-testid="stModal"],
section[data-testid="stDialog"] > div[role="dialog"] {
    max-width: 90% !important; /* Adjust percentage as needed */
    margin: auto !important; /* Center the dialog */
    border-radius: 10px; /* Optional: add rounded corners */
}
/* Ensure the content within the dialog still behaves well */
div[data-testid="stModal"] > div[role="dialog"] > div,
section[data-testid="stDialog"] > div[role="dialog"] > div {
    width: 100% !important;
}
</style>
"""
st.markdown(custom_dialog_css, unsafe_allow_html=True)
st.set_page_config(layout="wide")
st.title("Prbal API Documentation AI Agent")

# Initialize session state variables
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'api_doc_path' not in st.session_state:
    st.session_state.api_doc_path = None
if 'log_output' not in st.session_state:
    st.session_state.log_output = ""
if 'chromadb_query_results' not in st.session_state:
    st.session_state.chromadb_query_results = None
if 'processing_step' not in st.session_state:
    st.session_state.processing_step = 'idle' # idle, selecting_missing, finalizing
if 'missing_sections_for_ui' not in st.session_state:
    st.session_state.missing_sections_for_ui = []
if 'selected_sections_to_create_cb_state' not in st.session_state:
    st.session_state.selected_sections_to_create_cb_state = {}

# --- UI Elements: Sidebar for File Input and Actions ---
st.sidebar.header("Document Setup")
uploaded_file = st.sidebar.file_uploader("Upload API Documentation (Markdown)", type=['md'])
manual_path_input = st.sidebar.text_input(
    "Or provide path to API Doc file (on server)", 
    value=get_default_api_doc_path() or ""
)

# Determine API doc path and initialize agent
current_doc_path = None
if uploaded_file is not None:
    # Save uploaded file to a temporary location to get a persistent path
    if 'temp_file_path' not in st.session_state or st.session_state.get('uploaded_file_name') != uploaded_file.name:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            st.session_state.temp_file_path = tmp_file.name
        st.session_state.uploaded_file_name = uploaded_file.name
    current_doc_path = st.session_state.temp_file_path
    st.sidebar.success(f"Using uploaded file: {uploaded_file.name}")
elif manual_path_input and os.path.exists(manual_path_input):
    current_doc_path = manual_path_input
    # Clear temp file if manual path is now used
    if 'temp_file_path' in st.session_state:
        del st.session_state.temp_file_path 
        if 'uploaded_file_name' in st.session_state:
            del st.session_state.uploaded_file_name
else:
    st.sidebar.warning("Please upload a Markdown file or provide a valid path.")

if current_doc_path:
    if st.session_state.api_doc_path != current_doc_path or st.session_state.agent is None:
        st.session_state.api_doc_path = current_doc_path
        try:
            st.session_state.agent = ApiDocumentationAgent(st.session_state.api_doc_path)
            st.session_state.log_output = f"Agent initialized for: {os.path.basename(st.session_state.api_doc_path)}\n"
        except Exception as e:
            st.error(f"Error initializing agent: {e}")
            st.session_state.agent = None
elif st.session_state.agent is not None:
    # Path became invalid, clear agent
    st.session_state.agent = None
    st.session_state.api_doc_path = None
    st.session_state.log_output = "API Document path is no longer valid. Agent cleared.\n"

# --- Agent Actions --- 
st.sidebar.header("Agent Actions")
log_capture = StreamlitLogCapture()

def run_agent_action(action_name, *args, **kwargs):
    if not st.session_state.agent:
        st.sidebar.error("Agent not initialized. Please provide a valid file path.")
        st.rerun()
        return

    # Preserve existing log for append, unless it's a new top-level action start
    # or an explicit clear is requested by the calling context.
    if not kwargs.get('append_log'):
        st.session_state.log_output = f"Attempting to run: {action_name}...\n"
    else:
        st.session_state.log_output += f"\nContinuing with: {action_name}...\n"
    
    # Clear ChromaDB results for most actions, except when it's a ChromaDB query itself
    if action_name != 'query_chromadb':
        st.session_state.chromadb_query_results = None
    
    success = False
    try:
        with log_capture:
            if action_name == 'analyze':
                success = st.session_state.agent.analyze()
            
            elif action_name == 'start_interactive_processing':
                st.session_state.missing_sections_for_ui = st.session_state.agent.start_interactive_processing()
                st.session_state.selected_sections_to_create_cb_state = {item['title']: False for item in st.session_state.missing_sections_for_ui}
                if not st.session_state.missing_sections_for_ui:
                    st.session_state.log_output += "No missing sections found. Proceeding to finalize.\n"
                    st.session_state.processing_step = 'finalizing'
                else:
                    st.session_state.processing_step = 'selecting_missing'
                success = True # Represents successful initiation
            
            elif action_name == 'add_missing_sections':
                titles_to_add = args[0]
                st.session_state.missing_sections_for_ui = st.session_state.agent.add_missing_sections_and_reanalyze(titles_to_add)
                st.session_state.selected_sections_to_create_cb_state = {item['title']: False for item in st.session_state.missing_sections_for_ui}
                if not st.session_state.missing_sections_for_ui:
                    st.session_state.log_output += "All specified missing sections added or no more missing sections. Proceeding to finalize.\n"
                    st.session_state.processing_step = 'finalizing'
                else:
                    st.session_state.processing_step = 'selecting_missing'
                success = True
            
            elif action_name == 'finalize_interactive_processing':
                success = st.session_state.agent.finalize_processing_after_interactive()
                st.session_state.processing_step = 'idle'
                st.session_state.missing_sections_for_ui = []
                st.session_state.selected_sections_to_create_cb_state = {}
            
            elif action_name == 'validate':
                success = st.session_state.agent.validate()
            
            elif action_name == 'all': # CLI 'all' might still use agent.execute_all()
                st.info("Full 'All' command (CLI version with potential console prompts) started.")
                success = st.session_state.agent.execute_all()
            
            elif action_name == 'query_chromadb':
                query_text = args[0]
                num_results = int(args[1]) if len(args) > 1 and args[1] else 3
                # Ensure ChromaDB is initialized if not already
                if not st.session_state.agent.db_client or not st.session_state.agent.db_collection_name:
                    st.session_state.agent.init_chromadb()
                results = st.session_state.agent.query_chromadb(query_text, n_results=num_results)
                st.session_state.chromadb_query_results = results
                success = True

        st.session_state.log_output += log_capture.get_value()
        log_capture.clear()

        if success:
            st.session_state.log_output += f"Action '{action_name}' part completed successfully.\n"
            if action_name in ['validate', 'all', 'finalize_interactive_processing'] and st.session_state.agent.backup_filepath:
                st.session_state.log_output += f"Backup was created at: {st.session_state.agent.backup_filepath}\n"
            if action_name == 'finalize_interactive_processing' and st.session_state.agent.output_filepath:
                 st.session_state.log_output += f"Processed file saved at: {st.session_state.agent.output_filepath}\n"
        else:
            st.session_state.log_output += f"Action '{action_name}' part may have failed or was interrupted.\n"

    except Exception as e:
        st.session_state.log_output += f"\n!!! An error occurred during '{action_name}': {str(e)}\n"
        import traceback
        st.session_state.log_output += traceback.format_exc()
        log_capture.clear()
        st.session_state.processing_step = 'idle' # Reset on critical error
    
    st.rerun()

# Sidebar Buttons
if st.sidebar.button("Analyze Document"):
    st.session_state.processing_step = 'idle' # Ensure interactive processing is reset
    run_agent_action('analyze')

if st.sidebar.button("Process Document (Interactive)"):
    st.session_state.processing_step = 'idle' # Reset before starting
    st.session_state.missing_sections_for_ui = []
    st.session_state.selected_sections_to_create_cb_state = {}
    run_agent_action('start_interactive_processing')

if st.sidebar.button("Validate & Correct TOC"):
    st.session_state.processing_step = 'idle'
    run_agent_action('validate')

if st.sidebar.button("Run All Operations (CLI Style)"):
    st.session_state.processing_step = 'idle'
    run_agent_action('all')

st.sidebar.header("ChromaDB Query")
query_text_sb = st.sidebar.text_input("Enter search query:", key="query_text_sidebar")
num_results_sb = st.sidebar.number_input("Number of results:", min_value=1, max_value=20, value=3, key="num_results_sidebar")
if st.sidebar.button("Query Database"):
    st.session_state.processing_step = 'idle'
    if query_text_sb:
        run_agent_action('query_chromadb', query_text_sb, num_results_sb)
    else:
        st.sidebar.warning("Please enter a query.")

st.sidebar.divider()
st.sidebar.header("Document Viewing")
if st.sidebar.button("View Current API Document"):
    if st.session_state.api_doc_path and os.path.exists(st.session_state.api_doc_path):
        try:
            with open(st.session_state.api_doc_path, 'r', encoding='utf-8') as f_md:
                st.session_state.md_content_for_dialog = f_md.read()
                st.session_state.md_filename_for_dialog = os.path.basename(st.session_state.api_doc_path)
            st.session_state.show_md_dialog = True
            st.session_state.dialog_source = 'file'

        except Exception as e_md_view:
            st.sidebar.error(f"Error reading MD file: {e_md_view}")
            st.session_state.show_md_dialog = False

    elif st.session_state.agent and st.session_state.agent.content_lines:
        try:
            st.session_state.md_content_for_dialog = "".join(st.session_state.agent.content_lines)
            st.session_state.md_filename_for_dialog = "content loaded by agent"
            st.session_state.show_md_dialog = True
            st.session_state.dialog_source = 'agent'
        except Exception as e_agent_view:
            st.sidebar.error(f"Error getting content from agent: {e_agent_view}")
            st.session_state.show_md_dialog = False
    else:
        st.sidebar.warning("No API document loaded or path is invalid.")
        st.session_state.show_md_dialog = False

if 'render_api_doc_in_dialog_impl' not in globals():
    @st.dialog("API Document Viewer") # Use a static title for the decorator
    def render_api_doc_in_dialog_impl():
        # Determine dynamic title inside the dialog function
        dialog_title_specific = "API Document Content"
        if st.session_state.get('dialog_source') == 'file':
            dialog_title_specific = f"Displaying: {st.session_state.get('md_filename_for_dialog', 'N/A')}"
        elif st.session_state.get('dialog_source') == 'agent':
            dialog_title_specific = "Displaying content loaded by agent"
        
        st.markdown(f"### {dialog_title_specific}")
        st.markdown("---")
        with st.container(height=600): # Attempt to make this area scrollable
            st.markdown(st.session_state.get('md_content_for_dialog', '*No content available.*'))
        if st.button("Close", key="close_md_dialog_from_decorated_func"):
            st.session_state.show_md_dialog = False # Signal to not reopen this dialog on next rerun
            st.rerun() # Rerun to reflect the state change and hide dialog

if st.session_state.get('show_md_dialog'):
    render_api_doc_in_dialog_impl() # Call the decorated function


# --- Interactive Processing UI in Main Area --- 
if st.session_state.agent and st.session_state.processing_step == 'selecting_missing':
    st.subheader("Interactive Section Creation")
    if st.session_state.missing_sections_for_ui:
        st.markdown("The following TOC entries do not have corresponding sections in the document. **Select sections to create:**")
        
        # Use a form to group checkboxes and action buttons
        with st.form(key='missing_sections_form'):
            for i, toc_item in enumerate(st.session_state.missing_sections_for_ui):
                cb_key = f"cb_{toc_item['title'].replace(' ', '_')}_{i}" # Create a unique key
                st.session_state.selected_sections_to_create_cb_state[cb_key] = st.checkbox(
                    f"{toc_item['title']} (from TOC line: {toc_item.get('line_num', 'N/A')})", 
                    value=st.session_state.selected_sections_to_create_cb_state.get(cb_key, False), 
                    key=cb_key
                )
            
            form_col1, form_col2, form_col3 = st.columns(3)
            with form_col1:
                create_selected_submitted = st.form_submit_button("Create Selected Sections")
            with form_col2:
                create_all_submitted = st.form_submit_button("Create All Listed Sections")
            with form_col3:
                skip_finalize_submitted = st.form_submit_button("Skip and Finalize Processing")

        if create_selected_submitted:
            titles_to_create_selected = []
            for i, toc_item in enumerate(st.session_state.missing_sections_for_ui):
                cb_key = f"cb_{toc_item['title'].replace(' ', '_')}_{i}"
                if st.session_state.selected_sections_to_create_cb_state.get(cb_key, False):
                    titles_to_create_selected.append(toc_item['title'])
            
            if titles_to_create_selected:
                run_agent_action('add_missing_sections', titles_to_create_selected, append_log=True)
            else:
                st.warning("No sections selected to create.")
        for i, toc_item in enumerate(st.session_state.missing_sections_for_ui):
            # Use a unique key for each checkbox based on title and iteration if needed
            # For simplicity, assuming titles are unique enough for this context as keys
            is_selected = st.checkbox(f"{toc_item['title']} (from TOC line: {toc_item.get('line_num', 'N/A')})", 
                                      key=f"select_{toc_item['title'].replace(' ', '_')}_{i}", 
                                      value=st.session_state.selected_sections_to_create.get(toc_item['title'], False))
            if is_selected:
                titles_to_potentially_create.append(toc_item['title'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Create Selected Sections"):
                if titles_to_potentially_create:
                    run_agent_action('add_missing_sections', titles_to_potentially_create)
                else:
                    st.warning("No sections selected to create.")
        with col2:
            if st.button("Create All Listed Missing Sections"):
                all_missing_titles = [item['title'] for item in st.session_state.missing_sections_for_ui]
                if all_missing_titles:
                    run_agent_action('add_missing_sections', all_missing_titles)
                else:
                    st.info("No missing sections listed to create.") # Should not happen if UI is shown
        with col3:
            if st.button("Skip and Finalize Processing"):
                st.session_state.processing_step = 'finalizing' # Will be picked up by next block or rerun
                st.rerun() # Ensure immediate transition
    else:
        st.info("No missing sections to select. Moving to finalize processing...")
        st.session_state.processing_step = 'finalizing'
        # Potentially trigger rerun or let the flow continue if finalize is checked next

if st.session_state.agent and st.session_state.processing_step == 'finalizing':
    st.info("Finalizing document processing...")
    # Add a button to confirm finalization to avoid accidental auto-runs after selection
    if st.button("Confirm Finalize Processing"):
        run_agent_action('finalize_interactive_processing')
    elif not st.session_state.missing_sections_for_ui: # Auto-trigger if no missing sections were ever found
        run_agent_action('finalize_interactive_processing')


# --- Main Area for Output ---
st.header("Agent Output & Logs")
with st.expander("View Agent Logs", expanded=True):
    st.text_area("Logs", value=st.session_state.log_output, height=300, key="log_display_area_expander")

if st.session_state.chromadb_query_results:
    st.subheader("ChromaDB Query Results")
    results = st.session_state.chromadb_query_results
    if results and results.get('documents') and results['documents'][0]:
        for i, doc_content in enumerate(results['documents'][0]):
            with st.expander(f"Result {i+1} - Title: {results['metadatas'][0][i].get('section_title', 'N/A')}"):
                st.markdown(f"**ID:** `{results['ids'][0][i]}`")
                if results.get('distances') and results['distances'][0]:
                    st.markdown(f"**Distance:** `{results['distances'][0][i]:.4f}`")
                st.markdown(f"**Source File:** `{results['metadatas'][0][i].get('source_file', 'N/A')}`")
                st.markdown(f"**Line Number:** `{results['metadatas'][0][i].get('line_num', 'N/A')}`")
                st.markdown(f"**Level:** `{results['metadatas'][0][i].get('level', 'N/A')}`")
                st.markdown(f"**Status:** `{results['metadatas'][0][i].get('status', 'N/A')}`")
                st.markdown("**Content Snippet:**")
                st.text(doc_content)
    else:
        st.info("No results found for your query or an error occurred.")

# Cleanup temp file if it exists from a previous session and is no longer needed
# This is a bit tricky with Streamlit's execution model. 
# A more robust solution might involve a session timeout or explicit clear button.
# For now, we rely on re-upload or new manual path to clear the old temp file reference.

# streamlit run postman\ai_gent_streamlit.py