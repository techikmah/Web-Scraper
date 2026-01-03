const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runScraper: (config) => ipcRenderer.invoke('run-scraper', config)
});