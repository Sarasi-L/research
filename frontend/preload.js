// frontend/preload.js

const { contextBridge } = require("electron");

// Expose protected methods that allow the renderer process to use
// certain Node.js features in a controlled manner
contextBridge.exposeInMainWorld("api", {
    // Navigation function
    navigate: (page) => {
        window.location.href = page;
    },
    
    // Get current page name
    getCurrentPage: () => {
        return window.location.pathname.split("/").pop() || "landing.html";
    },
    
    // Go back in history
    goBack: () => {
        window.history.back();
    },
    
    // Go forward in history
    goForward: () => {
        window.history.forward();
    },
    
    // Check if can go back
    canGoBack: () => {
        return window.history.length > 1;
    }
});

// Optional: Log when preload script is loaded
console.log("Preload script loaded successfully");