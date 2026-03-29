const { contextBridge, ipcRenderer } = require('electron');

// Define a strict whitelist of allowed IPC channels for security
const validChannels = [
  'window:minimize',
  'window:maximize',
  'window:close',
  'app:quit',
  'backend-ready',
  'backend-error'
];

contextBridge.exposeInMainWorld('electron', {
  isElectron: true,
  platform: process.platform,

  sendMessage: (channel, data) => {
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    } else {
      console.warn(`Attempted to send over unauthorized IPC channel: ${channel}`);
    }
  },

  onMessage: (channel, func) => {
    if (validChannels.includes(channel)) {
      // Strip the event object to prevent exposing internal IPC implementation details
      const subscription = (event, ...args) => func(...args);
      ipcRenderer.on(channel, subscription);
      return subscription;
    } else {
      console.warn(`Attempted to listen to unauthorized IPC channel: ${channel}`);
    }
  },

  removeListener: (channel, func) => {
    if (validChannels.includes(channel)) {
      ipcRenderer.removeListener(channel, func);
    } else {
      console.warn(`Attempted to remove listener on unauthorized IPC channel: ${channel}`);
    }
  }
});
