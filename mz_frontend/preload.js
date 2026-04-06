// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  toggleWindowSize: (isExpanded) => ipcRenderer.send('toggle-window-size', isExpanded)
});