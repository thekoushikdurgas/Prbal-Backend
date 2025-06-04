import os
import re
import json
import sys
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import shutil
import shlex
import chromadb
from collections import defaultdict
from urllib.parse import parse_qs, urlparse
import streamlit.components.v1 as components
import logging

class APIDocParser:
    """Parser for API documentation in Markdown format"""
    
    def __init__(self, filepath):
        """Initialize with the path to the API documentation file"""
        self.filepath = filepath
        self.content = ""
        self.content_lines = []
        self.toc_entries = []
        self.sections = []
        self.headings = []
        self.api_endpoints = []
        self.section_hierarchy = {"children": []}
        self.implementation_status = {"total": 0, "implemented": 0}
        self.toc_start_line = -1
        self.toc_end_line = -1
        self.db_client = None
        self.db_collection_name = None  # Store the name for reference
        self.db_path = None  # Store the path for reference
        self.toc_dictionary = None  # Store the TOC dictionary structure
        
    def load_file(self):
        """Load the markdown file content both as a string and as lines"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                # Reset file pointer and read as lines
                f.seek(0)
                self.content_lines = f.readlines()
            st.success(f"Successfully loaded file: {self.filepath}")
            return True
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return False
            
    def backup_original(self):
        """Create a backup of the original documentation file"""
        dirname = os.path.dirname(self.filepath)
        basename = os.path.basename(self.filepath)
        name, ext = os.path.splitext(basename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filepath = os.path.join(dirname, f"{name}_backup_{timestamp}{ext}")
        
        try:
            shutil.copy2(self.filepath, backup_filepath)
            st.info(f"Created backup at: {backup_filepath}")
            return backup_filepath
        except Exception as e:
            st.error(f"Error creating backup: {e}")
            return None
            
    def find_toc_section(self):
        """Find the Table of Contents section in the document"""
        for i, line in enumerate(self.content_lines):
            if "## Table of Contents" in line:
                self.toc_start_line = i + 1  # Line after "## Table of Contents"
                break
        
        if self.toc_start_line == -1:
            st.warning("Could not find Table of Contents section")
            return False
        
        # Find the end of TOC (next heading or blank line followed by heading)
        for i in range(self.toc_start_line, len(self.content_lines)):
            line = self.content_lines[i].strip()
            if line.startswith('#') or (not line and i+1 < len(self.content_lines) and self.content_lines[i+1].strip().startswith('#')):
                self.toc_end_line = i
                break
        
        if self.toc_end_line == -1:
            self.toc_end_line = len(self.content_lines)
        
        return True
    
    def extract_headings(self):
        """Extract all headings from the document with their line numbers, levels, and status"""
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
        
        return self.headings
    
    def extract_toc_entries(self):
        """Extract all entries from the Table of Contents with their status and line references"""
        if self.toc_start_line == -1 or self.toc_end_line == -1:
            if not self.find_toc_section():
                return []
        
        toc_entry_regex = r'^\s*-\s+\[(✅|❌)?\s*(.*?)\]\((.*?)\)(?:\(L-(\d+)\))?$'
        
        self.toc_entries = []
        for i in range(self.toc_start_line, self.toc_end_line):
            line = self.content_lines[i].strip()
            toc_match = re.match(toc_entry_regex, line)
            
            if toc_match:
                status = toc_match.group(1) if toc_match.group(1) else '❌'
                title = toc_match.group(2).strip()
                anchor = toc_match.group(3)
                line_ref = int(toc_match.group(4)) if toc_match.group(4) else None
                indent_level = len(self.content_lines[i]) - len(self.content_lines[i].lstrip())
                
                self.toc_entries.append({
                    'title': title,
                    'anchor': anchor,
                    'toc_line': i + 1,  # 1-based line numbering
                    'stated_line': line_ref,
                    'status': status,
                    'indent_level': indent_level,
                    'level': indent_level // 2  # Estimate heading level based on indent
                })
        
        return self.toc_entries
    
    def extract_sections(self):
        """Extract all sections with their content from the document"""
        section_pattern = r'^(#{1,6})\s+(✅|❌)?\s*(.*?)$(.*?)(?=^#{1,6}\s|$)'
        matches = re.finditer(section_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        self.sections = []
        for match in matches:
            level = len(match.group(1))
            status = match.group(2) if match.group(2) else '❌'
            title = match.group(3).strip()
            content = match.group(4).strip()
            
            # Find the line number
            line_num = self.content[:match.start()].count('\n') + 1
            
            self.sections.append({
                'level': level,
                'status': status,
                'title': title,
                'content': content,
                'line_num': line_num
            })
        
        return self.sections
    
    def build_section_hierarchy(self):
        """Build a hierarchical tree of sections for better TOC generation"""
        if not self.headings:
            self.extract_headings()
            
        self.section_hierarchy = {"children": []}
        stack = [self.section_hierarchy]
        
        # Determine the maximum level in the document
        max_level = 0
        for heading in self.headings:
            max_level = max(max_level, heading.get("level", 0))
        
        for heading in sorted(self.headings, key=lambda x: x["line_num"]):
            level = heading["level"]
            
            # Go up the stack until we find a parent with a lower level
            while len(stack) > 1 and stack[-1]["level"] >= level:
                stack.pop()
            
            # Determine if this is the last level
            is_last = (level == max_level) or not any(h["level"] > level for h in self.headings)
            
            # Create a new node
            node = {
                "level": level,
                "title": heading["title"],
                "status": heading["status"],
                "line_num": heading["line_num"],
                "anchor": heading["title"].lower().replace(' ', '-'),
                "children": [],
                "is_last": is_last
            }
            
            # Clean up anchor for special characters
            node["anchor"] = re.sub(r'[^\w\-]', '', node["anchor"])
            
            # Add to parent's children
            stack[-1]["children"].append(node)
            
            # Push this node onto the stack
            stack.append(node)
        
        # After building the hierarchy, build the TOC dictionary
        self.build_toc_dictionary()
        
        return self.section_hierarchy
        
    def build_toc_dictionary(self):
        """Build a TOC dictionary that follows the requested structure"""
        if not self.section_hierarchy:
            self.build_section_hierarchy()
        
        # Determine first and last levels
        first_level = 1  # Always Level 1
        last_level = 0
        for heading in self.headings:
            last_level = max(last_level, heading.get("level", 0))
        
        # Function to convert a node to the new format recursively
        def convert_node_to_toc_format(node):
            # Skip if node doesn't have a title (like the root node)
            if "title" not in node:
                return None
            
            # Check if this node corresponds to an API endpoint
            api_data = {}
            for api in self.api_endpoints:
                if api["title"] == node.get("title"):
                    api_data = api
                    break
            
            # Check if children exist
            has_children = bool(node.get("children", []))
            
            # Determine if this is the last level
            # A node is considered last level if:
            # 1. It has no children OR
            # 2. It's at the maximum heading level found in the document
            is_last = (node["level"] == last_level) or not has_children
            
            # Convert children recursively
            children = []
            for child in node.get("children", []):
                child_node = convert_node_to_toc_format(child)
                if child_node:
                    children.append(child_node)
            
            # Create the new node structure
            toc_node = {
                "name": node["title"],
                "level": node["level"],
                "is_last": is_last,
                "status": node.get("status", "❌")
            }
            
            # Add children if any
            if children:
                toc_node["children"] = children
            
            # Add API info if it's an endpoint
            if api_data:
                toc_node["api"] = api_data
            elif is_last:
                toc_node["api"] = {}  # Empty API object for leaf nodes
            
            return toc_node
        
        # Start the conversion from level 1 nodes
        toc_dict = {}
        for root_node in self.section_hierarchy["children"]:
            if root_node.get("level", 0) == first_level:
                converted = convert_node_to_toc_format(root_node)
                if converted:
                    toc_dict = converted
                    break  # Just take the first level 1 node
        
        # Store in the instance for later use
        self.toc_dictionary = {"toc": toc_dict}
        
        # Store in ChromaDB if available
        if self.db_client and self.db_collection_name:
            try:
                collection = self.db_client.get_collection(name=self.db_collection_name)
                # Delete existing TOC dictionary if it exists
                try:
                    collection.delete(ids=["toc_dictionary"])
                except Exception as e:
                    # st.info(f"Could not delete existing toc_dictionary from ChromaDB (may not exist): {e}")
                    pass # Ignore if it doesn't exist or other deletion error
                
                current_file_mtime = os.path.getmtime(self.filepath)
                current_file_mtime_iso = datetime.fromtimestamp(current_file_mtime).isoformat()
                
                # Store as a single document with a special ID
                collection.add(
                    documents=[json.dumps(self.toc_dictionary)],
                    metadatas=[{
                        "type": "toc_dictionary", 
                        "source_file": self.filepath,
                        "source_file_mtime_iso": current_file_mtime_iso, # Added for freshness check
                        "first_level": first_level,
                        "last_level": last_level,
                        "total_headings": len(self.headings),
                        "timestamp": datetime.now().isoformat()
                    }],
                    ids=["toc_dictionary"]
                    )
                st.success("TOC dictionary stored in ChromaDB.")
            except Exception as e:
                st.warning(f"Could not store TOC dictionary in ChromaDB: {e}")
        return self.toc_dictionary

    def extract_api_endpoints(self):
        """Extract API endpoints with their details from the sections"""
        if not self.sections:
            self.extract_sections()
        
        self.api_endpoints = []
        
        for section in self.sections:
            content = section['content']
            
            endpoint_match = re.search(r'\*\*Endpoint:\*\*\s+`([^`]+)`', content)
            if not endpoint_match:
                continue
                
            endpoint_str = endpoint_match.group(1)
            
            method_match = re.search(r'^(GET|POST|PUT|DELETE|PATCH)\s+', endpoint_str, re.IGNORECASE)
            if method_match:
                method = method_match.group(1).upper()
                path = endpoint_str[len(method):].strip()
            else:
                title_lower = section['title'].lower()
                if 'create' in title_lower or 'add' in title_lower or 'register' in title_lower:
                    method = 'POST'
                elif 'update' in title_lower or 'edit' in title_lower or 'modify' in title_lower:
                    method = 'PUT'
                elif 'delete' in title_lower or 'remove' in title_lower:
                    method = 'DELETE'
                elif 'get' in title_lower or 'list' in title_lower or 'view' in title_lower:
                    method = 'GET'
                else:
                    method = 'GET' # Default
                path = endpoint_str

            request_body = None
            request_body_match = re.search(r'\*\*Request Body:\*\*\s+```json\s+(.+?)\s+```', content, re.DOTALL)
            if request_body_match:
                try:
                    request_body = json.loads(request_body_match.group(1).strip())
                except json.JSONDecodeError:
                    request_body = request_body_match.group(1).strip()
            
            curl_command = None
            curl_match = re.search(r'```bash\s+(curl .+?)\s+```', content, re.DOTALL)
            if curl_match:
                curl_command = curl_match.group(1).strip()
            
            response_example = None
            response_match = re.search(r'\*\*Possible Output Response \(Success.*?\):\*\*\s+```json\s+(.+?)\s+```', content, re.DOTALL)
            if response_match:
                try:
                    response_example = json.loads(response_match.group(1).strip())
                except json.JSONDecodeError:
                    response_example = response_match.group(1).strip()

            api_entry = {
                'title': section['title'],
                'endpoint': endpoint_str,
                'method': method,
                'path': path,
                'status': section['status'],
                'request_body': request_body,
                'curl_command': curl_command,
                'response_example': response_example,
                'section_id': section['title'].lower().replace(' ', '-').replace('/', '-'),
                'section_level': section['level'],
                'section_content': content,
                'line_num': section['line_num']
            }
            self.api_endpoints.append(api_entry)
        return self.api_endpoints

    def detect_placeholders(self):
        """Detect placeholder text like '(Section content to be added)' and log warnings"""
        placeholder_pattern = r'\(Section content to be added\)'
        for i, line in enumerate(self.content_lines):
            if re.search(placeholder_pattern, line):
                logging.warning(f'Placeholder detected at line {i+1}: Incomplete section may cause parsing issues.')
                # Optionally, collect and report in UI

    def init_chromadb(self):
        """Initialize ChromaDB for semantic search"""
        try:
            db_dir = os.path.join(os.path.dirname(self.filepath), "api_docs_db")
            os.makedirs(db_dir, exist_ok=True)
            
            filename = os.path.basename(self.filepath)
            collection_name = os.path.splitext(filename)[0].replace('-', '_').replace('.', '_')
            
            self.db_client = chromadb.PersistentClient(path=db_dir)
            self.db_collection_name = collection_name
            self.db_path = db_dir
            
            try:
                collection = self.db_client.get_collection(name=collection_name)
            except:
                collection = self.db_client.create_collection(name=collection_name)
                st.success(f"Created new ChromaDB collection: {collection_name}")
            
            return collection
        except Exception as e:
            st.error(f"Error initializing ChromaDB: {e}")
            self.db_client = None
            self.db_collection_name = None
            self.db_path = None
            return None

    def update_chromadb(self):
        """Update ChromaDB with current sections (excluding TOC dictionary)"""
        if not self.sections:
            return False

        if not self.db_client or not self.db_collection_name:
            st.warning("ChromaDB not initialized. Cannot update.")
            return False
        
        try:
            collection = self.db_client.get_collection(name=self.db_collection_name)
        except Exception as e:
            st.error(f"Failed to get ChromaDB collection '{self.db_collection_name}': {e}")
            return False

        try:
            current_section_ids = [f"section_{s['title'].lower().replace(' ', '-')}_{s['line_num']}" for s in self.sections]
            if current_section_ids:
                try:
                    existing_docs = collection.get(ids=current_section_ids)
                    if existing_docs and existing_docs['ids']:
                         collection.delete(ids=existing_docs['ids'])
                except Exception:
                    pass

            documents = []
            metadatas = []
            ids = []
            
            for section in self.sections:
                document_content = f"Title: {section['title']}\nStatus: {section['status']}\nLevel: {section['level']}\n{section['content']}"
                documents.append(document_content)
                
                metadata = {
                    "type": "section_content",
                    "source_file": self.filepath,
                    "section_title": section['title'],
                    "level": section['level'],
                    "status": section['status'],
                    "line_num": section['line_num']
                }
                metadatas.append(metadata)
                
                doc_id = f"section_{section['title'].lower().replace(' ', '-')}_{section['line_num']}"
                ids.append(doc_id)
            
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                st.success(f"Updated/Added {len(documents)} sections in ChromaDB for '{os.path.basename(self.filepath)}'.")
                return True
            else:
                return False
        except Exception as e:
            st.error(f"Error updating ChromaDB with sections: {e}")
            return False

    def load_toc_from_chromadb_if_fresh(self):
        """Load the TOC dictionary from ChromaDB if it's fresh and matches the current file's modification time."""
        if not self.db_client or not self.db_collection_name:
            return False 
        try:
            collection = self.db_client.get_collection(name=self.db_collection_name)
            toc_data = collection.get(ids=["toc_dictionary"], include=["documents", "metadatas"])
            
            if toc_data and toc_data['ids'] and toc_data['ids'][0] == "toc_dictionary" and \
               toc_data['documents'] and toc_data['documents'][0] and \
               toc_data['metadatas'] and toc_data['metadatas'][0]:
                
                stored_metadata = toc_data['metadatas'][0]
                stored_file_mtime_iso = stored_metadata.get('source_file_mtime_iso')
                
                if not stored_file_mtime_iso:
                    st.info("Stored TOC in ChromaDB is missing its source file modification timestamp. Rebuilding.")
                    return False

                if not os.path.exists(self.filepath):
                    st.error(f"Source file {self.filepath} not found. Cannot verify TOC freshness.")
                    return False
                current_file_mtime = os.path.getmtime(self.filepath)
                current_file_mtime_iso_for_compare = datetime.fromtimestamp(current_file_mtime).isoformat()

                if stored_file_mtime_iso < current_file_mtime_iso_for_compare:
                    st.info(f"Markdown file '{os.path.basename(self.filepath)}' (mtime: {current_file_mtime_iso_for_compare}) is newer than stored TOC (mtime: {stored_file_mtime_iso}). Rebuilding TOC.")
                    return False
                
                self.toc_dictionary = json.loads(toc_data['documents'][0])
                return True
            else:
                return False
        except json.JSONDecodeError as e:
            st.error(f"Error decoding TOC dictionary from ChromaDB: {e}. Rebuilding.")
            self.toc_dictionary = None
            return False
        except Exception as e:
            st.error(f"Error loading TOC dictionary from ChromaDB: {e}. Rebuilding.")
            self.toc_dictionary = None
            return False

    def query_chromadb(self, query_text, n_results=5, query_filter=None):
        """Query ChromaDB for relevant sections (not TOC)."""
        if not self.db_client or not self.db_collection_name:
            if not self.init_chromadb():
                 st.error("Failed to initialize ChromaDB for query.")
                 return None
        
        try:
            collection = self.db_client.get_collection(name=self.db_collection_name)
        except Exception as e:
            st.error(f"Failed to get ChromaDB collection '{self.db_collection_name}' for query: {e}")
            return None
        
        try:
            final_filter = {"type": "section_content"}
            if query_filter:
                final_filter.update(query_filter)

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=final_filter
            )
            return results
        except Exception as e:
            st.error(f"Error querying ChromaDB: {e}")
            return None

    def parse_curl_command(self, curl_command_str):
        """Basic parsing of a curl command string into components."""
        if not curl_command_str:
            return {}

        parts = shlex.split(curl_command_str)
        if not parts or parts[0] != 'curl':
            return {}

        command_details = {'method': 'GET', 'url': '', 'headers': {}, 'data': None}
        i = 1
        while i < len(parts):
            part = parts[i]
            if part == '-X' or part == '--request':
                if i + 1 < len(parts):
                    command_details['method'] = parts[i+1].upper()
                    i += 1
            elif part == '-H' or part == '--header':
                if i + 1 < len(parts):
                    header_parts = parts[i+1].split(':', 1)
                    if len(header_parts) == 2:
                        command_details['headers'][header_parts[0].strip()] = header_parts[1].strip()
                    i += 1
            elif part == '-d' or part == '--data' or part == '--data-raw' or part == '--data-binary':
                if i + 1 < len(parts):
                    command_details['data'] = parts[i+1]
                    i += 1
            elif part.startswith('http://') or part.startswith('https://'):
                if not command_details['url']:
                    command_details['url'] = part
            i += 1
        
        if not command_details['url'] and parts[-1] not in ['-X', '-H', '-d'] and not parts[-1].startswith('-'):
             if parts[-1].startswith('http://') or parts[-1].startswith('https://'):
                command_details['url'] = parts[-1]

        return command_details

    def parse_document(self):
        """Parse the entire document and extract all relevant information."""
        if not self.content:
            if not self.load_file():
                st.error("Failed to load the Markdown file.")
                return False
            
        self.extract_headings()
        self.extract_sections()
        self.detect_placeholders()  # Run placeholder detection
        self.extract_api_endpoints()

        if not self.db_client:
            self.init_chromadb()

        toc_loaded_from_db = False
        if self.db_client and self.db_collection_name:
            if self.load_toc_from_chromadb_if_fresh():
                st.success(f"Loaded fresh TOC dictionary from ChromaDB for '{os.path.basename(self.filepath)}'.")
                toc_loaded_from_db = True
        
        if not toc_loaded_from_db:
            st.info(f"Building TOC dictionary for '{os.path.basename(self.filepath)}'.")
            self.build_section_hierarchy()

        st.info(f"Updating ChromaDB with section content for '{os.path.basename(self.filepath)}'...")
        self.update_chromadb()
            
        return True


class APIRunner:
    """Class to execute API requests based on extracted API endpoint details"""
    
    def __init__(self):
        """Initialize the API Runner"""
        self.session = requests.Session()
        self.last_response = None
        self.last_request = None
        self.history = []
    
    def execute_request(self, method, url, headers=None, params=None, data=None, json_data=None, auth=None, timeout=10):
        """Execute an HTTP request and return the response"""
        if headers is None:
            headers = {}
        
        # Add default Content-Type if sending JSON data
        if json_data and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
            
        # Store request details for later reference
        request_details = {
            'method': method,
            'url': url,
            'headers': headers,
            'params': params,
            'data': data,
            'json_data': json_data,
            'timestamp': datetime.now().isoformat()
        }
        self.last_request = request_details
        
        try:
            start_time = time.time()
            
            # Execute the request with appropriate parameters
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                auth=auth,
                timeout=timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Parse response
            try:
                response_json = response.json()
                is_json = True
            except:
                response_json = None
                is_json = False
            
            # Create response object
            response_details = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'json': response_json,
                'is_json': is_json,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.last_response = response_details
            
            # Add to history
            history_entry = {
                'request': request_details,
                'response': response_details
            }
            self.history.append(history_entry)
            
            return response_details
        
        except requests.exceptions.Timeout:
            error_response = {'error': 'Request timed out', 'status_code': 0}
            self.last_response = error_response
            return error_response
        
        except requests.exceptions.ConnectionError:
            error_response = {'error': 'Connection error', 'status_code': 0}
            self.last_response = error_response
            return error_response
        
        except Exception as e:
            error_response = {'error': str(e), 'status_code': 0}
            self.last_response = error_response
            return error_response
    
    def format_curl_command(self, method, url, headers=None, params=None, data=None, json_data=None):
        """Format a curl command based on request details"""
        if headers is None:
            headers = {}
        
        # Start with the basic curl command
        curl_parts = [f"curl -X {method.upper()}"]  
        
        # Add URL with params if any
        if params:
            # Build query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            if '?' in url:
                curl_parts.append(f"{url}&{query_string}")
            else:
                curl_parts.append(f"{url}?{query_string}")
        else:
            curl_parts.append(url)
            
        # Add headers
        for key, value in headers.items():
            curl_parts.append(f'-H "{key}: {value}"')
        
        # Add data if present
        if json_data:
            if isinstance(json_data, dict) or isinstance(json_data, list):
                json_str = json.dumps(json_data, indent=2)
                curl_parts.append(f"-d '{json_str}'")
            else:
                curl_parts.append(f"-d '{json_data}'")
        elif data:
            if isinstance(data, dict):
                data_str = '&'.join([f"{k}={v}" for k, v in data.items()])
                curl_parts.append(f"-d '{data_str}'")
            else:
                curl_parts.append(f"-d '{data}'")
        
        return " \
  ".join(curl_parts)
    
    def save_response_to_file(self, filepath, response=None):
        """Save the last response to a file"""
        if response is None:
            response = self.last_response
        
        if not response:
            st.error("No response to save")
            return False
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if response.get('is_json') and response.get('json'):
                    json.dump(response['json'], f, indent=2)
                else:
                    f.write(response.get('content', ''))
            
            st.success(f"Response saved to {filepath}")
            return True
        except Exception as e:
            st.error(f"Error saving response: {e}")
            return False


# Streamlit UI Components

def render_toc_sidebar(doc_parser):
    """Render the Table of Contents in the sidebar"""
    st.sidebar.title("API Documentation")
    
    # Add implementation status summary
    if doc_parser.implementation_status["total"] > 0:
        implemented = doc_parser.implementation_status["implemented"]
        total = doc_parser.implementation_status["total"]
        percent = (implemented / total) * 100 if total > 0 else 0
        
        st.sidebar.progress(percent / 100)
        st.sidebar.caption(f"Implementation Status: {implemented}/{total} ({percent:.1f}%)")
    
    # Add filters
    st.sidebar.subheader("Filters")
    
    # Status filter
    status_filter = st.sidebar.radio(
        "Status:",
        ["All", "✅ Implemented", "❌ Not Implemented"],
        horizontal=True
    )
    
    # Method filter if endpoints available
    method_filter = "All"
    if doc_parser.api_endpoints:
        methods = ["All"] + sorted(list(set([ep["method"] for ep in doc_parser.api_endpoints])))
        method_filter = st.sidebar.selectbox("HTTP Method:", methods)
    
    # Search filter
    search_filter = st.sidebar.text_input("Search:", "", placeholder="Filter by keyword...")
    
    # Table of Contents
    st.sidebar.subheader("Table of Contents")
    
    # Initialize expanded sections in session state if not already present
    if 'expanded_sections' not in st.session_state:
        st.session_state.expanded_sections = {}
    
    # Build TOC tree recursively with collapsible sections
    def render_toc_node(node, indent=0, path=""):
        # Skip rendering if filtered out by status
        status = node.get("status", "")
        if status:
            if status_filter == "✅ Implemented" and status != "✅":
                return
            if status_filter == "❌ Not Implemented" and status != "❌":
                return
        
        # Skip if doesn't match method filter (check api data)
        if method_filter != "All" and "api" in node and node["api"]:
            api_method = node["api"].get("method", "")
            if api_method and api_method != method_filter:
                return
            
            # For non-API nodes or parent nodes, check children
            if not api_method:
                has_matching_child = False
                for child in node.get("children", []):
                    if "api" in child and child["api"] and child["api"].get("method", "") == method_filter:
                        has_matching_child = True
                        break
                
                # Always show level 1 and 2 categories, filter others if no matching children
                if not has_matching_child and node.get("level", 0) > 2:
                    return
        
        # Skip if doesn't match search filter
        name = node.get("name", "")
        if search_filter and name:
            if search_filter.lower() not in name.lower():
                # Check if any child matches
                has_matching_child = False
                for child in node.get("children", []):
                    if search_filter.lower() in child.get("name", "").lower():
                        has_matching_child = True
                        break
                if not has_matching_child:
                    return
        
        # Render the node
        if "name" in node:
            node_level = node.get("level", 0)
            node_path = f"{path}/{name}" if path else name
            has_children = len(node.get("children", [])) > 0
            is_last = node.get("is_last", False)
            
            # Determine if this section should be expanded
            if node_path not in st.session_state.expanded_sections:
                # Level 1 nodes start expanded by default
                st.session_state.expanded_sections[node_path] = (node_level == 1)
            
            # Create a unique key for the component
            component_key = f"toc_{node_path}_{node.get('line_num', 0)}"
            
            # Indent based on level
            indent_str = "&nbsp;" * (indent * 2)
            
            # All headings are collapsible, but only last level headings are clickable for content display
            if has_children or not is_last:
                # Create an expander-like button that toggles the expanded state
                expander_icon = "▼" if st.session_state.expanded_sections[node_path] else "►"
                expander_label = f"{indent_str}{expander_icon} {status} {name}"
                
                if st.sidebar.button(expander_label, key=f"exp_{component_key}"):
                    # Toggle the expanded state
                    st.session_state.expanded_sections[node_path] = not st.session_state.expanded_sections[node_path]
                    st.rerun()
                
                # If expanded, render the children
                if st.session_state.expanded_sections[node_path]:
                    for child in node.get("children", []):
                        render_toc_node(child, indent + 1, node_path)
            
            # For last level headings, create a clickable button to display content
            if is_last:
                leaf_label = f"{indent_str}{status} {name}"
                if st.sidebar.button(leaf_label, key=component_key):
                    # Convert toc node format to section_hierarchy node format for compatibility
                    converted_node = {
                        "title": name,
                        "status": status,
                        "level": node_level,
                        "children": [],
                        "is_last": True
                    }
                    
                    # If this is an API endpoint, add the API info
                    if "api" in node and node["api"]:
                        for api in doc_parser.api_endpoints:
                            if api["title"] == name:
                                converted_node.update(api)
                                break
                    
                    # Store the selected node in session state
                    st.session_state.selected_node = converted_node
                    st.rerun() # Ensure main panel updates immediately
    
    # Check if all headings are present in the TOC
    def validate_toc_headings(toc_data, headings):
        """Validate that all headings in the document are in the TOC dictionary"""
        # Extract all heading titles from the TOC dictionary
        toc_titles = set()
        
        def extract_titles(node):
            if "name" in node:
                toc_titles.add(node["name"])
            for child in node.get("children", []):
                extract_titles(child)
        
        extract_titles(toc_data)
        
        # Compare with actual headings
        heading_titles = set([h["title"] for h in headings])
        missing_headings = heading_titles - toc_titles
        extra_headings = toc_titles - heading_titles
        
        if missing_headings:
            st.sidebar.warning(f"⚠️ {len(missing_headings)} headings missing from TOC")
        if extra_headings:
            st.sidebar.warning(f"⚠️ {len(extra_headings)} extra headings in TOC")
        
        return len(missing_headings) == 0 and len(extra_headings) == 0
    
    # If the TOC dictionary exists, use it for rendering
    if hasattr(doc_parser, 'toc_dictionary') and doc_parser.toc_dictionary:
        toc_data = doc_parser.toc_dictionary.get("toc", {})
        if toc_data:
            # Validate TOC headings before rendering
            validate_toc_headings(toc_data, doc_parser.headings)
            render_toc_node(toc_data, indent=0)
    else:
        # Fall back to the original section hierarchy rendering
        # First, determine the maximum heading level in the document
        max_level = 0
        for heading in doc_parser.headings:
            max_level = max(max_level, heading.get("level", 0))
        
        # Build the TOC dictionary if it doesn't exist
        doc_parser.build_toc_dictionary()
        
        # Then render the TOC using the new format
        if hasattr(doc_parser, 'toc_dictionary') and doc_parser.toc_dictionary:
            toc_data = doc_parser.toc_dictionary.get("toc", {})
            if toc_data:
                # Validate TOC headings before rendering
                validate_toc_headings(toc_data, doc_parser.headings)
                render_toc_node(toc_data, indent=0)


def render_api_runner(api_endpoint, api_runner):
    """Render the API runner interface for a specific endpoint"""
    st.subheader(f"{api_endpoint['status']} {api_endpoint['title']}")
    
    # Create tabs for Documentation, Request, and Response
    doc_tab, request_tab, response_tab = st.tabs(["Documentation", "Request", "Response"])
    
    with doc_tab:
        st.markdown(f"Endpoint: `{api_endpoint['endpoint']}`")
        st.markdown(f"Status: {api_endpoint['status']}")
        
        # Display documentation content
        st.markdown(api_endpoint['section_content'])
        
        # Display curl command if available
        if api_endpoint['curl_command']:
            st.subheader("Example cURL Command")
            st.code(api_endpoint['curl_command'], language="bash")
        
        # Display response example if available
        if api_endpoint['response_example']:
            st.subheader("Example Response")
            if isinstance(api_endpoint['response_example'], (dict, list)):
                st.json(api_endpoint['response_example'])
            else:
                st.code(api_endpoint['response_example'], language="json")
    
    with request_tab:
        # Parse the curl command if available
        curl_details = {}
        if api_endpoint['curl_command']:
            curl_details = api_runner.parse_curl_command(api_endpoint['curl_command'])
        
        # Method selection
        method = st.selectbox(
            "HTTP Method",
            ["GET", "POST", "PUT", "DELETE", "PATCH"],
            index=["GET", "POST", "PUT", "DELETE", "PATCH"].index(api_endpoint['method'])
        )
        
        # URL input
        default_url = curl_details.get('url', api_endpoint['path'])
        if not default_url.startswith('http'):
            # Add a default base URL if path is relative
            default_url = f"http://localhost:8000{default_url}"
        url = st.text_input("URL", value=default_url)
        
        # Headers input
        st.subheader("Headers")
        default_headers = curl_details.get('headers', {})
        if 'Content-Type' not in default_headers and method in ['POST', 'PUT', 'PATCH']:
            default_headers['Content-Type'] = 'application/json'
        
        headers_count = st.number_input("Number of Headers", min_value=0, value=len(default_headers), step=1)
        headers = {}
        
        if headers_count > 0:
            # Create a container for the headers form
            headers_container = st.container()
            
            with headers_container:
                # Create two columns for key-value pairs
                for i in range(headers_count):
                    col1, col2 = st.columns([1, 2])
                    
                    # Get the i-th header key-value pair if it exists
                    default_key = list(default_headers.keys())[i] if i < len(default_headers) else ""
                    default_value = default_headers.get(default_key, "") if i < len(default_headers) else ""
                    
                    with col1:
                        key = st.text_input(f"Header {i+1} Key", value=default_key, key=f"header_key_{i}")
                    with col2:
                        value = st.text_input(f"Header {i+1} Value", value=default_value, key=f"header_value_{i}")
                    
                    if key:  # Only add if key is not empty
                        headers[key] = value
        
        # Request body for POST, PUT, PATCH
        if method in ['POST', 'PUT', 'PATCH']:
            st.subheader("Request Body")
            body_type = st.radio("Body Type", ["JSON", "Form Data", "Raw"], horizontal=True)
            
            if body_type == "JSON":
                # Get default JSON body
                default_json = curl_details.get('data', api_endpoint.get('request_body', {}))
                if default_json and not isinstance(default_json, (dict, list)):
                    try:
                        default_json = json.loads(default_json)
                    except:
                        default_json = {}
                
                # Convert to pretty JSON string for display
                if default_json:
                    default_json_str = json.dumps(default_json, indent=2)
                else:
                    default_json_str = "{}"
                    
                json_body = st.text_area("JSON Body", value=default_json_str, height=200)
                try:
                    json_data = json.loads(json_body)
                    form_data = None
                    raw_data = None
                except:
                    st.error("Invalid JSON format")
                    json_data = None
                    form_data = None
                    raw_data = json_body
            
            elif body_type == "Form Data":
                # Create form data fields
                form_fields_count = st.number_input("Number of Form Fields", min_value=0, value=1, step=1)
                form_data = {}
                json_data = None
                raw_data = None
                
                if form_fields_count > 0:
                    # Create a container for the form fields
                    form_container = st.container()
                    
                    with form_container:
                        # Create two columns for key-value pairs
                        for i in range(form_fields_count):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                key = st.text_input(f"Field {i+1} Key", key=f"form_key_{i}")
                            with col2:
                                value = st.text_input(f"Field {i+1} Value", key=f"form_value_{i}")
                            
                            if key:  # Only add if key is not empty
                                form_data[key] = value
            
            else:  # Raw body
                raw_data = st.text_area("Raw Body", height=200)
                json_data = None
                form_data = None
        else:  # GET, DELETE don't have body
            json_data = None
            form_data = None
            raw_data = None
        
        # Query parameters
        st.subheader("Query Parameters")
        query_params_count = st.number_input("Number of Query Parameters", min_value=0, value=0, step=1)
        params = {}
        
        if query_params_count > 0:
            # Create a container for the query parameters
            params_container = st.container()
            
            with params_container:
                # Create two columns for key-value pairs
                for i in range(query_params_count):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        key = st.text_input(f"Parameter {i+1} Key", key=f"param_key_{i}")
                    with col2:
                        value = st.text_input(f"Parameter {i+1} Value", key=f"param_value_{i}")
                    
                    if key:  # Only add if key is not empty
                        params[key] = value
        
        # Execute button
        if st.button("Execute Request", type="primary"):
            with st.spinner("Executing request..."):
                response = api_runner.execute_request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=form_data or raw_data,
                    json_data=json_data
                )
                
                # Store the response in session state
                st.session_state.last_response = response
                
                # Switch to the response tab
                st.session_state.active_tab = "Response"
    
    with response_tab:
        # Display response if available
        if hasattr(st.session_state, 'last_response') and st.session_state.last_response:
            response = st.session_state.last_response
            
            # Status code and execution time
            status_code = response.get('status_code', 0)
            execution_time = response.get('execution_time', 0)
            
            # Color based on status
            if status_code >= 200 and status_code < 300:
                status_color = "green"
            elif status_code >= 300 and status_code < 400:
                status_color = "blue"
            elif status_code >= 400 and status_code < 500:
                status_color = "orange"
            else:
                status_color = "red"
            
            # Display status and time
            st.markdown(f"<h3 style='color: {status_color};'>Status: {status_code}</h3>", unsafe_allow_html=True)
            st.markdown(f"Execution Time: {execution_time:.2f} seconds")
            
            # Response headers
            with st.expander("Response Headers"):
                if 'headers' in response:
                    for key, value in response['headers'].items():
                        st.text(f"{key}: {value}")
            
            # Response body
            st.subheader("Response Body")
            if response.get('is_json') and response.get('json'):
                # Pretty print JSON
                st.json(response['json'])
                
                # Option to save response
                if st.button("Save Response to File"):
                    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses")
                    os.makedirs(save_path, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"response_{timestamp}.json"
                    filepath = os.path.join(save_path, filename)
                    
                    if api_runner.save_response_to_file(filepath, response):
                        st.download_button(
                            label="Download Response",
                            data=json.dumps(response['json'], indent=2),
                            file_name=filename,
                            mime="application/json"
                        )
            else:
                # Raw text response
                st.text_area("Raw Response", value=response.get('content', ''), height=300)


# Main application function
def main():
    """Main entry point for the Streamlit application"""
    # Set page configuration
    st.set_page_config(
        page_title="Prbal API Documentation Runner",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("Prbal API Documentation Runner")
    st.markdown(
        """This application allows you to browse and test the Prbal API endpoints directly from the documentation.
        Select an endpoint from the sidebar to view its documentation and test it using the API runner."""
    )
    
    # Path to the API documentation file
    api_doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Prbal-API.md")
    
    # Initialize session state for tracking selected node and response
    if 'selected_node' not in st.session_state:
        st.session_state.selected_node = None
    if 'last_response' not in st.session_state:
        st.session_state.last_response = None
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Documentation"
    
    # Initialize API document parser and runner
    doc_parser = APIDocParser(api_doc_path)
    api_runner = APIRunner()
    
    # Load and parse the API documentation
    if not doc_parser.content:
        doc_parser.load_file()
        doc_parser.parse_document()
    
    # Render the Table of Contents sidebar
    render_toc_sidebar(doc_parser)
    
    # Main content area
    if st.session_state.selected_node:
        # Find the selected API endpoint
        selected_title = st.session_state.selected_node.get("title")
        selected_api = None
        
        for api in doc_parser.api_endpoints:
            if api["title"] == selected_title:
                selected_api = api
                break
        
        if selected_api:
            # Render the API runner for the selected endpoint
            render_api_runner(selected_api, api_runner)
        else:
            # Display section content if it's not an API endpoint
            st.header(f"{st.session_state.selected_node.get('status', '')} {selected_title}")
            
            # Find the section content
            for section in doc_parser.sections:
                if section["title"] == selected_title:
                    st.markdown(section["content"])
                    break
            
            # Show child sections/endpoints if any
            children = st.session_state.selected_node.get("children", [])
            if children:
                st.subheader("Endpoints in this section:")
                for child in children:
                    child_title = child.get("title", "")
                    child_status = child.get("status", "")
                    
                    # Create a clickable card for each child
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"### {child_status}")
                    with col2:
                        if st.button(child_title, key=f"child_{child_title}"):
                            st.session_state.selected_node = child
                            st.rerun()
    else:
        # Show welcome message if no endpoint is selected
        st.info("👈 Select an API endpoint from the sidebar to view its documentation and test it.")
        
        # Show overall statistics
        st.subheader("API Documentation Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_endpoints = len(doc_parser.api_endpoints)
            st.metric("Total Endpoints", total_endpoints)
        
        with col2:
            implemented = doc_parser.implementation_status["implemented"]
            st.metric("Implemented Endpoints", implemented)
        
        with col3:
            not_implemented = doc_parser.implementation_status["total"] - doc_parser.implementation_status["implemented"]
            st.metric("Not Implemented", not_implemented)
        
        # Show method distribution
        if doc_parser.api_endpoints:
            st.subheader("HTTP Method Distribution")
            method_counts = defaultdict(int)
            for ep in doc_parser.api_endpoints:
                method_counts[ep["method"]] += 1
            
            # Create a DataFrame for visualization
            method_df = pd.DataFrame({
                "Method": list(method_counts.keys()),
                "Count": list(method_counts.values())
            })
            
            # Display as a bar chart
            st.bar_chart(method_df.set_index("Method"))
        
        # Add search functionality
        st.subheader("Search Documentation")
        search_query = st.text_input("Search for API endpoints:", placeholder="Enter keywords...")
        if search_query:
            # Search using ChromaDB for semantic search
            results = doc_parser.query_chromadb(search_query, n_results=5)
            
            if results and results["documents"]:
                st.subheader("Search Results")
                for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                    with st.expander(f"{metadata.get('status', '')} {metadata.get('section_title', 'Result '+str(i+1))}"):
                        st.markdown(doc)
                        st.caption(f"Line: {metadata.get('line_num', 'N/A')}")
                        
                        # Find matching API endpoint
                        matching_api = None
                        for api in doc_parser.api_endpoints:
                            if api["title"] == metadata.get("section_title"):
                                matching_api = api
                                break
                        
                        if matching_api:
                            if st.button(f"View API Runner", key=f"search_result_{i}"):
                                # Find the corresponding node
                                for node in doc_parser.headings:
                                    if node["title"] == metadata.get("section_title"):
                                        st.session_state.selected_node = node
                                        st.rerun()
                                        break


# Run the application
if __name__ == "__main__":
    main()

'''
toc={
{
    "name":"Authentication",
    "level":1,
    "is_last":false,
    "children":[
        {
            "name":"User Registration",
            "level":2,
            "is_last":false,
            "children":[
                {
                    "name":"Generic User Registration",
                    "level":3,
                    "is_last":false,
                    "children":[
                        {
                            "name":"Customer Specific Registration",
                            "level":4,
                            "is_last":true,
                            "api":{}
                        },
                        {
                            "name":"Provider Specific Registration",
                            "level":4,
                            "is_last":true,
                            "api":{}
                        },
                        {
                            "name":"Admin Specific Registration",
                            "level":4,
                            "is_last":true,
                            "api":{}
                        }
                    ]
                }
            ]
        },
        {
            "name":"User Logout",
            "level":2,
            "is_last":true,
            "api":{}
        },
        {
            "name":"Access Token Management",
            "level":2,
            "is_last":true,
            "children":[
                {
                    "name":"List User's Access Tokens",
                    "level":3,
                    "is_last":true,
                    "api":{}
                },
                {
                    "name":"Revoke Specific Access Token",
                    "level":3,
                    "is_last":true,
                    "api":{}
                }
            ]
        },
        {
            "name":"User Management",
            "level":2,
            "is_last":true,
            "children":[
                {
                    "name":"Generic User Endpoints",
                    "level":3,
                    "is_last":true,
                    "api":{}
                },
                {
                    "name":"Customer Specific Endpoints",
                    "level":3,
                    "is_last":true,
                    "api":{}
                },
                {
                    "name":"Provider Specific Endpoints",
                    "level":3,
                    "is_last":true,
                    "api":{}
                },
                {
                    "name":"Admin Specific Endpoints (Profile)",
                    "level":3,
                    "is_last":true,
                    "api":{}
                }
            ]
        },{},{} ....
    ]
}
'''

'''
sample of md file structurelearn and understand and analysis my flutter android app "prbal" in deeply for Enhancements :

### Why this structure works with [ai_gent_backend.py](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:0:0-0:0):

1.  Headings (`## ✅ Get User Data`):
    *   The script's [extract_headings()](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:89:4-114:28) and [extract_sections()](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:148:4-171:28) methods use regex to find lines starting with `#` (e.g., `##`, `###`).
    *   It expects a status emoji (✅ or ❌) immediately after the hashmarks and a space.
    *   The title is captured from here. This title is crucial because the script matches the selected TOC item's title with the parsed API endpoint's title to display the runner.

2.  `Endpoint: 'METHOD /path':
    *   The [extract_api_endpoints()](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:209:4-293:33) method specifically looks for the bolded string `Endpoint:` followed by the method and path enclosed in backticks.
    *   Example: `Endpoint: 'GET /api/users/{id}'`

3.  `Request Body:' (for POST, PUT, etc.):
    *   If your endpoint accepts a request body, use the bolded string `Request Body:` followed by a JSON code block.
    *   Example:
        ```markdown
        Request Body:
        ```json
        {
          "key": "value"
        }
        ```
        ```

4.  `[curl](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:400:4-436:9) Command::
    *   The script looks for `[curl](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:400:4-436:9) Command:` followed by a `bash` code block containing the curl command.
    *   Example:
        ```markdown
        [curl](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:400:4-436:9) Command:
        ```bash
        curl -X GET http://example.com/api/resource
        ```
        ```

5.  `Possible Output Response (Success/Error...)::
    *   This pattern is used to extract example responses.
    *   Example:
        ```markdown
        Possible Output Response (Success 200 OK):
        ```json
        {
          "message": "Success"
        }
        ```
        ```

6.  Section Content:
    *   All details for an API endpoint (Endpoint, Request Body, Curl Command, Responses) must be *within the same section*, i.e., under the same heading and before the next heading of the same or higher level.

To use this sample:

1.  Save the content above into a new [.md](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/Prbal-API.md:0:0-0:0) file (e.g., `sample-api.md`) in the same directory as [ai_gent_backend.py](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:0:0-0:0).
2.  Modify the `api_doc_path` in your [ai_gent_backend.py](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:0:0-0:0) script (around line 1001 in your [main()](cci:1://file:///d:/durgas/Prbal-App/Prbal_backend/postman/ai_gent_backend.py:983:0-1127:45) function) to point to this new `sample-api.md` file:
    ```python
    # api_doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Prbal-API.md") # Old
    api_doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-api.md") # New
    ```
3.  Run your Streamlit application.

If this sample file works and displays the APIs correctly, it indicates that the structure or specific details within your [Prbal-API.md](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/Prbal-API.md:0:0-0:0) might have subtle differences that prevent correct parsing for some endpoints. You can then compare your [Prbal-API.md](cci:7://file:///d:/durgas/Prbal-App/Prbal_backend/postman/Prbal-API.md:0:0-0:0) sections against this sample to identify and correct those differences.

If this sample *also* fails to display APIs correctly, the issue might be deeper within the Python script's logic for selecting or rendering API details, beyond just the Markdown parsing. 
'''