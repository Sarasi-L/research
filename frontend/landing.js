// frontend/landing.js

document.getElementById("startBtn").addEventListener("click", () => {
    // Add a smooth transition effect before navigation
    document.body.style.opacity = "0.7";
    document.body.style.transition = "opacity 0.3s ease";
    
    // Navigate to selection page after brief delay for visual feedback
    setTimeout(() => {
        window.location.href = "index.html";
    }, 300);
});