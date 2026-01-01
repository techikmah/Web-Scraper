# Advanced Web Scraper Pro

A professional-grade web scraping tool with a modern Electron desktop application, Python backend, and React frontend. Features comprehensive scraping capabilities with advanced options for handling dynamic content, rate limiting, proxy rotation, and more.

## 🚀 Features

### Core Scraping Features
- **Multiple Selector Types**: CSS selectors and XPath support
- **Attribute Extraction**: Extract specific attributes (href, src, data-*) from elements
- **Image Scraping**: Download images with configurable selectors
- **JavaScript Rendering**: Support for Playwright and Selenium for dynamic content
- **Pagination**: Automatic multi-page scraping with configurable patterns
- **Incremental Scraping**: Skip duplicate data automatically

### Advanced Features
- **Rate Limiting**: Configurable requests per second to avoid overwhelming servers
- **Retry Logic**: Automatic retries with exponential backoff
- **Proxy Rotation**: Health-checked proxy management with automatic rotation
- **User-Agent Rotation**: Random User-Agent strings to avoid detection
- **Data Validation**: Automatic data cleaning and validation
- **Cookie/Session Management**: Persistent sessions for authenticated scraping

### Output Formats
- **JSON**: Structured data export
- **CSV**: Spreadsheet-compatible format
- **Excel**: Microsoft Excel format (.xlsx)
- **XML**: XML format for structured data
- **SQLite**: Database format for large datasets

### User Interface
- **Real-time Progress**: Live progress tracking during scraping
- **Selector Testing**: Test selectors before running full scrape
- **URL Validation**: Validate URLs before scraping
- **Scraping History**: Track all scraping jobs with statistics
- **Data Preview**: Preview scraped data before export
- **Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS

## 📋 Requirements

### Backend (Python)
- Python 3.8+
- See `backend/requirements.txt` for full list

### Frontend (Node.js)
- Node.js 16+
- npm or yarn

### Optional (for JavaScript rendering)
- Playwright: `pip install playwright && playwright install chromium`
- Selenium: `pip install selenium` (requires ChromeDriver)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd web-scraper
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 4. Install Root Dependencies (for Electron)
```bash
cd ..
npm install
```

## 🚀 Usage

### Development Mode

#### Option 1: Run Everything Together
```bash
npm run dev
```
This will start:
- Vite dev server (frontend) on http://localhost:5173
- Flask API (backend) on http://localhost:5000
- Electron app

#### Option 2: Run Separately

**Backend:**
```bash
cd backend
python app.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Electron:**
```bash
npm run dev:electron
```

### Production Build

#### Build Frontend
```bash
cd frontend
npm run build
```

#### Build Backend (Windows executable)
```bash
cd backend
python build_backend.py
```

#### Build Electron App
```bash
npm run build
```

For platform-specific builds:
```bash
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

## 📖 Usage Guide

### Basic Scraping

1. **Enter Target URL**: Enter the website URL you want to scrape
2. **Add Selectors**: 
   - Click "+ Add" to add a new selector
   - Enter a field name (e.g., "title", "price")
   - Choose selector type (CSS or XPath)
   - Enter the selector (e.g., `.product-title` or `//h1[@class="title"]`)
   - Optionally specify an attribute to extract (e.g., `href`, `src`)
3. **Test Selector**: Click the test tube icon to preview results
4. **Configure Options**: 
   - Enable image scraping if needed
   - Choose output format
   - Configure proxy/authentication if required
5. **Start Scraping**: Click "Start Scraping" button

### Advanced Features

#### JavaScript Rendering
Enable JavaScript rendering for websites that load content dynamically:
1. Click "Advanced" button
2. Enable "JavaScript Rendering"
3. Choose engine (Playwright recommended)

#### Pagination
Scrape multiple pages automatically:
1. Enable "Pagination" in Advanced settings
2. Choose pagination type (Query Parameter or Path-based)
3. Set start and end page numbers

#### Rate Limiting
Control request rate to avoid being blocked:
1. Set "Max Requests Per Second" in Advanced settings
2. Recommended: 1-2 requests/second for most sites

#### Proxy Rotation
Use proxies for anonymity:
1. Enable "Use proxy rotation"
2. Upload proxy list file or paste proxies (one per line)
3. Format: `http://proxy:port` or `https://proxy:port`

#### Authentication
Scrape protected pages:
1. Enable "Requires authentication"
2. Upload credentials file or paste (format: `username,password`)
3. Configure login URL if different from default

## 🔧 Configuration

### Backend Configuration

The scraper accepts a configuration dictionary:

```python
config = {
    'url': 'https://example.com',
    'selectors': [
        {
            'name': 'title',
            'selector': 'h1',
            'type': 'css',
            'attribute': None  # Optional: 'href', 'src', etc.
        }
    ],
    'scrapeImages': True,
    'imageSelector': 'img',
    'outputFormat': 'json',  # 'json', 'csv', 'excel', 'xml', 'sqlite'
    'useJavaScriptRendering': False,
    'jsEngine': 'playwright',  # 'playwright' or 'selenium'
    'maxRequestsPerSecond': 2.0,
    'maxRetries': 3,
    'pagination': {
        'type': 'query',  # 'query' or 'path'
        'startPage': 1,
        'endPage': 5,
        'paramName': 'page'
    },
    'incrementalScraping': False,
    'proxies': [],
    'credentials': []
}
```

## 📊 API Endpoints

### Health Check
```
GET /api/health
```

### Scrape
```
POST /api/scrape
Body: { config object }
```

### Quick Scrape
```
POST /api/scrape-quick
Body: { url, selectors, ... }
```

### Test Selector
```
POST /api/test-selector
Body: { url, selector, type, attribute }
```

### Validate URL
```
POST /api/validate-url
Body: { url }
```

### Download Results
```
POST /api/download
Body: { results, format }
```

### Scraping History
```
GET /api/history?limit=50&offset=0
GET /api/history/<id>
```

## 🎯 Best Practices

1. **Respect robots.txt**: Always check and respect website robots.txt
2. **Rate Limiting**: Use appropriate rate limits (1-2 req/sec recommended)
3. **User-Agent**: The scraper automatically rotates User-Agents
4. **Error Handling**: The scraper includes automatic retry logic
5. **Data Validation**: Enable data validation for cleaner results
6. **Incremental Scraping**: Use for recurring scrapes to avoid duplicates

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 5000 is available

### Frontend won't connect
- Ensure backend is running on http://localhost:5000
- Check CORS settings if using different ports
- Verify API URL in frontend settings

### JavaScript rendering not working
- Install Playwright: `pip install playwright && playwright install chromium`
- Or install Selenium: `pip install selenium`
- Ensure ChromeDriver is in PATH (for Selenium)

### Selectors not working
- Use browser DevTools to test selectors
- Try the "Test Selector" feature in the UI
- Check if JavaScript rendering is needed
- Verify selector syntax (CSS vs XPath)

## 📝 License

This project is open source and available for use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ using Python, Flask, React, Electron, and Tailwind CSS**







