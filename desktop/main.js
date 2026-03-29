const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

// Determine if we are running in development or production mode
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
let mainWindow;
let backendProcess;

function getBackendConfig() {
  if (isDev) {
    // Dev mode: Spawn python directly from virtual environment in the project root
    const pythonExecutable = process.platform === 'win32'
      ? path.join(__dirname, '..', '.venv', 'Scripts', 'python.exe')
      : path.join(__dirname, '..', '.venv', 'bin', 'python');
    
    const scriptPath = path.join(__dirname, '..', 'tobu_launcher.py');
    return { 
      command: pythonExecutable, 
      args: [scriptPath],
      cwd: path.join(__dirname, '..')
    };
  } else {
    // Prod mode: Spawn the PyInstaller bundled executable
    const binaryName = process.platform === 'win32' ? 'fastapi-server.exe' : 'fastapi-server';
    // Use process.resourcesPath/dist/fastapi-server/...
    const binaryPath = path.join(process.resourcesPath, 'dist', 'fastapi-server', binaryName);
    return { 
      command: binaryPath, 
      args: [],
      cwd: process.resourcesPath
    };
  }
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const { command, args, cwd } = getBackendConfig();
    console.log('=== BACKEND CONFIG ===');
    console.log('Command:', command);
    console.log('Args:', args);
    console.log('CWD:', cwd);
    console.log('__dirname:', __dirname);
    console.log('======================');
    console.log(`Starting backend: ${command} ${args.join(' ')}`);
    
    // Spawn the backend process
    backendProcess = spawn(command, args, { cwd, stdio: 'inherit' });

    backendProcess.on('error', (err) => {
      console.error('Failed to start backend process:', err);
      reject(err);
    });

    // Health check polling settings
    let isReady = false;
    let attempts = 0;
    const maxAttempts = 120; // 120 attempts * 500ms = 60 seconds

    const checkHealth = () => {
      attempts++;
      const req = http.get('http://127.0.0.1:8000/api/v1/health', (res) => {
        if (res.statusCode === 200) {
          isReady = true;
          resolve();
        } else {
          retryOrFail();
        }
      });

      req.on('error', () => {
        retryOrFail();
      });

      req.end();
    };

    const retryOrFail = () => {
      if (!isReady) {
        if (attempts >= maxAttempts) {
          reject(new Error('Backend health check timed out after 60 seconds.'));
        } else {
          setTimeout(checkHealth, 500);
        }
      }
    };

    // Start initial health check
    setTimeout(checkHealth, 500);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  if (isDev) {
    // Development: Load Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: Load the built React app
    mainWindow.loadFile(path.join(__dirname, '..', 'client', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  try {
    await startBackend();
    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    dialog.showErrorBox('Backend Error', `Failed to start the backend server:\n\n${error.message}`);
    if (backendProcess && !backendProcess.killed) {
      backendProcess.kill();
    }
    app.quit();
  }
});

// Cleanly terminate backend process when the app quits
app.on('will-quit', () => {
  if (backendProcess && !backendProcess.killed) {
    console.log('Terminating backend process...');
    if (process.platform === 'win32') {
      // Use taskkill to kill process tree on Windows to prevent orphaned uvicorn workers
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
