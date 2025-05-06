document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const referencesContainer = document.getElementById('references-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const sidebar = document.getElementById('references-sidebar');

    // Initialize console debugging
    console.log('Chat.js loaded - Financial Legal Assistant ready');

    // Function to add a message to the chat
    function addMessageToChat(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'd-flex ' + (isUser ? 'justify-content-end' : 'justify-content-start');

        const messageBubble = document.createElement('div');
        messageBubble.className = isUser ? 'user-message' : 'bot-message';
        messageBubble.textContent = message;

        messageDiv.appendChild(messageBubble);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to display references
    function displayReferences(references) {
        console.log('Displaying references:', references);
        referencesContainer.innerHTML = '';

        if (!references || references.length === 0) {
            const noRefsDiv = document.createElement('div');
            noRefsDiv.className = 'alert alert-info';
            noRefsDiv.textContent = 'No specific references found for this response.';
            referencesContainer.appendChild(noRefsDiv);
            return;
        }

        // Add a title for the references section
        const titleDiv = document.createElement('div');
        titleDiv.className = 'references-title mb-3';
        titleDiv.innerHTML = `<h5>Relevant Sources <small class="text-muted">(${references.length} found)</small></h5>`;
        referencesContainer.appendChild(titleDiv);

        references.forEach(ref => {
            const card = document.createElement('div');
            card.className = 'card reference-card mb-3';
            card.dataset.docId = ref.id;

            // Create badge for document type
            let badgeClass = 'badge-standard';
            if (ref.document_type === 'statute') badgeClass = 'badge-statute';
            if (ref.document_type === 'directive') badgeClass = 'badge-directive';
            if (ref.document_type === 'regulation') badgeClass = 'badge-regulation';
            badgeClass = 'badge-regulation'

            // Format relevance percentage
            const relevancePercent = ref.relevance || 100;
            const relevanceBarClass = relevancePercent > 75 ? 'relevance-high' :
                relevancePercent > 50 ? 'relevance-medium' :
                    relevancePercent > 25 ? 'relevance-low' : 'relevance-very-low';

            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">
                        ${ref.title}
                        <span class="badge ${badgeClass}">${ref.document_type}</span>
                    </h5>
                    <h6 class="card-subtitle mb-2 text-muted">${ref.source}</h6>
                    <div class="card-text">${ref.content_preview}</div>
                    
                    <div class="relevance-indicator">
                        <div class="relevance-bar">
                            <div class="relevance-fill ${relevanceBarClass}" style="width: ${relevancePercent}%"></div>
                        </div>
                        <div class="relevance-percentage">${relevancePercent}%</div>
                    </div>
                    
                    <button class="btn btn-sm btn-outline-info view-document mt-2" data-doc-id="${ref.id}">
                        <i class="fas fa-file-alt me-1"></i> View Full Document
                    </button>
                </div>
            `;

            referencesContainer.appendChild(card);
        });

        // Add event listeners to view document buttons
        document.querySelectorAll('.view-document').forEach(button => {
            button.addEventListener('click', function () {
                const docId = this.dataset.docId;
                loadDocument(docId);

                // Mark this reference as active
                document.querySelectorAll('.reference-card').forEach(card => {
                    card.classList.remove('active');
                });
                this.closest('.reference-card').classList.add('active');
            });
        });

        // Show the sidebar after references are loaded
        sidebar.classList.add('show');
    }

    // Function to load document
    function loadDocument(docId) {
        console.log('Loading document with ID:', docId);
        // Show loading state
        const documentDisplay = document.getElementById('document-display');
        documentDisplay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';

        fetch(`/document/${docId}`)
            .then(response => {
                console.log('Document fetch response status:', response.status);
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
                }
                return response.json().catch(err => {
                    console.error('Error parsing document JSON:', err);
                    throw new Error('Failed to parse document response as JSON');
                });
            })
            .then(data => {
                console.log('Document data received:', data);
                if (data.error) {
                    documentDisplay.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }

                // Format publication date if available
                let formattedDate = '';
                if (data.publication_date) {
                    const date = new Date(data.publication_date);
                    formattedDate = date.toLocaleDateString();
                }

                documentDisplay.innerHTML = `
                    <div class="document-header">
                        <h5>${data.title}</h5>
                        <div class="document-meta">
                            <span class="badge ${data.document_type}">${data.document_type}</span>
                            <span class="text-muted ms-2">${data.source}</span>
                            ${formattedDate ? `<span class="text-muted ms-2">Published: ${formattedDate}</span>` : ''}
                            ${data.jurisdiction ? `<span class="text-muted ms-2">Jurisdiction: ${data.jurisdiction}</span>` : ''}
                        </div>
                    </div>
                    <div class="document-content">
                        ${data.content}
                    </div>
                `;
            })
            .catch(error => {
                console.error('Error loading document:', error);
                documentDisplay.innerHTML = `<div class="alert alert-danger">Error loading document: ${error.message}</div>`;
            });
    }

    // Handle form submission
    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const message = userInput.value.trim();
        if (!message) return;

        console.log('Submitting chat form with message:', message);

        // Clear welcome message if it exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Add user message to chat
        addMessageToChat(message, true);

        // Clear input
        userInput.value = '';

        // Show loading spinner
        loadingSpinner.classList.add('active');

        // Send message to server
        console.log('Sending message to server:', message);
        const formData = new FormData();
        formData.append('message', message);

        fetch('/chat', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                console.log('Received response from server, status:', response.status);
                if (!response.ok) {
                    console.error('Response not OK:', response.status, response.statusText);
                    throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
                }
                return response.json().catch(err => {
                    console.error('Error parsing JSON response:', err);
                    throw new Error('Failed to parse server response as JSON. The server may be experiencing issues.');
                });
            })
            .then(data => {
                // Hide loading spinner
                loadingSpinner.classList.remove('active');
                console.log('Parsed response data:', data);

                if (data.error) {
                    console.error('Server returned error:', data.error);
                    addMessageToChat('Error: ' + data.error, false);
                    return;
                }

                // Add bot response to chat
                addMessageToChat(data.response, false);

                // Display references
                console.log('Displaying references:', data.references);
                displayReferences(data.references);

                // Automatically open the sidebar if there are references
                if (data.references && data.references.length > 0) {
                    sidebar.classList.add('show');
                }
            })
            .catch(error => {
                // Hide loading spinner
                loadingSpinner.classList.remove('active');

                console.error('Error processing chat request:', error);

                // More detailed error message for users
                let errorMessage = 'Sorry, an error occurred while processing your request. ';

                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    errorMessage += 'There appears to be a network connection issue. Please check your internet connection.';
                } else if (error.message.includes('JSON')) {
                    errorMessage += 'The server returned an invalid response. This might be due to API configuration issues.';
                } else if (error.message.includes('CORS')) {
                    errorMessage += 'There was a cross-origin request issue. This is likely a server configuration problem.';
                } else {
                    errorMessage += 'Please check if the server is running properly and try again. If you are running locally, ensure the GEMINI_API_KEY is set.';
                }

                addMessageToChat(errorMessage, false);
            });
    });

    // Clear chat
    clearChatBtn.addEventListener('click', function () {
        console.log('Clearing chat');
        try {
            fetch('/clear_chat', {
                method: 'POST'
            })
                .then(response => {
                    console.log('Clear chat response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`Network response was not ok: ${response.status}`);
                    }
                    return response.json().catch(err => {
                        console.error('Error parsing clear chat JSON:', err);
                        throw new Error('Failed to parse clear chat response');
                    });
                })
                .then(data => {
                    console.log('Clear chat response:', data);
                    if (data.status === 'success') {
                        // Clear chat messages
                        chatMessages.innerHTML = `
                        <div class="welcome-message">
                            <div class="logo-container">
                                <i class="fas fa-balance-scale fa-4x"></i>
                            </div>
                            <h2>Welcome to the Financial Legal Assistant</h2>
                            <p>Ask me any question about financial laws and regulations.</p>
                            <div class="example-questions">
                                <p>Try asking:</p>
                                <ul>
                                    <li>"What are the key provisions of the Dodd-Frank Act?"</li>
                                    <li>"Explain SEC Rule 10b-5 regarding securities fraud"</li>
                                    <li>"What are Basel III capital requirements for banks?"</li>
                                </ul>
                            </div>
                        </div>
                    `;

                        // Clear references and document display
                        referencesContainer.innerHTML = `
                        <div class="text-center mt-4">
                            <i class="fas fa-file-alt fa-3x text-muted mb-3"></i>
                            <p class="text-muted">References will appear here after asking a question.</p>
                        </div>
                    `;

                        document.getElementById('document-display').innerHTML = `
                        <div class="alert alert-info">
                            Select a reference document to view its contents here.
                        </div>
                    `;

                        // Hide sidebar
                        sidebar.classList.remove('show');
                    }
                })
                .catch(error => {
                    console.error("Error clearing chat:", error);
                });
        } catch (error) {
            console.error("Error clearing chat:", error);
        }
    });

    // Handle search form submission
    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const query = searchInput.value.trim();
        if (!query) return;

        console.log('Submitting search with query:', query);

        // Show loading state
        searchResults.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';

        // Send search query to server
        const formData = new FormData();
        formData.append('query', query);

        fetch('/search', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                console.log('Search response status:', response.status);
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json().catch(err => {
                    console.error('Error parsing search JSON:', err);
                    throw new Error('Failed to parse search response');
                });
            })
            .then(data => {
                console.log('Search results:', data);

                if (data.error) {
                    searchResults.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }

                // Display search results
                if (data.results.length === 0) {
                    searchResults.innerHTML = '<div class="alert alert-info">No results found matching your query.</div>';
                    return;
                }

                searchResults.innerHTML = `<h5 class="mb-3">Search Results <small class="text-muted">(${data.results.length} found)</small></h5>`;

                data.results.forEach(result => {
                    const resultCard = document.createElement('div');
                    resultCard.className = 'card reference-card mb-3';
                    resultCard.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">
                            ${result.title}
                            <span class="badge badge-${result.document_type}">${result.document_type}</span>
                        </h5>
                        <h6 class="card-subtitle mb-2 text-muted">${result.source}</h6>
                        <p class="card-text">${result.content_preview}</p>
                        <button class="btn btn-sm btn-outline-primary search-view-doc" data-doc-id="${result.id}">
                            <i class="fas fa-file-alt me-1"></i> View Document
                        </button>
                    </div>
                `;
                    searchResults.appendChild(resultCard);
                });

                // Add event listeners to search result buttons
                document.querySelectorAll('.search-view-doc').forEach(button => {
                    button.addEventListener('click', function () {
                        const docId = this.dataset.docId;
                        loadDocument(docId);
                    });
                });
            })
            .catch(error => {
                console.error('Error searching:', error);
                searchResults.innerHTML = `<div class="alert alert-danger">Error performing search: ${error.message}</div>`;
            });
    });

    // Example questions click handler
    document.addEventListener('click', function (e) {
        if (e.target.closest('.example-questions li')) {
            const question = e.target.closest('li').textContent.trim();
            userInput.value = question;
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
});
