const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 5000;

// Determine paths based on environment
function getBackendPath() {
  if (app.isPackaged) {
    // Production: Backend executable is in resources
    const exeName = process.platform === 'win32' ? 'web-scraper-backend.exe' : 'web-scraper-backend';
    return path.join(process.resourcesPath, 'backend', exeName);
  } else {
    // Development: Use Python script
    return path.join(__dirname, '../backend/app.py');
  }
}

function getFrontendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'frontend', 'dist', 'index.html');
  } else {
    return path.join(__dirname, '../frontend/dist/index.html');
  }
}

// Start Python backend server
function startBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = getBackendPath();
    
    console.log('Starting backend from:', backendPath);
    
    if (!fs.existsSync(backendPath)) {
      console.error('Backend not found at:', backendPath);
      reject(new Error('Backend executable not found'));
      return;
    }

    let command, args;
    
    if (app.isPackaged) {
      // Production: Run executable directly
      command = backendPath;
      args = [];
    } else {
      // Development: Run with Python
      command = 'python';
      args = [backendPath];
    }

    console.log('Executing:', command, args.join(' '));

    backendProcess = spawn(command, args, {
      cwd: path.dirname(backendPath),
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
      // Check if backend is ready
      if (data.toString().includes('Running on')) {
        console.log('✅ Backend is ready!');
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      const message = data.toString().trim();
      console.error(`[Backend Error] ${message}`);
      // Flask startup messages go to stderr, so check for ready state
      if (message.includes('Running on')) {
        console.log('✅ Backend is ready!');
        resolve();
      }
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendProcess = null;
    });

    // Timeout after 10 seconds
    setTimeout(() => {
      if (backendProcess) {
        console.log('Backend started (timeout reached, assuming success)');
        resolve();
      }
    }, 10000);
  });
}

// Stop backend when app closes
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// Check if backend is running
async function checkBackendHealth() {
  const fetch = require('node-fetch');
  try {
    const response = await fetch(`http://localhost:${BACKEND_PORT}/api/health`, {
      timeout: 5000
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false,
    backgroundColor: '#1a1a2e'
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  const isDev = !app.isPackaged;
  
  if (isDev) {
    // Development mode - load from Vite dev server
    console.log('Loading from Vite dev server...');
    mainWindow.loadURL('http://localhost:5173')
      .catch(err => {
        console.error('Failed to load dev server:', err);
        // Show error page
        mainWindow.loadURL(`data:text/html,
          <html>
            <body style="font-family: Arial; padding: 40px; background: #1a1a1a; color: white;">
              <h1>Development Server Not Running</h1>
              <p>Please start the Vite dev server:</p>
              <code style="background: #333; padding: 10px; display: block; margin: 10px 0;">
                cd frontend && npm run dev
              </code>
            </body>
          </html>
        `);
      });
    mainWindow.webContents.openDevTools();
  } else {
    // Production mode - load from built files
    const indexPath = getFrontendPath();
    console.log('Loading from:', indexPath);
    
    if (fs.existsSync(indexPath)) {
      mainWindow.loadFile(indexPath);
    } else {
      console.error('Frontend files not found!');
      mainWindow.loadURL(`data:text/html,
        <html>
          <body style="font-family: Arial; padding: 40px; background: #1a1a1a; color: white;">
            <h1>Build Error</h1>
            <p>Frontend files not found at:</p>
            <code style="background: #333; padding: 10px; display: block; margin: 10px 0;">
              ${indexPath}
            </code>
            <p>Please rebuild: <code style="background: #333; padding: 5px;">cd frontend && npm run build</code></p>
          </body>
        </html>
      `);
    }
  }

  // Log errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Page failed to load:', errorCode, errorDescription);
  });

  mainWindow.webContents.on('console-message', (event, level, message) => {
    console.log(`[Renderer] ${message}`);
  });
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('App is ready, starting backend...');
  
  try {
    await startBackend();
    console.log('Backend started successfully');
    
    // Wait a bit for backend to be fully ready
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    createWindow();
  } catch (error) {
    console.error('Failed to start backend:', error);
    
    // Create window anyway and show error
    createWindow();
    
    setTimeout(() => {
      if (mainWindow) {
        const { dialog } = require('electron');
        dialog.showErrorBox(
          'Backend Error',
          'Failed to start the scraper backend. The app may not work properly.\n\n' +
          'Error: ' + error.message
        );
      }
    }, 1000);
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

// IPC handlers
ipcMain.handle('check-backend', async () => {
  const isHealthy = await checkBackendHealth();
  return {
    running: isHealthy,
    url: `http://localhost:${BACKEND_PORT}`
  };
});

ipcMain.handle('get-backend-url', () => {
  return `http://localhost:${BACKEND_PORT}`;
});