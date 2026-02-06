/**
 * Voice UI Controller - Intelligent interface navigation and highlighting
 * 
 * Features:
 * - Parse user intent (navigate, explain, action)
 * - Find elements by keywords
 * - Navigate to pages automatically
 * - Highlight elements with animation
 * - Scroll to elements smoothly
 * 
 * @version 1.0
 */

class VoiceUIController {
    constructor() {
        this.currentPage = window.location.pathname;
        this.userType = this.detectUserType();
        
        // Navigation map: keyword → page URL
        this.pageMap = {
            // Patient pages
            'suche': '/patient/search',
            'arztsuche': '/patient/search',
            'search': '/patient/search',
            'ärzte finden': '/patient/search',
            'termine': '/patient/bookings',
            'buchungen': '/patient/bookings',
            'meine termine': '/patient/bookings',
            'bookings': '/patient/bookings',
            'profil': '/patient/profile',
            'einstellungen': '/patient/profile',
            'dashboard': '/patient/dashboard',
            
            // Doctor pages
            'praxis profil': '/practice/profile',
            'praxisprofil': '/practice/profile',
            'practice profile': '/practice/profile',
            'kalender': '/doctor/calendar',
            'calendar': '/doctor/calendar',
            'verfügbarkeiten': '/doctor/calendar',
            'patienten termine': '/doctor/bookings',
            'arzt dashboard': '/doctor/dashboard',
            
            // Auth pages
            'anmelden': '/patient/login',
            'login': '/patient/login',
            'registrieren': '/patient/register',
            'register': '/patient/register',
            'arzt login': '/doctor/login',
            'doctor login': '/doctor/login'
        };
        
        // Element keywords map
        this.elementMap = {};
        
        // Build element map on page load
        this.buildElementMap();
        
        console.log('🎯 Voice UI Controller initialized for:', this.userType);
    }
    
    /**
     * Detect user type from JWT token
     */
    detectUserType() {
        const token = this.getCookie('access_token_cookie');
        if (!token) return 'guest';
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub?.type || 'guest';
        } catch {
            return 'guest';
        }
    }
    
    /**
     * Get cookie value by name
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    /**
     * Build map of all navigable elements on page
     */
    buildElementMap() {
        // Find all elements with data-voice-nav attribute
        const voiceElements = document.querySelectorAll('[data-voice-nav]');
        
        voiceElements.forEach(element => {
            const navId = element.getAttribute('data-voice-nav');
            const title = element.getAttribute('data-voice-title') || '';
            const description = element.getAttribute('data-voice-description') || '';
            
            // Extract keywords from title and description
            const keywords = this.extractKeywords(title + ' ' + description + ' ' + element.textContent);
            
            this.elementMap[navId] = {
                element: element,
                keywords: keywords,
                title: title,
                description: description,
                type: this.detectElementType(element)
            };
        });
        
        console.log('📍 Built element map:', Object.keys(this.elementMap).length, 'elements');
    }
    
    /**
     * Extract keywords from text
     */
    extractKeywords(text) {
        if (!text) return [];
        
        // Convert to lowercase and remove special characters
        const normalized = text.toLowerCase()
            .replace(/[^\wäöüß\s]/gi, ' ')
            .trim();
        
        // Split into words and filter short words
        return normalized.split(/\s+/)
            .filter(word => word.length > 2)
            .filter((word, index, self) => self.indexOf(word) === index); // unique
    }
    
    /**
     * Detect element type (button, link, input, etc.)
     */
    detectElementType(element) {
        const tagName = element.tagName.toLowerCase();
        
        if (tagName === 'button' || element.getAttribute('role') === 'button') {
            return 'button';
        } else if (tagName === 'a') {
            return 'link';
        } else if (tagName === 'input' || tagName === 'textarea') {
            return 'input';
        } else if (element.getAttribute('data-bs-toggle') === 'tab') {
            return 'tab';
        } else if (element.classList.contains('modal')) {
            return 'modal';
        }
        
        return 'element';
    }
    
    /**
     * Process voice command with intelligent parsing
     * @param {string} transcript - User's voice command
     * @returns {Object} - {intent, target, keywords, action}
     */
    parseIntent(transcript) {
        const text = transcript.toLowerCase().trim();
        const words = text.split(/\s+/);
        
        // Detect intent patterns
        const navigationPatterns = [
            /^(gehe? zu|zeige?|öffne?|navigiere zu|go to|show|open)/i,
            /^(wo ist|wo finde ich|where is|find)/i
        ];
        
        const actionPatterns = [
            /^(klick|drücke?|klicke auf|click|press|tap)/i,
            /^(fülle? aus|eingeben|type|fill|enter)/i,
            /^(buche?|reserviere?|book|reserve)/i
        ];
        
        const explainPatterns = [
            /^(wie|was|warum|erkläre|erklär|how|what|why|explain)/i,
            /^(hilfe|help|info|information)/i
        ];
        
        let intent = 'explain'; // default
        let action = null;
        
        // Check navigation intent
        for (const pattern of navigationPatterns) {
            if (pattern.test(text)) {
                intent = 'navigate';
                break;
            }
        }
        
        // Check action intent
        if (intent === 'explain') {
            for (const pattern of actionPatterns) {
                if (pattern.test(text)) {
                    intent = 'action';
                    action = this.detectActionType(text);
                    break;
                }
            }
        }
        
        // Check explain intent
        if (intent === 'explain') {
            for (const pattern of explainPatterns) {
                if (pattern.test(text)) {
                    intent = 'explain';
                    break;
                }
            }
        }
        
        // Extract target keywords (remove intent words)
        const intentWords = ['gehe', 'zeige', 'öffne', 'navigiere', 'klick', 'drücke', 'klicke', 
                            'wie', 'was', 'warum', 'wo', 'ist', 'finde', 'ich', 'auf', 'zu',
                            'go', 'show', 'open', 'click', 'press', 'how', 'what', 'where', 'find'];
        
        const keywords = words.filter(word => 
            word.length > 2 && 
            !intentWords.includes(word)
        );
        
        return {
            intent: intent,
            action: action,
            keywords: keywords,
            originalText: transcript
        };
    }
    
    /**
     * Detect action type from command
     */
    detectActionType(text) {
        if (/klick|click|drücke|press/i.test(text)) return 'click';
        if (/fülle|eingeben|type|fill|enter/i.test(text)) return 'fill';
        if (/buche|reserviere|book|reserve/i.test(text)) return 'book';
        return 'click'; // default action
    }
    
    /**
     * Execute voice command
     * @param {string} transcript - User's voice command
     * @returns {Promise<Object>} - Result with success, message, action taken
     */
    async executeCommand(transcript) {
        const parsed = this.parseIntent(transcript);
        
        console.log('🎯 Parsed intent:', parsed);
        
        try {
            switch (parsed.intent) {
                case 'navigate':
                    return await this.handleNavigation(parsed);
                
                case 'action':
                    return await this.handleAction(parsed);
                
                case 'explain':
                default:
                    return await this.handleExplain(parsed);
            }
        } catch (error) {
            console.error('❌ Command execution error:', error);
            return {
                success: false,
                message: 'Entschuldigung, ich konnte diesen Befehl nicht ausführen.',
                error: error.message
            };
        }
    }
    
    /**
     * Handle navigation commands
     */
    async handleNavigation(parsed) {
        const { keywords } = parsed;
        
        // 1. Check if keywords match a page
        const targetPage = this.findTargetPage(keywords);
        
        if (targetPage && targetPage !== this.currentPage) {
            // Navigate to page
            console.log('📄 Navigating to:', targetPage);
            
            return {
                success: true,
                message: `Navigiere zu ${targetPage}...`,
                action: 'page_navigation',
                target: targetPage,
                execute: () => {
                    window.location.href = targetPage;
                }
            };
        }
        
        // 2. Find element on current page
        const targetElement = this.findTargetElement(keywords);
        
        if (targetElement) {
            // Scroll and highlight element
            await this.highlightElement(targetElement.element);
            
            return {
                success: true,
                message: `Hier ist: ${targetElement.title || 'das Element'}`,
                action: 'element_highlight',
                target: targetElement.title
            };
        }
        
        // 3. No match found - ask chatbot
        return {
            success: false,
            message: 'Ich konnte dieses Element nicht finden. Lass mich dir helfen...',
            action: 'fallback_to_chatbot'
        };
    }
    
    /**
     * Handle action commands (click, fill, etc.)
     */
    async handleAction(parsed) {
        const { keywords, action } = parsed;
        
        // Find target element
        const targetElement = this.findTargetElement(keywords);
        
        if (!targetElement) {
            return {
                success: false,
                message: 'Ich konnte das Element nicht finden.',
                action: 'element_not_found'
            };
        }
        
        // Highlight element first
        await this.highlightElement(targetElement.element);
        
        // Perform action
        switch (action) {
            case 'click':
                // Simulate click after delay
                setTimeout(() => {
                    targetElement.element.click();
                }, 1000);
                
                return {
                    success: true,
                    message: `Klicke auf: ${targetElement.title}`,
                    action: 'element_click',
                    target: targetElement.title
                };
            
            case 'fill':
                // Focus input field
                targetElement.element.focus();
                
                return {
                    success: true,
                    message: `Bereit für Eingabe in: ${targetElement.title}`,
                    action: 'element_focus',
                    target: targetElement.title
                };
            
            default:
                return {
                    success: false,
                    message: 'Diese Aktion wird noch nicht unterstützt.',
                    action: 'unsupported_action'
                };
        }
    }
    
    /**
     * Handle explanation requests (fallback to chatbot)
     */
    async handleExplain(parsed) {
        return {
            success: true,
            message: 'Lass mich dir das erklären...',
            action: 'chatbot_explain',
            fallbackToChatbot: true
        };
    }
    
    /**
     * Find target page from keywords
     */
    findTargetPage(keywords) {
        if (!keywords || keywords.length === 0) return null;
        
        // Check exact matches first
        for (const keyword of keywords) {
            if (this.pageMap[keyword]) {
                return this.pageMap[keyword];
            }
        }
        
        // Check partial matches
        const keywordStr = keywords.join(' ');
        for (const [key, url] of Object.entries(this.pageMap)) {
            if (keywordStr.includes(key) || key.includes(keywordStr)) {
                return url;
            }
        }
        
        return null;
    }
    
    /**
     * Find target element from keywords
     */
    findTargetElement(keywords) {
        if (!keywords || keywords.length === 0) return null;
        
        let bestMatch = null;
        let bestScore = 0;
        
        for (const [navId, elementData] of Object.entries(this.elementMap)) {
            // Calculate match score
            let score = 0;
            
            for (const keyword of keywords) {
                if (elementData.keywords.includes(keyword)) {
                    score += 10;
                } else {
                    // Partial match
                    for (const elemKeyword of elementData.keywords) {
                        if (elemKeyword.includes(keyword) || keyword.includes(elemKeyword)) {
                            score += 5;
                        }
                    }
                }
            }
            
            if (score > bestScore) {
                bestScore = score;
                bestMatch = elementData;
            }
        }
        
        // Return if match is good enough
        return bestScore > 5 ? bestMatch : null;
    }
    
    /**
     * Highlight element with animation and scroll
     */
    async highlightElement(element) {
        if (!element) return;
        
        // Scroll to element
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        
        // Wait for scroll
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Add highlight animation
        const originalBoxShadow = element.style.boxShadow;
        const originalTransition = element.style.transition;
        const originalZIndex = element.style.zIndex;
        
        element.style.transition = 'all 0.3s ease';
        element.style.boxShadow = '0 0 0 4px rgba(76, 217, 100, 0.8), 0 0 30px rgba(76, 217, 100, 0.5)';
        element.style.zIndex = '10000';
        
        // Pulse animation
        for (let i = 0; i < 3; i++) {
            await new Promise(resolve => setTimeout(resolve, 300));
            element.style.boxShadow = '0 0 0 8px rgba(76, 217, 100, 0.4), 0 0 40px rgba(76, 217, 100, 0.3)';
            
            await new Promise(resolve => setTimeout(resolve, 300));
            element.style.boxShadow = '0 0 0 4px rgba(76, 217, 100, 0.8), 0 0 30px rgba(76, 217, 100, 0.5)';
        }
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
            element.style.boxShadow = originalBoxShadow;
            element.style.transition = originalTransition;
            element.style.zIndex = originalZIndex;
        }, 3000);
    }
    
    /**
     * Add voice navigation attributes to elements automatically
     */
    autoAnnotateElements() {
        // Annotate buttons
        document.querySelectorAll('button').forEach((btn, index) => {
            if (!btn.hasAttribute('data-voice-nav')) {
                const text = btn.textContent.trim();
                if (text) {
                    btn.setAttribute('data-voice-nav', `auto-btn-${index}`);
                    btn.setAttribute('data-voice-title', text);
                }
            }
        });
        
        // Annotate links
        document.querySelectorAll('a').forEach((link, index) => {
            if (!link.hasAttribute('data-voice-nav')) {
                const text = link.textContent.trim();
                if (text) {
                    link.setAttribute('data-voice-nav', `auto-link-${index}`);
                    link.setAttribute('data-voice-title', text);
                }
            }
        });
        
        // Rebuild element map
        this.buildElementMap();
        
        console.log('🤖 Auto-annotated elements on page');
    }
}

// Initialize on page load
let voiceUIController = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        voiceUIController = new VoiceUIController();
        voiceUIController.autoAnnotateElements();
        
        // Make available globally
        window.voiceUIController = voiceUIController;
    });
} else {
    voiceUIController = new VoiceUIController();
    voiceUIController.autoAnnotateElements();
    window.voiceUIController = voiceUIController;
}
