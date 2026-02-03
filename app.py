import os
import requests
import uuid
import re
import json
from flask import Flask, render_template, request, jsonify, Response
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Global cache for search generators
# format: { 'uuid': generator_object }
SEARCH_SESSIONS = {}

class BingImageSearch:
    def __init__(self, query):
        self.query = query
        self.offset = 1  # Bing starts at 1
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def __iter__(self):
        return self

    def __next__(self):
        # We need to fetch batches. 
        # Since this iterator is called one by one, we should buffer results.
        # But for simplicity, we can fetch on demand if the buffer is empty.
        # However, the previous architecture expected a generator that yields individual items.
        # Let's implement that properly.
        if not hasattr(self, '_buffer'):
            self._buffer = []
        
        while not self._buffer:
            new_results = self._fetch_more()
            if not new_results:
                raise StopIteration
            self._buffer.extend(new_results)
        
        return self._buffer.pop(0)

    def _fetch_more(self):
        # Limit to 1000 results to avoid infinite loops behaving badly
        if self.offset > 1000:
            return []

        url = "https://www.bing.com/images/search"
        params = {
            'q': self.query,
            'form': 'HDRSC2',
            'first': self.offset,
            'scenario': 'ImageBasicHover'
        }
        
        try:
            print(f"Fetching Bing offset {self.offset}...")
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            # Extract links
            # Bing behavior: murl matches
            links = re.findall(r'murl&quot;:&quot;([^&]+)&quot;', resp.text)
            if not links:
                 links = re.findall(r'"murl":"([^"]+)"', resp.text)
            
            # Also try to extract titles/source if possible, but links are priority
            # For simplest regex, we just get links.
            
            formatted_results = []
            for link in links:
                formatted_results.append({
                    'image': link,
                    'thumbnail': link, # Use same for now, or finding turl is harder with regex
                    'title': 'Image',
                    'source': 'Bing',
                    'url': link,
                    'width': 0,
                    'height': 0
                })
            
            if not formatted_results:
                return []
                
            self.offset += len(formatted_results)
            return formatted_results
            
        except Exception as e:
            print(f"Bing search error: {e}")
            return []

@app.route('/')
def index():
    return render_template('index.html')

def get_next_batch(gen, count=30):
    results = []
    try:
        for _ in range(count):
            r = next(gen)
            results.append({
                'image': r.get('image'),
                'thumbnail': r.get('thumbnail'),
                'title': r.get('title'),
                'source': r.get('source'),
                'url': r.get('url'),
                'width': r.get('width'),
                'height': r.get('height')
            })
    except StopIteration:
        pass
    except Exception as e:
        print(f"Error iterating: {e}")
    return results

@app.route('/api/search', methods=['GET'])
def search_images():
    query = request.args.get('q', '')
    size = request.args.get('size', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Handle custom high-res triggers
        search_query = query
        if size in ['2k', '4k', '8k']:
            search_query = f"{query} {size} wallpaper"
            
        # Create Bing generator
        bing_gen = BingImageSearch(search_query)
        
        # Create session
        session_id = str(uuid.uuid4())
        SEARCH_SESSIONS[session_id] = bing_gen
        
        # Get first batch
        results = get_next_batch(bing_gen, count=30)
            
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'results': results, 'session_id': session_id})

@app.route('/api/more', methods=['GET'])
def search_more():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in SEARCH_SESSIONS:
        return jsonify({'error': 'Invalid or expired session'}), 400
        
    try:
        gen = SEARCH_SESSIONS[session_id]
        results = get_next_batch(gen, count=30)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    return jsonify({'results': results})

@app.route('/api/proxy_download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    try:
        # Stream the file from the source to the client
        r = requests.get(url, stream=True, timeout=15)
        r.raise_for_status()
        
        # Extract filename
        filename = url.split('/')[-1].split('?')[0]
        if not filename or len(filename) > 50: 
            filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
        
        # Ensure it has an extension
        if '.' not in filename: filename += ".jpg"
            
        return Response(
            r.iter_content(chunk_size=8192),
            content_type=r.headers.get('Content-Type', 'image/jpeg'),
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return str(e), 500

def download_single_image(url):
    try:
        # Get filename from URL or default
        filename = url.split('/')[-1].split('?')[0]
        if not filename or len(filename) > 200:
            filename = f"image_{abs(hash(url))}.jpg"
            
        # Ensure extension
        if '.' not in filename:
             filename += ".jpg"
             
        # Sanitize filename
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._- ']).strip()
        
        save_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Avoid overwrites
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(save_path):
            save_path = os.path.join(DOWNLOAD_FOLDER, f"{base_name}_{counter}{ext}")
            counter += 1

        response = requests.get(url, timeout=15, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return {'url': url, 'status': 'success', 'path': save_path}
    except Exception as e:
        return {'url': url, 'status': 'error', 'error': str(e)}

@app.route('/api/download', methods=['POST'])
def download_images():
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
        
    results = []
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(download_single_image, urls))
        
    return jsonify({'results': results})

if __name__ == '__main__':
    # Listen on all interfaces
    app.run(host='0.0.0.0', debug=True, port=5000)
