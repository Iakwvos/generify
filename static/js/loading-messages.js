// Loading messages with emojis
const loadingMessages = [
    "🔍 Analyzing product details...",
    "🤖 Implementing AI magic...",
    "✨ Crafting engaging content...",
    "📝 Generating product descriptions...",
    "🎨 Designing the perfect template...",
    "💫 Optimizing for your audience...",
    "🌟 Adding that special touch...",
    "🚀 Preparing for launch..."
];

class LoadingMessageRotator {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        this.currentIndex = 0;
        this.interval = null;
    }

    start() {
        if (!this.element) return;
        
        // Set initial message
        this.element.textContent = loadingMessages[0];
        
        // Start rotation
        this.interval = setInterval(() => {
            this.currentIndex = (this.currentIndex + 1) % loadingMessages.length;
            
            // Fade out
            this.element.style.opacity = '0';
            
            setTimeout(() => {
                // Update text
                this.element.textContent = loadingMessages[this.currentIndex];
                // Fade in
                this.element.style.opacity = '1';
            }, 200);
            
        }, 3000);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Export for use in other files
window.LoadingMessageRotator = LoadingMessageRotator; 