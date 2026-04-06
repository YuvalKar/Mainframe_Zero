import { app, BrowserWindow, ipcMain, screen } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

// --- ES Module compatibility for __dirname ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Constants for the "Folded" state size
const FOLDED_WIDTH = 120;
const FOLDED_HEIGHT = 40;

let mainWindow; // Store the window globally so IPC can access it

function createWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    mainWindow = new BrowserWindow({
        // Start folded by default
        width: FOLDED_WIDTH,      
        height: FOLDED_HEIGHT,    
        // Center the folded logo on screen
        x: (width / 2) - (FOLDED_WIDTH / 2),
        y: 20, // Sit nicely at the top
        alwaysOnTop: true,      
        frame: false,            
        transparent: true,
        resizable: false,      
        webPreferences: {
            nodeIntegration: false, // Changed to false for security with preload
            contextIsolation: true, // Changed to true
            preload: path.join(__dirname, 'preload.js') // Connect the bridge
        }
    });

    mainWindow.loadURL('http://localhost:5173');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

// --- Listen to React's expansion request ---
ipcMain.on('toggle-window-size', (event, isExpanded) => {
    if (!mainWindow) return;

    if (isExpanded) {
        // Expand: Find which screen the small logo is currently on, and fill it
        const currentBounds = mainWindow.getBounds();
        // screen.getDisplayNearestPoint is a super helpful Electron method
        const currentDisplay = screen.getDisplayNearestPoint({ x: currentBounds.x, y: currentBounds.y });
        
        mainWindow.setBounds({
            x: currentDisplay.workArea.x,
            y: currentDisplay.workArea.y,
            width: currentDisplay.workArea.width,
            height: currentDisplay.workArea.height
        });
    } else {
        // Fold: Shrink back down to the logo size
        // We calculate the center of the screen so it shrinks nicely, 
        // or you can just leave x,y alone to have it shrink where the mouse is
        const currentBounds = mainWindow.getBounds();
        const currentDisplay = screen.getDisplayNearestPoint({ x: currentBounds.x, y: currentBounds.y });

        mainWindow.setBounds({
            width: FOLDED_WIDTH,
            height: FOLDED_HEIGHT,
            // Keep it roughly where it was, but adjusted to new size
            x: currentBounds.x, 
            y: currentBounds.y
        });
    }
});