// frontend/main.js

const { app, BrowserWindow } = require("electron");
const path = require("path");

function createWindow() {
    const win = new BrowserWindow({
        width: 1600,
        height: 1000,
        minWidth: 1024,
        minHeight: 768,
        backgroundColor: '#000000',
        show: false,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'assets/icon.png'), // Optional: Add your app icon
        title: "Music Notation Generator"
    });

    // Load landing page first
    win.loadFile("landing.html");

    // Show window when ready
    win.once("ready-to-show", () => {
        win.show();
    });

    // Handle window close event
    win.on("closed", () => {
        console.log("Window closed");
    });

    // Optional: Open DevTools in development mode
    // Uncomment the line below for debugging
    // win.webContents.openDevTools();

    // Handle navigation errors
    win.webContents.on("did-fail-load", (event, errorCode, errorDescription) => {
        console.error("Failed to load:", errorDescription);
    });

    return win;
}

// App ready event
app.whenReady().then(() => {
    createWindow();

    // macOS specific: Re-create window when dock icon is clicked
    app.on("activate", () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Quit when all windows are closed (except on macOS)
app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});

// Handle app activation (macOS)
app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Optional: Handle before quit
app.on("before-quit", (event) => {
    console.log("App is quitting...");
});

// Optional: Log app version
app.on("ready", () => {
    console.log("App Version:", app.getVersion());
    console.log("Electron Version:", process.versions.electron);
});