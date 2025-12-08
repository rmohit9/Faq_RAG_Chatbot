const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatHistoryContainer = document.getElementById('chatHistory');

// Get session ID from URL or generate a new one
function getSessionId() {
    if (currentSessionId) return currentSessionId;
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('session_id') || generateSessionId();
}

let socket = new WebSocket("ws://127.0.0.1:8001/ws/chat/lobby/");



let typingIndicator = null;

// New: Variables for session management
let currentSessionId = null;
let chatSessions = {}; // Stores all chat sessions: { sessionId: [{text, isUser, time}, ...] }

// Helper to generate unique session IDs
function generateSessionId() {
    return crypto.randomUUID();
}

// Save the current session's messages to localStorage
function saveCurrentSession() {
    if (currentSessionId && chatSessions[currentSessionId]) {
        localStorage.setItem('chatSessions', JSON.stringify(chatSessions));
        renderChatHistoryList(); // Update the sidebar after saving
    }
}

// Load a specific chat session by ID
function loadChatSession(sessionId) {
    saveCurrentSession(); // Save the current session before switching

    currentSessionId = sessionId;
    messagesContainer.innerHTML = ''; // Clear current messages

    // Update browser URL with selected session ID (fixes refresh consistency)
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('session_id', sessionId);
    window.history.pushState({}, '', newUrl);

    const sessionMessages = chatSessions[sessionId] || [];
    sessionMessages.forEach(message => {
        addMessage(message.text, message.isUser, false); // Don't save again when loading
    });
    scrollToBottom();
    renderChatHistoryList(); // Highlight the active session
}

// Render the list of chat sessions in the sidebar
function renderChatHistoryList() {
    chatHistoryContainer.innerHTML = ''; // Clear existing list

    // Sort sessions by last updated (most recent first)
    const sortedSessionIds = Object.keys(chatSessions).sort((a, b) => {
        const sessionA = chatSessions[a];
        const sessionB = chatSessions[b];
        const lastMessageA = sessionA.length > 0 ? sessionA[sessionA.length - 1].time : '';
        const lastMessageB = sessionB.length > 0 ? sessionB[sessionB.length - 1].time : '';
        return lastMessageB.localeCompare(lastMessageA); // Simple string comparison for time
    });


    sortedSessionIds.forEach(sessionId => {
        const sessionMessages = chatSessions[sessionId];
        if (sessionMessages && sessionMessages.length > 0) {
            const firstMessage = sessionMessages[0].text;
            const sessionItem = document.createElement('div');
            sessionItem.className = `chat-history-item ${sessionId === currentSessionId ? 'active' : ''}`;
            sessionItem.innerHTML = `
                <i class="fas fa-comments chat-icon"></i>
                <div class="chat-info">
                    <h4>${firstMessage.substring(0, 25) + (firstMessage.length > 25 ? '...' : '')}</h4>
                    <p>${sessionMessages[sessionMessages.length - 1].time}</p>
                </div>
            `;
            sessionItem.onclick = () => loadChatSession(sessionId);
            chatHistoryContainer.appendChild(sessionItem);
        }
    });
}

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Get current time
function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return hours + ':' + minutes + ' ' + ampm;
}

// Add message
function addMessage(text, isUser, save = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    const time = getCurrentTime();

    const avatarHTMLUser = `<div class="msg-avatar user">U</div>`;
    const avatarHTMLBot = `<div class="msg-avatar bot">AI</div>`;

    messageDiv.innerHTML = isUser
        ? `
            <div class=\"message-bubble\">${text}</div>
            ${avatarHTMLUser}
            <div class=\"message-time\">${time}</div>
          `
        : `
            <div class=\"message-time\">${time}</div>
            ${avatarHTMLBot}
            <div class=\"message-bubble\">${text}</div>
          `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    if (save && currentSessionId) {
        if (!chatSessions[currentSessionId]) {
            chatSessions[currentSessionId] = [];
        }
        chatSessions[currentSessionId].push({ text, isUser, time });
        saveCurrentSession(); // Save to localStorage after adding message
    }
}

// Add system message
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `<div class="message-bubble">${text}</div>`;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Start new chat
function startNewChat() {
    saveCurrentSession(); // Save the current session before starting a new one

    currentSessionId = generateSessionId();
    chatSessions[currentSessionId] = []; // Initialize new session
    messagesContainer.innerHTML = ''; // Clear current messages
    renderChatHistoryList(); // Update sidebar with new active session
    messageInput.focus();
}

// Show typing indicator
function showTypingIndicator() {
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot typing';
    typingIndicator.innerHTML = `
        <div class="message-bubble">AI is typing...</div>
    `;
    messagesContainer.appendChild(typingIndicator);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.remove();
        typingIndicator = null;
    }
}

// Send message
function sendMessage() {
    const messageText = messageInput.value.trim();
    if (!messageText) return;

    const sessionId = getSessionId();
    const botSelect = document.getElementById('botSelect');
    const selectedBotId = botSelect ? botSelect.value : null; // Get selected bot ID
    
    // Add user message to the chat
    addMessage(messageText, true);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    removeTypingIndicator();
    showTypingIndicator();

    // Send message to the server with session_id and selected_bot_id
    fetch('/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: `message=${encodeURIComponent(messageText)}&session_id=${encodeURIComponent(sessionId)}&bot_id=${encodeURIComponent(selectedBotId)}`
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator();
        if (data.response) {
            addMessage(data.response, false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage("Error connecting to the bot.", false);
    });
}

// Append bot message
function appendBotMessage(text) {
    removeTypingIndicator();
    addMessage(text, false); // Bot messages are also saved
}

// Quick replies
function sendQuickReply(message) {
    messageInput.value = message;
    sendMessage();
}

// Enter key
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// WebSocket events

// Speech Recognition
const micBtn = document.getElementById('micBtn'); // Assuming your microphone button has the ID 'micBtn'
const speechConfirmationButtons = document.getElementById('speechConfirmationButtons');
const sendButton = document.getElementById('sendBtn');

if (micBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = SpeechRecognition ? new SpeechRecognition() : null;

    if (recognition) {
        recognition.continuous = false; // Listen for a single utterance
        recognition.lang = 'en-US'; // Set language
        recognition.interimResults = false; // Don't return interim results
        recognition.maxAlternatives = 1; // Get the most likely result

        micBtn.addEventListener('click', () => {
            if (micBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });

        recognition.addEventListener('start', () => {
            micBtn.classList.add('listening');
            messageInput.placeholder = "Listening...";
            sendButton.style.display = 'none'; // Hide original send button
            speechConfirmationButtons.style.display = 'none'; // Hide confirmation buttons initially
        });

        recognition.addEventListener('result', (event) => {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript; // Set transcript for user verification
            speechConfirmationButtons.style.display = 'flex'; // Show confirmation buttons
            messageInput.focus();
        });

        recognition.addEventListener('end', () => {
            micBtn.classList.remove('listening');
            messageInput.placeholder = "Type your message...";
            if (messageInput.value.trim() === '' || speechConfirmationButtons.style.display === 'none') {
                sendButton.style.display = 'block'; // Show original send button if no speech or cancelled
            }
        });

        recognition.addEventListener('error', (event) => {
            micBtn.classList.remove('listening');
            messageInput.placeholder = "Type your message...";
            sendButton.style.display = 'block'; // Show original send button on error
            speechConfirmationButtons.style.display = 'none'; // Hide confirmation buttons on error
            console.error('Speech recognition error:', event.error);
        });
    } else {
        console.warn('Speech Recognition API not supported in this browser.');
        // Optionally, disable the mic button or show a message to the user
        if (micBtn) {
            micBtn.style.display = 'none';
        }
    }
}

function sendSpeechMessage() {
    sendMessage(); // Use the existing sendMessage function
    speechConfirmationButtons.style.display = 'none'; // Hide confirmation buttons
    sendButton.style.display = 'block'; // Show original send button
}

function cancelSpeechInput() {
    messageInput.value = ''; // Clear the input
    speechConfirmationButtons.style.display = 'none'; // Hide confirmation buttons
    sendButton.style.display = 'block'; // Show original send button
    messageInput.placeholder = "Type your message...";
}

function confirmDeleteHistory() {
    if (confirm("Are you sure you want to delete all chat history? This action cannot be undone.")) {
        deleteChatHistory();
    }
}

function deleteChatHistory() {
    // Clear from localStorage
    localStorage.removeItem('chatSessions');
    chatSessions = {}; // Clear in-memory sessions
    currentSessionId = null; // Reset current session
    messagesContainer.innerHTML = ''; // Clear messages from display
    renderChatHistoryList(); // Update sidebar (should now be empty)
    startNewChat(); // Start a fresh chat session

    // Make API call to backend to delete history from database
    fetch('/delete_history/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addSystemMessage("Chat history deleted successfully.");
            localStorage.removeItem('chatSessions'); // Clear localStorage
            chatSessions = {}; // Clear in-memory sessions
            currentSessionId = null; // Reset current session
            window.location.reload(); // Reload the page
        } else {
            addSystemMessage("Error deleting chat history: " + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting chat history:', error);
        addSystemMessage("Network error while deleting chat history.");
    });
}

// WebSocket events
socket.onopen = function(event) {
    // Connection established, no need to show a message
    console.log("WebSocket connection established");
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    appendBotMessage(data.reply);
};

socket.onerror = function(event) {
    removeTypingIndicator();
    console.error("WebSocket connection error:", event);
    // Don't show error message in the chat UI
};

socket.onclose = function() {
    removeTypingIndicator();
    console.log("WebSocket connection closed");
    // Don't show closed message in the chat UI
    
    // Optional: Automatically attempt to reconnect
    setTimeout(() => {
        console.log("Attempting to reconnect...");
        socket = new WebSocket("ws://127.0.0.1:8001/ws/chat/lobby/");
    }, 5000); // Try to reconnect after 5 seconds
};

// Fetch all user-specific backend sessions (fixes missing history)
async function fetchBackendChatSessions() {
    try {
        const response = await fetch('/api/user_chat_sessions/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        });
        const data = await response.json();
        if (data.success && data.sessions.length > 0) {
            console.log('Fetched backend sessions:', data.sessions.length);
            data.sessions.forEach(sessionData => {
                if (!chatSessions[sessionData.session_id]) { // Add missing backend sessions
                    chatSessions[sessionData.session_id] = sessionData.messages;
                    console.log('Added missing backend session:', sessionData.session_id);
                }
            });
            saveCurrentSession(); // Persist merged sessions to localStorage
            renderChatHistoryList(); // Update sidebar with all sessions
        }
    } catch (error) {
        console.error('Failed to fetch backend chat sessions:', error);
    }
}

// Initialization on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check for new_chat flag in URL
    const urlParams = new URLSearchParams(window.location.search);
    const newChatFlag = urlParams.get('new_chat');

    if (newChatFlag === 'true') {
        startNewChat();
        // Remove the new_chat parameter from the URL to prevent it from triggering again on refresh
        urlParams.delete('new_chat');
        const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
        window.history.replaceState({}, '', newUrl);
        console.log('New chat initiated due to new_chat flag.');
    }

    // Load all chat sessions from localStorage with error handling
    let storedSessions = null;
    try {
        storedSessions = localStorage.getItem('chatSessions');
        if (storedSessions) {
            chatSessions = JSON.parse(storedSessions);
            console.log('Loaded sessions from localStorage:', Object.keys(chatSessions).length);
        }
    } catch (error) {
        console.error('Failed to parse localStorage sessions:', error);
        localStorage.removeItem('chatSessions'); // Clear corrupted data
        chatSessions = {};
    }

    // Merge initialChatSessions from Django (prioritize localStorage data)
    if (typeof initialChatSessions !== 'undefined' && initialChatSessions.length > 0) {
        console.log('Merging backend initial sessions:', initialChatSessions.length);
        initialChatSessions.forEach(sessionData => {
            if (!chatSessions[sessionData.session_id]) { // Only add if not in localStorage
                chatSessions[sessionData.session_id] = sessionData.messages;
                console.log('Added new backend session:', sessionData.session_id);
            } else {
                console.log('Skipping existing session (localStorage takes priority):', sessionData.session_id);
            }
        });
    }

    // Fetch backend sessions dynamically (add this line)
    fetchBackendChatSessions();

    // Determine the current session (prioritize URL > localStorage > new session)
    const urlSessionId = urlParams.get('session_id');
    const allSessionIds = Object.keys(chatSessions);
    let lastSessionId = null;

    if (allSessionIds.length > 0) {
        lastSessionId = allSessionIds.sort((a, b) => {
            const sessionA = chatSessions[a];
            const sessionB = chatSessions[b];
            const lastMessageA = sessionA.length > 0 ? sessionA[sessionA.length - 1].time : '';
            const lastMessageB = sessionB.length > 0 ? sessionB[sessionB.length - 1].time : '';
            return lastMessageB.localeCompare(lastMessageA); // Most recent first
        })[0];
    }

    // Set current session priority: URL session > most recent localStorage session > new session
    // Only start a new chat if newChatFlag is not true, otherwise it's already handled above
    if (urlSessionId && chatSessions[urlSessionId]) {
        currentSessionId = urlSessionId;
        loadChatSession(currentSessionId);
        console.log('Loaded session from URL:', urlSessionId);
    } else if (lastSessionId && chatSessions[lastSessionId].length > 0 && newChatFlag !== 'true') {
        currentSessionId = lastSessionId;
        loadChatSession(currentSessionId);
        console.log('Loaded most recent localStorage session:', lastSessionId);
    } else if (newChatFlag !== 'true') { // Only start new chat if not already handled by newChatFlag
        startNewChat();
        console.log('No existing sessions found - started new chat');
    }

    renderChatHistoryList(); // Render the sidebar history

    // Sidebar toggle for chat page (unchanged)
    const chatSidebarToggle = document.getElementById('chat-sidebar-toggle');
    const chatSidebar = document.querySelector('.sidebar');
    const chatMainContent = document.querySelector('.main-content');

    if (chatSidebarToggle && chatSidebar && chatMainContent) {
        chatSidebarToggle.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                chatSidebar.classList.toggle('active');
            } else {
                chatMainContent.classList.toggle('sidebar-collapsed');
            }
        });

        // Close sidebar when clicking outside on mobile/tablet
        document.addEventListener('click', (event) => {
            if (window.innerWidth <= 1024) {
                if (!chatSidebar.contains(event.target) && !chatSidebarToggle.contains(event.target)) {
                    chatSidebar.classList.remove('active');
                }
            }
        });
    }
});
