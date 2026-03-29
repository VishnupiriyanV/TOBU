const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess;
let backendPort = 8000;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    autoHideMenuBar: true
  });

  // Load the React build
  const uiPath = path.join(__dirname, 'ui', 'index.html');
  console.log(`Loading UI from ${uiPath}`);
  mainWindow.loadFile(uiPath);

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startBackend(callback) {
  const isDev = !app.isPackaged;
  
  let executablePath;
  if (isDev) {
    executablePath = path.join(__dirname, '..', 'dist', 'tobu-vault-engine', 'tobu-vault-engine.exe');
  } else {
    // Backend is copied via extraResources to resources/engine/
    executablePath = path.join(process.resourcesPath, 'engine', 'tobu-vault-engine.exe');
  }

  console.log('Starting backend at:', executablePath);
  
  try {
    backendProcess = spawn(executablePath, [], {
      windowsHide: true,
    });
  } catch (err) {
    console.error("Failed to spawn backend:", err);
    if (mainWindow) {
      mainWindow.webContents.executeJavaScript(`console.error("Failed to spawn backend: ${err.message}")`);
    }
  }

  if (backendProcess) {
    backendProcess.stdout.on('data', (data) => console.log(`[Backend]: ${data}`));
    backendProcess.stderr.on('data', (data) => console.error(`[Backend Err]: ${data}`));
    
    backendProcess.on('error', (err) => {
      console.error("Backend process error:", err);
    });

    backendProcess.on('exit', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });
  }

  // Quick poll to see if backend is up
  let attempts = 0;
  const maxAttempts = 30; // 30 seconds
  const pollInterval = setInterval(() => {
    attempts++;
    http.get(`http://127.0.0.1:${backendPort}/api/system/health`, (res) => {
      if (res.statusCode === 200) {
        clearInterval(pollInterval);
        console.log("Backend is ready!");
        callback();
      }
    }).on('error', (err) => {
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        console.error("Backend failed to start after 30 seconds");
        callback(new Error('Backend failed to start after 30 seconds'));
      }
    });
  }, 1000);
}

app.on('ready', () => {
  createWindow();
  startBackend((err) => {
    if (err) {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(
          "console.error('TOBU backend failed to start. Check packaged resources and backend logs.');"
        );
      }
      return;
    }
    console.log('Backend ready. UI already loaded.');
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
