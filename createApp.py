import os
import sys

def create_app_files():
    """Create all files for the File Search Pro application"""
    
    # Create main directory
    app_dir = "file_search_app"
    templates_dir = os.path.join(app_dir, "templates")
    
    # Create directories
    os.makedirs(templates_dir, exist_ok=True)
    
    print(f"📁 Creating application in: {os.path.abspath(app_dir)}")
    
    # ============================================
    # FILE 1: app.py
    # ============================================
    app_py = '''from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Store search results globally for progress tracking
search_status = {
    'is_searching': False,
    'progress': 0,
    'total_files': 0,
    'current_file': '',
    'results': [],
    'total_found': 0
}

def format_size(size):
    """Format file size to human readable format"""
    if size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_file_info(filepath):
    """Get file information including modification time and size"""
    try:
        stat_info = os.stat(filepath)
        return {
            'path': filepath,
            'name': os.path.basename(filepath),
            'directory': os.path.dirname(filepath),
            'size': stat_info.st_size,
            'size_formatted': format_size(stat_info.st_size),
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'modified_formatted': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        }
    except (OSError, FileNotFoundError, PermissionError):
        return None

def search_files_async(directory, filename):
    """Perform the actual file search"""
    global search_status
    
    results = []
    total_files_checked = 0
    files_found = 0
    
    search_status['is_searching'] = True
    search_status['progress'] = 0
    search_status['total_files'] = 0
    search_status['results'] = []
    search_status['total_found'] = 0
    
    total_files = 0
    try:
        for root, dirs, files in os.walk(directory):
            total_files += len(files)
    except Exception:
        pass
    
    search_status['total_files'] = total_files
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                total_files_checked += 1
                search_status['current_file'] = file
                
                if total_files > 0:
                    search_status['progress'] = int((total_files_checked / total_files) * 100)
                
                if filename.lower() in file.lower():
                    full_path = os.path.join(root, file)
                    file_info = get_file_info(full_path)
                    if file_info:
                        results.append(file_info)
                        files_found += 1
                
                if total_files_checked % 100 == 0:
                    time.sleep(0.01)
                    
    except Exception as e:
        print(f"Error during search: {e}")
    
    results.sort(key=lambda x: x['modified'], reverse=True)
    
    search_status['results'] = results
    search_status['is_searching'] = False
    search_status['progress'] = 100
    search_status['total_found'] = files_found

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    global search_status
    
    data = request.json
    directory = data.get('directory', '').strip()
    filename = data.get('filename', '').strip()
    
    if not directory or not filename:
        return jsonify({'error': 'Directory and filename are required'}), 400
    
    directory = os.path.expanduser(directory)
    
    if not os.path.exists(directory):
        return jsonify({'error': f'Directory "{directory}" does not exist'}), 400
    
    if not os.path.isdir(directory):
        return jsonify({'error': f'"{directory}" is not a directory'}), 400
    
    search_status['is_searching'] = True
    search_status['results'] = []
    search_status['progress'] = 0
    search_status['total_found'] = 0
    
    thread = threading.Thread(target=search_files_async, args=(directory, filename))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'Search started'})

@app.route('/api/status', methods=['GET'])
def get_status():
    global search_status
    return jsonify({
        'is_searching': search_status.get('is_searching', False),
        'progress': search_status.get('progress', 0),
        'total_files': search_status.get('total_files', 0),
        'current_file': search_status.get('current_file', ''),
        'total_found': search_status.get('total_found', 0)
    })

@app.route('/api/results', methods=['GET'])
def get_results():
    global search_status
    results = search_status.get('results', [])
    total_size = sum(r.get('size', 0) for r in results)
    folders = set(r.get('directory', '') for r in results)
    
    return jsonify({
        'results': results,
        'total': len(results),
        'total_size': total_size,
        'total_size_formatted': format_size(total_size),
        'unique_folders': len(folders)
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("📁 File Search Pro - Server Starting...")
    print("="*60)
    print(f"🌐 Server URL: http://localhost:5000")
    print("="*60)
    print("Press CTRL+C to stop the server\\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
'''

    with open(os.path.join(app_dir, 'app.py'), 'w', encoding='utf-8') as f:
        f.write(app_py.strip())
    print("✅ Created app.py")

    # ============================================
    # FILE 2: index.html (in templates folder)
    # ============================================
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Search Pro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            flex-wrap: wrap;
            gap: 15px;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .logo-icon {
            font-size: 36px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 12px;
            border-radius: 12px;
            color: white;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .logo-text h1 {
            font-size: 28px;
            color: #2d3748;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo-text p {
            color: #718096;
            font-size: 14px;
            -webkit-text-fill-color: #718096;
        }
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            border-radius: 20px;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #48bb78;
            transition: all 0.3s;
        }
        .status-dot.searching {
            background: #ed8936;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }
        .search-section {
            background: #f7fafc;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            border: 2px solid #e2e8f0;
        }
        .search-grid {
            display: grid;
            grid-template-columns: 2fr 1fr auto;
            gap: 15px;
            align-items: end;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .form-group label {
            font-weight: 600;
            color: #4a5568;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .form-group input {
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
            background: white;
            width: 100%;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
            height: 48px;
            min-width: 140px;
        }
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102,126,234,0.4);
        }
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .progress-container {
            margin-top: 15px;
            display: none;
        }
        .progress-container.active {
            display: block;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
        }
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0 30px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
        }
        .stat-label {
            color: #718096;
            font-size: 14px;
            margin-top: 5px;
        }
        .results-section {
            margin-top: 30px;
        }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .results-count {
            color: #718096;
            font-size: 14px;
            background: #f7fafc;
            padding: 4px 12px;
            border-radius: 20px;
        }
        .result-item {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
            cursor: pointer;
        }
        .result-item:hover {
            border-color: #667eea;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        .result-item.latest {
            border-left: 5px solid #48bb78;
            background: #f0fff4;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .result-title {
            font-weight: 600;
            color: #2d3748;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .result-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-latest {
            background: #48bb78;
            color: white;
        }
        .badge-old {
            background: #718096;
            color: white;
        }
        .result-path {
            color: #718096;
            font-size: 13px;
            margin-bottom: 8px;
            word-break: break-all;
            font-family: monospace;
        }
        .result-details {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            color: #718096;
            font-size: 13px;
        }
        .result-details span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #718096;
        }
        .no-results .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        .error-message {
            background: #fed7d7;
            color: #9b2c2c;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
            border-left: 4px solid #fc8181;
        }
        .error-message.active {
            display: block;
        }
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.6s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .btn-text {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .shortcuts {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .shortcut-tip {
            background: #edf2f7;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            color: #4a5568;
        }
        @media (max-width: 768px) {
            .search-grid {
                grid-template-columns: 1fr;
            }
            .stats-bar {
                grid-template-columns: 1fr 1fr;
            }
            .container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <div class="logo-icon">📁</div>
                <div class="logo-text">
                    <h1>FileSearch Pro</h1>
                    <p>Find the latest version of your files instantly</p>
                </div>
            </div>
            <div class="status-indicator">
                <span class="status-dot" id="statusDot"></span>
                <span id="statusText" style="font-size: 14px; font-weight: 500;">Ready</span>
            </div>
        </div>

        <div id="errorMessage" class="error-message"></div>

        <div class="search-section">
            <div class="search-grid">
                <div class="form-group">
                    <label>📂 Directory Path</label>
                    <input type="text" id="directoryInput" placeholder="e.g., ~/documents" value="~">
                </div>
                <div class="form-group">
                    <label>🔍 File Name</label>
                    <input type="text" id="filenameInput" placeholder="Enter filename or partial name" value=".pdf">
                </div>
                <button class="btn-primary" id="searchBtn">
                    <span class="btn-text" id="searchBtnText">🔎 Search Files</span>
                </button>
            </div>
            
            <div class="shortcuts">
                <span class="shortcut-tip">💡 Tip: Use partial names (e.g., "report")</span>
                <span class="shortcut-tip">⌨️ Press Enter to search</span>
            </div>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text">
                    <span id="progressStatus">Searching...</span>
                    <span id="progressPercent">0%</span>
                </div>
            </div>
        </div>

        <div class="stats-bar" id="statsBar" style="display: none;">
            <div class="stat-card">
                <div class="stat-value" id="totalFiles">0</div>
                <div class="stat-label">📄 Total Files Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalSize">0 B</div>
                <div class="stat-label">📦 Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uniqueFolders">0</div>
                <div class="stat-label">📂 Unique Folders</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="searchTime">-</div>
                <div class="stat-label">⏱️ Search Time</div>
            </div>
        </div>

        <div class="results-section" id="resultsSection">
            <div class="results-header">
                <h3>📄 Search Results</h3>
                <span class="results-count" id="resultsCount">0 files found</span>
            </div>
            <div id="resultsContainer">
                <div class="no-results">
                    <div class="icon">🔍</div>
                    <h3>Ready to Search</h3>
                    <p>Enter a directory and filename above to start searching</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isSearching = false;
        let statusCheckInterval = null;
        let searchStartTime = null;

        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const searchBtn = document.getElementById('searchBtn');
        const searchBtnText = document.getElementById('searchBtnText');
        const directoryInput = document.getElementById('directoryInput');
        const filenameInput = document.getElementById('filenameInput');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressStatus = document.getElementById('progressStatus');
        const progressPercent = document.getElementById('progressPercent');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsCount = document.getElementById('resultsCount');
        const statsBar = document.getElementById('statsBar');
        const totalFiles = document.getElementById('totalFiles');
        const totalSize = document.getElementById('totalSize');
        const uniqueFolders = document.getElementById('uniqueFolders');
        const searchTime = document.getElementById('searchTime');
        const errorMessage = document.getElementById('errorMessage');

        directoryInput.value = '~';

        async function testServer() {
            try {
                await fetch('/api/test');
                statusText.textContent = 'Connected';
            } catch (error) {
                statusText.textContent = 'Server offline';
                showError('Cannot connect to server. Make sure the application is running.');
            }
        }
        testServer();

        searchBtn.addEventListener('click', startSearch);
        directoryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') startSearch(); });
        filenameInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') startSearch(); });

        async function startSearch() {
            if (isSearching) return;

            const directory = directoryInput.value.trim();
            const filename = filenameInput.value.trim();

            if (!directory || !filename) {
                showError('⚠️ Please enter both directory path and filename to search');
                return;
            }

            clearResults();
            hideError();
            statsBar.style.display = 'none';

            isSearching = true;
            searchBtn.disabled = true;
            searchBtnText.innerHTML = '<span class="loading-spinner"></span> Searching...';
            statusDot.className = 'status-dot searching';
            statusText.textContent = 'Searching...';
            progressContainer.classList.add('active');
            progressFill.style.width = '0%';
            progressStatus.textContent = 'Initializing search...';
            progressPercent.textContent = '0%';
            
            searchStartTime = Date.now();

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ directory, filename })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to start search');
                }

                if (statusCheckInterval) clearInterval(statusCheckInterval);
                statusCheckInterval = setInterval(checkStatus, 500);

            } catch (error) {
                showError('❌ ' + error.message);
                resetUI();
            }
        }

        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();

                progressFill.style.width = status.progress + '%';
                progressPercent.textContent = status.progress + '%';
                
                if (status.is_searching) {
                    progressStatus.textContent = `Scanning: ${status.current_file || '...'}`;
                    statusText.textContent = `Searching... (${status.total_found || 0} found)`;
                } else {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    await getResults();
                    resetUI();
                    const searchDuration = ((Date.now() - searchStartTime) / 1000).toFixed(1);
                    searchTime.textContent = `${searchDuration}s`;
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }

        async function getResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                displayResults(data);

            } catch (error) {
                showError('❌ Failed to load results: ' + error.message);
            }
        }

        function displayResults(data) {
            const results = data.results || [];
            
            statsBar.style.display = 'grid';
            totalFiles.textContent = data.total || 0;
            totalSize.textContent = data.total_size_formatted || '0 B';
            uniqueFolders.textContent = data.unique_folders || 0;
            resultsCount.textContent = `${data.total || 0} files found`;

            if (results.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="no-results">
                        <div class="icon">😕</div>
                        <h3>No files found</h3>
                        <p>No files matching "<strong>${filenameInput.value}</strong>" were found</p>
                    </div>
                `;
                return;
            }

            let html = '';
            results.forEach((result, index) => {
                const isLatest = index === 0;
                const badgeClass = isLatest ? 'badge-latest' : 'badge-old';
                const itemClass = isLatest ? 'result-item latest' : 'result-item';
                const version = isLatest ? '⭐ Latest' : `v${results.length - index}`;

                html += `
                    <div class="${itemClass}">
                        <div class="result-header">
                            <div class="result-title">
                                <span>📄</span>
                                <span>${result.name}</span>
                            </div>
                            <span class="result-badge ${badgeClass}">${version}</span>
                        </div>
                        <div class="result-path">📂 ${result.path}</div>
                        <div class="result-details">
                            <span>📅 Modified: ${result.modified_formatted}</span>
                            <span>📦 Size: ${result.size_formatted}</span>
                        </div>
                    </div>
                `;
            });

            resultsContainer.innerHTML = html;
        }

        function clearResults() {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <div class="icon">🔍</div>
                    <h3>Searching...</h3>
                    <p>Please wait while we scan your files</p>
                </div>
            `;
            statsBar.style.display = 'none';
        }

        function resetUI() {
            isSearching = false;
            searchBtn.disabled = false;
            searchBtnText.textContent = '🔎 Search Files';
            statusDot.className = 'status-dot';
            statusText.textContent = 'Ready';
            progressContainer.classList.remove('active');
        }

        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.add('active');
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Error';
        }

        function hideError() {
            errorMessage.classList.remove('active');
        }

        window.addEventListener('beforeunload', function() {
            if (statusCheckInterval) clearInterval(statusCheckInterval);
        });
    </script>
</body>
</html>'''

    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html.strip())
    print("✅ Created templates/index.html")

    # ============================================
    # FILE 3: requirements.txt
    # ============================================
    requirements = 'Flask==2.3.2\n'
    with open(os.path.join(app_dir, 'requirements.txt'), 'w') as f:
        f.write(requirements)
    print("✅ Created requirements.txt")

    # ============================================
    # FILE 4: README.md
    # ============================================
    readme_content = ""## File Search Pro