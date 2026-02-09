import http.server
import random
import urllib.parse

class DummyAIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, _, *args):
        # Override this to suppresses all logging
        return

    def do_GET(self):
        # Parse the URL to simulate reading the 'board' parameter
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        # We don't actually need the board, but this mimics the real server's behavior
        board_data = params.get('board', [''])[0]
        print(f"board={board_data}")
        
        # Move options and weights
        moves = ['u', 'l', 'r', 'd']
        weights = [55, 25, 15, 5]
        
        # Select move based on probabilities
        selected_move = random.choices(moves, weights=weights, k=1)[0]
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*') # For browser-based testing
        self.end_headers()
        self.wfile.write(selected_move.encode())

if __name__ == "__main__":
    print("Starting Dummy 2048 AI Server on http://localhost:8080...")
    server = http.server.HTTPServer(('localhost', 8080), DummyAIHandler)
    server.serve_forever()