import os
import requests
import uuid
from flask import Flask, render_template, request, jsonify, Response
from duckduckgo_search import DDGS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Global cache for search generators
# format: { 'uuid': generator_object }
SEARCH_SESSIONS = {}

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
    return results

@app.route('/api/search', methods=['GET'])
def search_images():
    query = request.args.get('q', '')
    size = request.args.get('size', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        ddgs = DDGS()
        
        # Handle custom high-res triggers
        search_size = size
        search_query = query
        
        if size in ['2k', '4k', '8k']:
            search_query = f"{query} {size} wallpaper"
            search_size = "Wallpaper" 
            
        # The library returns a list even with max_results=None
        # We fetch a large batch (e.g. 500) and then iterate over it
        ddgs_results = ddgs.images(
            keywords=search_query,
            region="wt-wt",
            safesearch="off",
            size=search_size if search_size else None,
            max_results=500, # Fetch a reasonable upper limit
        )
        
        # Convert list to iterator so our get_next_batch logic works
        ddgs_gen = iter(ddgs_results)
        
        # Create session
        session_id = str(uuid.uuid4())
        SEARCH_SESSIONS[session_id] = ddgs_gen
        
        # Get first batch
        results = get_next_batch(ddgs_gen, count=30)
            
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
