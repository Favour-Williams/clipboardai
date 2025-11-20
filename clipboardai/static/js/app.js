const API_BASE = 'http://localhost:5000/api';
        let currentDetection = null;

        // Paste from clipboard
        async function pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('inputText').value = text;
                showSuccess('Pasted from clipboard!');
                detectContent();
            } catch (err) {
                showError('Failed to read clipboard. Please paste manually (Ctrl+V)');
            }
        }

        // Detect content type
        async function detectContent() {
            const content = document.getElementById('inputText').value;
            if (!content.trim()) {
                showError('Please enter some content first');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/detect`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });

                const result = await response.json();
                currentDetection = result;

                // Show detection info
                document.getElementById('detectionInfo').classList.add('active');
                document.getElementById('contentType').textContent = result.type;
                document.getElementById('confidenceText').textContent = 
                    `Confidence: ${(result.confidence * 100).toFixed(0)}%`;
                document.getElementById('confidenceFill').style.width = 
                    `${result.confidence * 100}%`;
                document.getElementById('suggestedActionsText').textContent = 
                    `Suggested actions: ${result.suggested_actions.slice(0, 3).join(', ')}`;

                // Show action buttons
                renderActionButtons(result.suggested_actions);

            } catch (err) {
                showError('Failed to detect content type');
                console.error(err);
            }
        }

        // Render action buttons
        function renderActionButtons(actions) {
            const grid = document.getElementById('actionsGrid');
            grid.innerHTML = '';

            actions.forEach(action => {
                const btn = document.createElement('button');
                btn.className = 'action-btn';
                btn.textContent = formatActionName(action);
                btn.onclick = () => executeAction(action);
                grid.appendChild(btn);
            });
        }

        // Format action name for display
        function formatActionName(action) {
            return action.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }

        // Execute AI action
        async function executeAction(action) {
            const content = document.getElementById('inputText').value;
            if (!content.trim()) {
                showError('No content to process');
                return;
            }

            // Show loading
            document.getElementById('loading').classList.add('active');
            document.getElementById('outputText').value = '';
            document.getElementById('copyBtn').style.display = 'none';
            hideMessages();

            try {
                const params = {};
                
                // Handle actions that need extra parameters
                if (action === 'translate') {
                    params.target_language = prompt('Enter target language:', 'Spanish') || 'Spanish';
                }
                if (action === 'summarize') {
                    params.target_length = prompt('Target word count:', '50') || '50';
                }

                const response = await fetch(`${API_BASE}/process`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action, content, params })
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('outputText').value = result.result;
                    document.getElementById('tokensUsed').textContent = result.tokens_used;
                    document.getElementById('copyBtn').style.display = 'block';
                    showSuccess(`✅ ${formatActionName(action)} completed! Used ${result.tokens_used} tokens.`);
                    loadHistory();
                    updateStats();
                } else {
                    showError(`Failed: ${result.error}`);
                }

            } catch (err) {
                showError('Failed to process action');
                console.error(err);
            } finally {
                document.getElementById('loading').classList.remove('active');
            }
        }

        // Copy output to clipboard
        async function copyOutput() {
            const text = document.getElementById('outputText').value;
            try {
                await navigator.clipboard.writeText(text);
                showSuccess('Copied to clipboard!');
            } catch (err) {
                showError('Failed to copy to clipboard');
            }
        }

        // Load history
        async function loadHistory() {
            try {
                const response = await fetch(`${API_BASE}/history?limit=20`);
                const data = await response.json();

                const list = document.getElementById('historyList');
                if (data.history.length === 0) {
                    list.innerHTML = '<p style="text-align: center; color: #999;">No history yet. Start using ClipboardAI!</p>';
                    return;
                }

                list.innerHTML = data.history.map(item => `
                    <div class="history-item" onclick="loadHistoryItem(${item.id})">
                        <div class="history-action">${formatActionName(item.action)}</div>
                        <div class="history-preview">${item.input_preview}...</div>
                        <div class="history-meta">
                            ${new Date(item.timestamp).toLocaleString()} • ${item.tokens_used} tokens
                        </div>
                    </div>
                `).join('');

            } catch (err) {
                console.error('Failed to load history', err);
            }
        }

        // Load specific history item
        async function loadHistoryItem(id) {
            try {
                const response = await fetch(`${API_BASE}/history/${id}`);
                const item = await response.json();

                document.getElementById('inputText').value = item.input_text;
                document.getElementById('outputText').value = item.output_text;
                document.getElementById('copyBtn').style.display = 'block';
                showSuccess('Loaded from history');

            } catch (err) {
                showError('Failed to load history item');
            }
        }

        // Update stats
        async function updateStats() {
            try {
                const response = await fetch(`${API_BASE}/stats`);
                const data = await response.json();

                document.getElementById('totalActions').textContent = data.total_requests;

            } catch (err) {
                console.error('Failed to load stats', err);
            }
        }

        // Show success message
        function showSuccess(message) {
            const el = document.getElementById('successMessage');
            el.textContent = message;
            el.classList.add('active');
            setTimeout(() => el.classList.remove('active'), 3000);
        }

        // Show error message
        function showError(message) {
            const el = document.getElementById('errorMessage');
            el.textContent = message;
            el.classList.add('active');
            setTimeout(() => el.classList.remove('active'), 3000);
        }

        // Hide messages
        function hideMessages() {
            document.getElementById('successMessage').classList.remove('active');
            document.getElementById('errorMessage').classList.remove('active');
        }

        // Initialize on page load
        window.onload = () => {
            loadHistory();
            updateStats();
        };
