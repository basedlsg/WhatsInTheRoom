#!/usr/bin/env python3
"""
Simple HTTP server for the Human Baseline Study.
Serves the HTML interface and handles data saving.
"""

import http.server
import socketserver
import json
import os
import random
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Configuration
PORT = 8001
DATA_DIR = "data/human_study"
BENCHMARK_DIR = "data/floorplan_qa_benchmark"

# Ensure directories exist
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

class StudyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"DEBUG: Request path: {self.path}")
        # Serve the main interface
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('src/human_study/index.html', 'rb') as f:
                self.wfile.write(f.read())
            return
            
        # API to get trials
        if self.path == '/api/trials':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Load benchmark index
            try:
                with open(f"{BENCHMARK_DIR}/dataset_index.json", 'r') as f:
                    dataset = json.load(f)
                
                # Select balanced subset (mock logic for now - just take first 30)
                # In production, this would implement the balanced sampling logic
                subset = dataset[:30]
                
                trials = []
                for entry in subset:
                    trials.append({
                        "id": entry["floorplan_id"],
                        "image": "/" + entry["image_path"] # Serve from root
                    })
                
                self.wfile.write(json.dumps(trials).encode())
            except Exception as e:
                print(f"Error loading trials: {e}")
                self.wfile.write(json.dumps([]).encode())
            return

        # Serve images from the data directory
        if self.path.startswith('/data/'):
            # Allow access to data directory for images
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            response_data = json.loads(post_data.decode('utf-8'))
            
            # Save response
            participant_id = response_data.get('participant_id', 'unknown')
            filename = f"{DATA_DIR}/{participant_id}.jsonl"
            
            with open(filename, 'a') as f:
                f.write(json.dumps(response_data) + "\n")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            return

print(f"Starting Human Study Server at http://localhost:{PORT}")
print(f"Saving data to: {DATA_DIR}")

with socketserver.TCPServer(("", PORT), StudyHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
