"""
Enhanced Flask API Backend for Web Scraper
Features:
- Real-time scraping with progress updates
- Scraping history and audit trail
- Multiple export formats
- Better error handling
- Selector testing and validation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper import WebScraper
import json
import os
import sqlite3
from datetime import datetime
import traceback
import threading
from typing import Dict, Optional
import logging

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
HISTORY_DB = 'scraping_history.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize history database
def init_history_db():
    """Initialize scraping history database"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            config TEXT,
            results_count INTEGER,
            images_count INTEGER,
            status TEXT,
            error_message TEXT,
            duration REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_history_db()

# Store active scraping jobs
active_jobs: Dict[str, Dict] = {}

def progress_callback(job_id: str):
    """Create progress callback for a job"""
    def callback(progress: Dict):
        if job_id in active_jobs:
            active_jobs[job_id]['progress'] = progress
            active_jobs[job_id]['last_update'] = datetime.now().isoformat()
    return callback

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Web Scraper API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/scrape', methods=['POST'])
def scrape():
    """
    Main scraping endpoint with enhanced features
    """
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    try:
        config = request.json
        
        if not config or not config.get('url'):
            return jsonify({
                'success': False,
                'error': 'Missing required field: url'
            }), 400
        
        if not config.get('selectors') or len(config['selectors']) == 0:
            return jsonify({
                'success': False,
                'error': 'At least one selector is required'
            }), 400
        
        # Initialize job tracking
        active_jobs[job_id] = {
            'status': 'running',
            'progress': {'current': 0, 'total': 1},
            'start_time': datetime.now().isoformat()
        }
        
        # Create progress callback
        def progress_cb(progress):
            if job_id in active_jobs:
                active_jobs[job_id]['progress'] = progress
        
        # Create scraper instance
        scraper = WebScraper(config, progress_callback=progress_cb)
        
        # Run scraping
        start_time = datetime.now()
        scraper.run()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save to history
        save_to_history(config, scraper, duration, 'success', None)
        
        # Update job status
        active_jobs[job_id]['status'] = 'completed'
        active_jobs[job_id]['end_time'] = datetime.now().isoformat()
        
        # Prepare response
        response_data = {
            'success': True,
            'job_id': job_id,
            'url': config['url'],
            'timestamp': datetime.now().isoformat(),
            'results': scraper.results,
            'stats': scraper.stats.to_dict(),
            'images_count': len(scraper.images_downloaded),
            'images': scraper.images_downloaded[:10] if scraper.images_downloaded else [],
            'duration': duration
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error during scraping: {error_trace}")
        
        # Save to history if config was available
        try:
            config = request.json if request.json else {}
            save_to_history(config, None, 0, 'failed', str(e))
        except:
            pass
        
        # Update job status
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['error'] = str(e)
        
        return jsonify({
            'success': False,
            'job_id': job_id,
            'error': str(e),
            'trace': error_trace
        }), 500

@app.route('/api/scrape-async', methods=['POST'])
def scrape_async():
    """
    Asynchronous scraping endpoint
    Returns job ID immediately, use /api/job-status to check progress
    """
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    try:
        config = request.json
        
        if not config or not config.get('url'):
            return jsonify({
                'success': False,
                'error': 'Missing required field: url'
            }), 400
        
        # Initialize job
        active_jobs[job_id] = {
            'status': 'queued',
            'progress': {'current': 0, 'total': 1},
            'start_time': datetime.now().isoformat(),
            'config': config
        }
        
        # Start scraping in background thread
        def run_scraper():
            try:
                active_jobs[job_id]['status'] = 'running'
                
                def progress_cb(progress):
                    if job_id in active_jobs:
                        active_jobs[job_id]['progress'] = progress
                
                scraper = WebScraper(config, progress_callback=progress_cb)
                start_time = datetime.now()
                scraper.run()
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                active_jobs[job_id].update({
                    'status': 'completed',
                    'results': scraper.results,
                    'stats': scraper.stats.to_dict(),
                    'duration': duration,
                    'end_time': datetime.now().isoformat()
                })
                
                save_to_history(config, scraper, duration, 'success', None)
                
            except Exception as e:
                active_jobs[job_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'end_time': datetime.now().isoformat()
                })
                save_to_history(config, None, 0, 'failed', str(e))
        
        thread = threading.Thread(target=run_scraper)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Scraping started in background',
            'status_url': f'/api/job-status/{job_id}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/job-status/<job_id>', methods=['GET'])
def job_status(job_id):
    """Get status of a scraping job"""
    if job_id not in active_jobs:
        return jsonify({
            'success': False,
            'error': 'Job not found'
        }), 404
    
    job = active_jobs[job_id]
    return jsonify({
        'success': True,
        'job_id': job_id,
        'status': job['status'],
        'progress': job.get('progress', {}),
        'results': job.get('results'),
        'stats': job.get('stats'),
        'error': job.get('error'),
        'start_time': job.get('start_time'),
        'end_time': job.get('end_time')
    })

@app.route('/api/scrape-quick', methods=['POST'])
def scrape_quick():
    """Quick scraping endpoint - returns only essential data"""
    try:
        data = request.json
        url = data.get('url')
        selectors = data.get('selectors', [])
        
        if not url or not selectors:
            return jsonify({'error': 'URL and selectors required'}), 400
        
        config = {
            'url': url,
            'selectors': selectors,
            'scrapeImages': data.get('scrapeImages', False),
            'imageSelector': data.get('imageSelector', 'img'),
            'outputFormat': 'json',
            'maxRequestsPerSecond': 5.0,
            'maxRetries': 1
        }
        
        scraper = WebScraper(config)
        result = scraper.scrape_page(url, download_images=False)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download', methods=['POST'])
def download_results():
    """Download scraped results in specified format"""
    try:
        data = request.json
        results = data.get('results')
        output_format = data.get('format', 'json')
        
        if not results:
            return jsonify({'error': 'No results to download'}), 400
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = None
        
        if output_format == 'json':
            filename = f'scraped_data_{timestamp}.json'
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        elif output_format == 'csv':
            import pandas as pd
            filename = f'scraped_data_{timestamp}.csv'
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            flattened = []
            for item in results:
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, list):
                        flat_item[key] = '|'.join(str(v) for v in value)
                    else:
                        flat_item[key] = value
                flattened.append(flat_item)
            
            df = pd.DataFrame(flattened)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        elif output_format == 'excel':
            import pandas as pd
            filename = f'scraped_data_{timestamp}.xlsx'
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            flattened = []
            for item in results:
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, list):
                        flat_item[key] = ', '.join(str(v) for v in value)
                    else:
                        flat_item[key] = value
                flattened.append(flat_item)
            
            df = pd.DataFrame(flattened)
            df.to_excel(filepath, index=False, engine='openpyxl')
        
        elif output_format == 'xml':
            import xml.etree.ElementTree as ET
            filename = f'scraped_data_{timestamp}.xml'
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            root = ET.Element('scraped_data')
            for item in results:
                record = ET.SubElement(root, 'record')
                for key, value in item.items():
                    elem = ET.SubElement(record, key.replace(' ', '_').replace('-', '_'))
                    if isinstance(value, list):
                        elem.text = '|'.join(str(v) for v in value)
                    else:
                        elem.text = str(value) if value else ''
            
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        elif output_format == 'sqlite':
            filename = f'scraped_data_{timestamp}.db'
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            if results:
                first_item = results[0]
                columns = []
                for key in first_item.keys():
                    col_name = key.replace(' ', '_').replace('-', '_')
                    columns.append(f"{col_name} TEXT")
                
                table_name = 'scraped_data'
                cursor.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
                
                for item in results:
                    keys = list(item.keys())
                    placeholders = ','.join(['?' for _ in keys])
                    col_names = ','.join([k.replace(' ', '_').replace('-', '_') for k in keys])
                    values = []
                    for key in keys:
                        value = item[key]
                        if isinstance(value, list):
                            values.append('|'.join(str(v) for v in value))
                        else:
                            values.append(str(value) if value else '')
                    
                    cursor.execute(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
            
            conn.commit()
            conn.close()
        
        if filepath and os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to create file'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-selector', methods=['POST'])
def test_selector():
    """Test a single selector on a URL"""
    try:
        data = request.json
        url = data.get('url')
        selector = data.get('selector')
        selector_type = data.get('type', 'css')
        attribute = data.get('attribute')
        
        if not url or not selector:
            return jsonify({'error': 'URL and selector required'}), 400
        
        import requests
        from bs4 import BeautifulSoup
        from lxml import html as lxml_html
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        if selector_type == 'css':
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.select(selector)
            if attribute:
                results = [elem.get(attribute, '') for elem in elements[:10]]
            else:
                results = [elem.get_text(strip=True) for elem in elements[:10]]
        else:  # xpath
            tree = lxml_html.fromstring(response.text)
            elements = tree.xpath(selector)
            results = [elem.text_content().strip() if hasattr(elem, 'text_content') 
                      else str(elem).strip() for elem in elements[:10]]
        
        return jsonify({
            'success': True,
            'count': len(results),
            'preview': results,
            'selector': selector,
            'type': selector_type
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate-url', methods=['POST'])
def validate_url():
    """Validate if a URL is accessible"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        import requests
        response = requests.head(url, timeout=5, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return jsonify({
            'success': True,
            'accessible': response.status_code < 400,
            'status_code': response.status_code,
            'final_url': response.url,
            'content_type': response.headers.get('Content-Type', '')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'accessible': False,
            'error': str(e)
        })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get scraping history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = sqlite3.connect(HISTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM scraping_history 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        
        cursor.execute('SELECT COUNT(*) as total FROM scraping_history')
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'history': history,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history/<int:history_id>', methods=['GET'])
def get_history_item(history_id):
    """Get specific history item"""
    try:
        conn = sqlite3.connect(HISTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scraping_history WHERE id = ?', (history_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'item': dict(row)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'History item not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def save_to_history(config: Dict, scraper: Optional[WebScraper], 
                   duration: float, status: str, error_message: Optional[str]):
    """Save scraping job to history"""
    try:
        conn = sqlite3.connect(HISTORY_DB)
        cursor = conn.cursor()
        
        results_count = len(scraper.results) if scraper else 0
        images_count = len(scraper.images_downloaded) if scraper else 0
        
        cursor.execute('''
            INSERT INTO scraping_history 
            (url, config, results_count, images_count, status, error_message, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.get('url', ''),
            json.dumps(config),
            results_count,
            images_count,
            status,
            error_message,
            duration
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving to history: {e}")

if __name__ == '__main__':
    print("="*50)
    print("Enhanced Web Scraper API Server v2.0")
    print("="*50)
    print("API running at: http://localhost:5000")
    print("Health check: http://localhost:5000/api/health")
    print("="*50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
