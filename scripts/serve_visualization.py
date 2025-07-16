#!/usr/bin/env python3
"""
Simple HTTP server for IETF Weavers visualization.
Run this script to serve the visualization locally.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

def serve_visualization(port=8000):
    """Start HTTP server and open visualization in browser."""
    
    # Change to visualisation directory
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vis_dir = os.path.join(script_dir, 'visualisation')
    
    if not os.path.exists(vis_dir):
        print(f"❌ Visualisation directory not found: {vis_dir}")
        return
    
    os.chdir(vis_dir)
    
    # Check if data.json exists
    if not os.path.exists('data.json'):
        print("⚠️  data.json not found. Please run the pipeline first:")
        print("   python src/main.py data/sample_emails.json")
        return
    
    try:
        # Start server
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), handler)
        httpd.server_close()  # Test if port is available
        httpd = socketserver.TCPServer(("", port), handler)
        
        print(f"🚀 Starting IETF Weavers visualization server...")
        print(f"📊 Server running at: http://localhost:{port}")
        print(f"🌐 Opening in browser...")
        print(f"⏹️  Press Ctrl+C to stop the server")
        
        # Open browser
        webbrowser.open(f'http://localhost:{port}/index.html')
        
        # Start serving
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped.")
        httpd.shutdown()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"⚠️  Port {port} is already in use. Try a different port:")
            print(f"   python serve_visualization.py --port 8001")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Serve IETF Weavers visualization')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    
    args = parser.parse_args()
    serve_visualization(args.port)
