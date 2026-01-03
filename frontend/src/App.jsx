import React, { useState, useEffect } from 'react';
import { Download, Upload, Play, Settings, Image, Lock, Globe, CheckCircle, XCircle, History, TestTube, Zap, Clock } from 'lucide-react';

export default function WebScraper() {
  const [url, setUrl] = useState('');
  const [selectors, setSelectors] = useState([{ id: 1, name: 'title', selector: '', type: 'css', attribute: '' }]);
  const [scrapeImages, setScrapeImages] = useState(false);
  const [imageSelector, setImageSelector] = useState('img');
  const [outputFormat, setOutputFormat] = useState('json');
  const [proxyList, setProxyList] = useState('');
  const [loginCredentials, setLoginCredentials] = useState('');
  const [useProxy, setUseProxy] = useState(false);
  const [useLogin, setUseLogin] = useState(false);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiUrl, setApiUrl] = useState('http://localhost:5000');
  const [progress, setProgress] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Advanced settings
  const [useJsRendering, setUseJsRendering] = useState(false);
  const [jsEngine, setJsEngine] = useState('playwright');
  const [maxRequestsPerSecond, setMaxRequestsPerSecond] = useState(2.0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [paginationEnabled, setPaginationEnabled] = useState(false);
  const [paginationConfig, setPaginationConfig] = useState({ type: 'query', startPage: 1, endPage: 5, paramName: 'page' });
  const [incrementalScraping, setIncrementalScraping] = useState(false);
  
  // Item-based scraping (for identical items like products, articles)
  const [itemScrapingMode, setItemScrapingMode] = useState(false);
  const [containerSelector, setContainerSelector] = useState('');
  const [containerType, setContainerType] = useState('css');
  const [itemFieldSelectors, setItemFieldSelectors] = useState([{ id: 1, name: 'title', selector: '', type: 'css', attribute: '', required: false }]);

  useEffect(() => {
    if (jobId) {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${apiUrl}/api/job-status/${jobId}`);
          const data = await response.json();
          if (data.success) {
            setProgress(data.progress);
            if (data.status === 'completed') {
              setResults({
                url: data.results?.[0]?.url || url,
                timestamp: new Date().toISOString(),
                data: data.results || [],
                stats: data.stats,
                images: [],
                images_count: data.stats?.images_downloaded || 0
              });
              setIsLoading(false);
              setJobId(null);
              loadHistory();
            } else if (data.status === 'failed') {
              setError(data.error || 'Scraping failed');
              setIsLoading(false);
              setJobId(null);
            }
          }
        } catch (err) {
          console.error('Error checking job status:', err);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, apiUrl, url]);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/history?limit=10`);
      const data = await response.json();
      if (data.success) {
        setHistory(data.history);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addSelector = () => {
    setSelectors([...selectors, { 
      id: Date.now(), 
      name: '', 
      selector: '', 
      type: 'css',
      attribute: ''
    }]);
  };

  const updateSelector = (id, field, value) => {
    setSelectors(selectors.map(s => 
      s.id === id ? { ...s, [field]: value } : s
    ));
  };

  const removeSelector = (id) => {
    setSelectors(selectors.filter(s => s.id !== id));
  };

  // Item field selector functions
  const addItemFieldSelector = () => {
    setItemFieldSelectors([...itemFieldSelectors, { 
      id: Date.now(), 
      name: '', 
      selector: '', 
      type: 'css',
      attribute: '',
      required: false
    }]);
  };

  const updateItemFieldSelector = (id, field, value) => {
    setItemFieldSelectors(itemFieldSelectors.map(s => 
      s.id === id ? { ...s, [field]: value } : s
    ));
  };

  const removeItemFieldSelector = (id) => {
    setItemFieldSelectors(itemFieldSelectors.filter(s => s.id !== id));
  };

  const testSelector = async (selector) => {
    if (!url || !selector.selector) {
      alert('Please enter URL and selector first');
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`${apiUrl}/api/test-selector`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          selector: selector.selector,
          type: selector.type,
          attribute: selector.attribute
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(`Found ${data.count} matches\n\nPreview:\n${data.preview.slice(0, 5).join('\n')}`);
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (err) {
      alert(`Error testing selector: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const validateUrl = async () => {
    if (!url) return;

    try {
      const response = await fetch(`${apiUrl}/api/validate-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await response.json();
      if (data.success && data.accessible) {
        alert(`✅ URL is accessible!\nStatus: ${data.status_code}\nContent-Type: ${data.content_type}`);
      } else {
        alert(`❌ URL is not accessible: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Error validating URL: ${err.message}`);
    }
  };

  const handleFileUpload = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (type === 'proxy') {
          setProxyList(event.target.result);
        } else if (type === 'login') {
          setLoginCredentials(event.target.result);
        }
      };
      reader.readAsText(file);
    }
  };

  const startScraping = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(null);
    setResults(null);
    
    if (!url) {
      setError('Please enter a URL');
      setIsLoading(false);
      return;
    }

    // Validate based on scraping mode
    if (itemScrapingMode) {
      if (!containerSelector) {
        setError('Please enter a container selector for item-based scraping');
        setIsLoading(false);
        return;
      }
      const validItemFields = itemFieldSelectors.filter(s => s.selector && s.name);
      if (validItemFields.length === 0) {
        setError('Please add at least one field selector for items');
        setIsLoading(false);
        return;
      }
    } else {
      const validSelectors = selectors.filter(s => s.selector && s.name);
      if (validSelectors.length === 0) {
        setError('Please add at least one valid selector');
        setIsLoading(false);
        return;
      }
    }

    const config = {
      url,
      selectors: itemScrapingMode ? [] : selectors.filter(s => s.selector && s.name),
      scrapeImages,
      imageSelector,
      outputFormat,
      proxies: useProxy ? proxyList.split('\n').filter(p => p.trim()) : [],
      credentials: useLogin ? loginCredentials.split('\n').filter(c => c.trim()) : [],
      useJavaScriptRendering: useJsRendering,
      jsEngine: jsEngine,
      maxRequestsPerSecond: maxRequestsPerSecond,
      maxRetries: maxRetries,
      pagination: paginationEnabled ? paginationConfig : null,
      incrementalScraping: incrementalScraping,
      itemScraping: itemScrapingMode ? {
        enabled: true,
        containerSelector: containerSelector,
        containerType: containerType,
        fieldSelectors: itemFieldSelectors.filter(s => s.selector && s.name)
      } : { enabled: false }
    };

    try {
      const response = await fetch(`${apiUrl}/api/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (data.success) {
        setResults({
          url: data.url,
          timestamp: data.timestamp,
          data: data.results,
          stats: data.stats,
          images: data.images || [],
          images_count: data.images_count || 0
        });
        setError(null);
        loadHistory();
      } else {
        setError(data.error || 'Scraping failed');
        setResults(null);
      }
    } catch (err) {
      console.error('Scraping error:', err);
      setError(`Failed to connect to API: ${err.message}. Make sure the Flask backend is running on ${apiUrl}`);
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadResults = async () => {
    if (!results) return;
    
    try {
      const response = await fetch(`${apiUrl}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          results: results.data,
          format: outputFormat
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const extension = outputFormat === 'json' ? 'json' 
          : outputFormat === 'csv' ? 'csv' 
          : outputFormat === 'excel' ? 'xlsx' 
          : outputFormat === 'xml' ? 'xml'
          : outputFormat === 'sqlite' ? 'db'
          : 'txt';
        a.download = `scraped_data_${Date.now()}.${extension}`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Failed to download results' }));
        alert(errorData.error || 'Failed to download results');
      }
    } catch (err) {
      alert(`Error downloading: ${err.message}`);
    }
  };

  const testConnection = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/health`);
      const data = await response.json();
      if (data.status === 'online') {
        alert(`✅ Backend API is connected!\nVersion: ${data.version || 'Unknown'}`);
      }
    } catch (err) {
      alert(`❌ Cannot connect to backend API at ${apiUrl}\n\nMake sure to run: python app.py`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Advanced Web Scraper Pro
          </h1>
          <p className="text-gray-400 text-lg">Professional web scraping with advanced features</p>
          <div className="flex gap-2 justify-center mt-4">
            <button
              onClick={testConnection}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition"
            >
              Test API Connection
            </button>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition flex items-center gap-2"
            >
              <History className="w-4 h-4" />
              History
            </button>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Advanced
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-900/50 border border-red-500 rounded-lg p-4 flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">×</button>
          </div>
        )}

        {progress && (
          <div className="mb-6 bg-blue-900/50 border border-blue-500 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-200">Progress: {progress.current} / {progress.total}</span>
              <span className="text-blue-300 text-sm">{progress.url}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
          </div>
        )}

        {showHistory && (
          <div className="mb-6 bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <History className="w-5 h-5 text-blue-400" />
              Scraping History
            </h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {history.length === 0 ? (
                <p className="text-gray-400">No history yet</p>
              ) : (
                history.map((item) => (
                  <div key={item.id} className="bg-gray-700 rounded p-3 text-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold">{item.url}</p>
                        <p className="text-gray-400 text-xs">
                          {new Date(item.created_at).toLocaleString()} • 
                          {item.results_count} results • 
                          {item.status}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        item.status === 'success' ? 'bg-green-600' : 'bg-red-600'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Configuration */}
          <div className="space-y-6">
            {/* URL Input */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-400" />
                Target URL
              </h2>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={validateUrl}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg"
                  title="Validate URL"
                >
                  <CheckCircle className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Scraping Mode Toggle */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-400" />
                Scraping Mode
              </h2>
              <div className="flex gap-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="scrapingMode"
                    checked={!itemScrapingMode}
                    onChange={() => setItemScrapingMode(false)}
                    className="w-5 h-5"
                  />
                  <span>Regular (Page-wide)</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="scrapingMode"
                    checked={itemScrapingMode}
                    onChange={() => setItemScrapingMode(true)}
                    className="w-5 h-5"
                  />
                  <span>Item-based (Identical Items)</span>
                </label>
              </div>
              {itemScrapingMode && (
                <div className="mt-4 p-3 bg-blue-900/30 rounded-lg text-sm text-blue-200">
                  <strong>Item-based mode:</strong> Scrape identical items (products, articles, etc.) from a single page. 
                  First select the container that wraps each item, then define fields to extract from each item.
                </div>
              )}
            </div>

            {/* Item-based Scraping Configuration */}
            {itemScrapingMode ? (
              <>
                {/* Container Selector */}
                <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
                  <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-blue-400" />
                    Item Container
                  </h2>
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <select
                        value={containerType}
                        onChange={(e) => setContainerType(e.target.value)}
                        className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                      >
                        <option value="css">CSS</option>
                        <option value="xpath">XPath</option>
                      </select>
                      <input
                        type="text"
                        placeholder={containerType === 'css' ? 'e.g., .product-item, .article-card' : 'e.g., //div[@class="product"]'}
                        value={containerSelector}
                        onChange={(e) => setContainerSelector(e.target.value)}
                        className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <p className="text-xs text-gray-400">
                      Selector for the container that wraps each item (e.g., each product card, article box)
                    </p>
                  </div>
                </div>

                {/* Item Field Selectors */}
                <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                      <Settings className="w-5 h-5 text-blue-400" />
                      Item Fields
                    </h2>
                    <button
                      onClick={addItemFieldSelector}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
                    >
                      + Add Field
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">
                    Define fields to extract from each item (selectors are relative to the container)
                  </p>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {itemFieldSelectors.map((selector) => (
                      <div key={selector.id} className="bg-gray-700 rounded-lg p-3 space-y-2">
                        <div className="flex gap-2">
                          <input
                            type="text"
                            placeholder="Field name (e.g., title, price)"
                            value={selector.name}
                            onChange={(e) => updateItemFieldSelector(selector.id, 'name', e.target.value)}
                            className="flex-1 px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                          />
                          <select
                            value={selector.type}
                            onChange={(e) => updateItemFieldSelector(selector.id, 'type', e.target.value)}
                            className="px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none"
                          >
                            <option value="css">CSS</option>
                            <option value="xpath">XPath</option>
                          </select>
                          <label className="flex items-center gap-1 px-2 py-1 bg-gray-600 rounded text-xs cursor-pointer">
                            <input
                              type="checkbox"
                              checked={selector.required}
                              onChange={(e) => updateItemFieldSelector(selector.id, 'required', e.target.checked)}
                              className="w-3 h-3"
                            />
                            Required
                          </label>
                        </div>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            placeholder={selector.type === 'css' ? 'e.g., .title, h2' : 'e.g., .//h2/text()'}
                            value={selector.selector}
                            onChange={(e) => updateItemFieldSelector(selector.id, 'selector', e.target.value)}
                            className="flex-1 px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                          />
                          {itemFieldSelectors.length > 1 && (
                            <button
                              onClick={() => removeItemFieldSelector(selector.id)}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                            >
                              ×
                            </button>
                          )}
                        </div>
                        {selector.type === 'css' && (
                          <input
                            type="text"
                            placeholder="Attribute (optional, e.g., href, src, data-id)"
                            value={selector.attribute}
                            onChange={(e) => updateItemFieldSelector(selector.id, 'attribute', e.target.value)}
                            className="w-full px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <>
                {/* Regular Selectors */}
                <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Settings className="w-5 h-5 text-blue-400" />
                    Data Selectors
                  </h2>
                  <button
                    onClick={addSelector}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
                  >
                    + Add
                  </button>
                </div>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {selectors.map((selector) => (
                  <div key={selector.id} className="bg-gray-700 rounded-lg p-3 space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Field name"
                        value={selector.name}
                        onChange={(e) => updateSelector(selector.id, 'name', e.target.value)}
                        className="flex-1 px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                      />
                      <select
                        value={selector.type}
                        onChange={(e) => updateSelector(selector.id, 'type', e.target.value)}
                        className="px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none"
                      >
                        <option value="css">CSS</option>
                        <option value="xpath">XPath</option>
                      </select>
                      <button
                        onClick={() => testSelector(selector)}
                        className="px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-sm"
                        title="Test selector"
                      >
                        <TestTube className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder={selector.type === 'css' ? 'e.g., .class-name' : 'e.g., //div[@class="name"]'}
                        value={selector.selector}
                        onChange={(e) => updateSelector(selector.id, 'selector', e.target.value)}
                        className="flex-1 px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                      />
                      {selectors.length > 1 && (
                        <button
                          onClick={() => removeSelector(selector.id)}
                          className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                        >
                          ×
                        </button>
                      )}
                    </div>
                    {selector.type === 'css' && (
                      <input
                        type="text"
                        placeholder="Attribute (optional, e.g., href, src)"
                        value={selector.attribute}
                        onChange={(e) => updateSelector(selector.id, 'attribute', e.target.value)}
                        className="w-full px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm focus:outline-none focus:border-blue-500"
                      />
                    )}
                  </div>
                ))}
              </div>
                </div>
              </>
            )}

            {/* Image Scraping */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Image className="w-5 h-5 text-blue-400" />
                Image Scraping
              </h2>
              <label className="flex items-center gap-3 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={scrapeImages}
                  onChange={(e) => setScrapeImages(e.target.checked)}
                  className="w-5 h-5"
                />
                <span>Enable image scraping</span>
              </label>
              {scrapeImages && (
                <input
                  type="text"
                  placeholder="Image selector (e.g., img, .image-class)"
                  value={imageSelector}
                  onChange={(e) => setImageSelector(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
              )}
            </div>

            {/* Output Format */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4">Output Format</h2>
              <div className="grid grid-cols-3 gap-2">
                {['json', 'csv', 'excel', 'xml', 'sqlite'].map(format => (
                  <button
                    key={format}
                    onClick={() => setOutputFormat(format)}
                    className={`py-2 rounded-lg transition text-sm ${
                      outputFormat === format
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    {format.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Advanced Settings & Results */}
          <div className="space-y-6">
            {/* Advanced Settings */}
            {showAdvanced && (
              <div className="bg-gray-800 rounded-lg p-6 shadow-xl space-y-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-400" />
                  Advanced Settings
                </h2>
                
                <div>
                  <label className="flex items-center gap-3 mb-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useJsRendering}
                      onChange={(e) => setUseJsRendering(e.target.checked)}
                      className="w-5 h-5"
                    />
                    <span>JavaScript Rendering (for dynamic content)</span>
                  </label>
                  {useJsRendering && (
                    <select
                      value={jsEngine}
                      onChange={(e) => setJsEngine(e.target.value)}
                      className="w-full mt-2 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                    >
                      <option value="playwright">Playwright (Recommended)</option>
                      <option value="selenium">Selenium</option>
                    </select>
                  )}
                </div>

                <div>
                  <label className="block mb-2">Max Requests Per Second</label>
                  <input
                    type="number"
                    min="0.1"
                    max="10"
                    step="0.1"
                    value={maxRequestsPerSecond}
                    onChange={(e) => setMaxRequestsPerSecond(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block mb-2">Max Retries</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                  />
                </div>

                <div>
                  <label className="flex items-center gap-3 mb-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={paginationEnabled}
                      onChange={(e) => setPaginationEnabled(e.target.checked)}
                      className="w-5 h-5"
                    />
                    <span>Enable Pagination</span>
                  </label>
                  {paginationEnabled && (
                    <div className="mt-2 space-y-2">
                      <select
                        value={paginationConfig.type}
                        onChange={(e) => setPaginationConfig({...paginationConfig, type: e.target.value})}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                      >
                        <option value="query">Query Parameter</option>
                        <option value="path">Path-based</option>
                      </select>
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="number"
                          placeholder="Start Page"
                          value={paginationConfig.startPage}
                          onChange={(e) => setPaginationConfig({...paginationConfig, startPage: parseInt(e.target.value)})}
                          className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                        />
                        <input
                          type="number"
                          placeholder="End Page"
                          value={paginationConfig.endPage}
                          onChange={(e) => setPaginationConfig({...paginationConfig, endPage: parseInt(e.target.value)})}
                          className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={incrementalScraping}
                      onChange={(e) => setIncrementalScraping(e.target.checked)}
                      className="w-5 h-5"
                    />
                    <span>Incremental Scraping (skip duplicates)</span>
                  </label>
                </div>
              </div>
            )}

            {/* Proxy Configuration */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-400" />
                Proxy Settings
              </h2>
              <label className="flex items-center gap-3 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useProxy}
                  onChange={(e) => setUseProxy(e.target.checked)}
                  className="w-5 h-5"
                />
                <span>Use proxy rotation</span>
              </label>
              {useProxy && (
                <>
                  <div className="mb-3">
                    <label className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg cursor-pointer">
                      <Upload className="w-4 h-4" />
                      <span>Upload Proxy List</span>
                      <input
                        type="file"
                        accept=".csv,.txt"
                        onChange={(e) => handleFileUpload(e, 'proxy')}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <textarea
                    placeholder="Paste proxies here (one per line)&#10;http://proxy1:8080&#10;http://proxy2:8080"
                    value={proxyList}
                    onChange={(e) => setProxyList(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 h-24 text-sm"
                  />
                </>
              )}
            </div>

            {/* Login Credentials */}
            <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Lock className="w-5 h-5 text-blue-400" />
                Login Credentials
              </h2>
              <label className="flex items-center gap-3 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useLogin}
                  onChange={(e) => setUseLogin(e.target.checked)}
                  className="w-5 h-5"
                />
                <span>Requires authentication</span>
              </label>
              {useLogin && (
                <>
                  <div className="mb-3">
                    <label className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg cursor-pointer">
                      <Upload className="w-4 h-4" />
                      <span>Upload Credentials</span>
                      <input
                        type="file"
                        accept=".csv,.txt"
                        onChange={(e) => handleFileUpload(e, 'login')}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <textarea
                    placeholder="Format: username,password (one per line)"
                    value={loginCredentials}
                    onChange={(e) => setLoginCredentials(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 h-24 text-sm"
                  />
                </>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={startScraping}
                disabled={!url || isLoading}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isLoading ? (
                  <>
                    <Clock className="w-5 h-5 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Start Scraping
                  </>
                )}
              </button>
            </div>

            {/* Results */}
            {results && (
              <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    Results
                  </h2>
                  <button
                    onClick={downloadResults}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
                
                {results.stats && (
                  <div className="mb-4 p-3 bg-gray-700 rounded-lg text-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <div>Pages: {results.stats.successful_pages}/{results.stats.total_pages}</div>
                      <div>Items: {results.stats.total_items}</div>
                      <div>Images: {results.images_count}</div>
                      <div>Duration: {results.stats.end_time && results.stats.start_time ? 
                        `${((new Date(results.stats.end_time) - new Date(results.stats.start_time)) / 1000).toFixed(2)}s` : 'N/A'}</div>
                    </div>
                  </div>
                )}

                <div className="bg-gray-700 rounded p-4 max-h-96 overflow-auto">
                  <pre className="text-xs text-green-400 whitespace-pre-wrap">
                    {JSON.stringify(results.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-3">Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-300">
            <div>
              <strong className="text-blue-400">✓ Advanced Selectors:</strong> CSS, XPath with attribute extraction
            </div>
            <div>
              <strong className="text-blue-400">✓ JavaScript Rendering:</strong> Playwright/Selenium support
            </div>
            <div>
              <strong className="text-blue-400">✓ Rate Limiting:</strong> Configurable request throttling
            </div>
            <div>
              <strong className="text-blue-400">✓ Retry Logic:</strong> Automatic retries with exponential backoff
            </div>
            <div>
              <strong className="text-blue-400">✓ Pagination:</strong> Automatic multi-page scraping
            </div>
            <div>
              <strong className="text-blue-400">✓ Multiple Formats:</strong> JSON, CSV, Excel, XML, SQLite
            </div>
            <div>
              <strong className="text-blue-400">✓ Proxy Rotation:</strong> Health-checked proxy management
            </div>
            <div>
              <strong className="text-blue-400">✓ Data Validation:</strong> Automatic cleaning and validation
            </div>
            <div>
              <strong className="text-blue-400">✓ Scraping History:</strong> Track all scraping jobs
            </div>
            <div>
              <strong className="text-blue-400">✓ Item-based Scraping:</strong> Extract identical items (products, articles) from single page
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
