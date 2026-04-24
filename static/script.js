document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const chatContainer = document.getElementById('chat-container');
    const sendBtn = document.getElementById('send-btn');
    const suggestionsList = document.getElementById('suggestions-list');
    const statusDot = document.querySelector('.dot');
    const statusText = document.querySelector('.status-text');

    let conversationId = null;

    // Seed questions
    const suggestions = [
        "Show me the top 5 patients by total amount billed",
        "What are the most common treatments?",
        "Show monthly revenue trend",
        "Which doctor has the most appointments?"
    ];

    // Populate suggestions
    suggestions.forEach(q => {
        const li = document.createElement('li');
        li.textContent = q;
        li.addEventListener('click', () => {
            queryInput.value = q;
            chatForm.dispatchEvent(new Event('submit'));
        });
        suggestionsList.appendChild(li);
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = queryInput.value.trim();
        if (!message) return;

        // Disable input
        queryInput.value = '';
        queryInput.disabled = true;
        sendBtn.disabled = true;

        // Add user message
        appendMessage('user', message);

        // Add typing indicator
        const typingIndicator = showTypingIndicator();

        try {
            statusDot.classList.replace('online', 'working');
            statusDot.style.background = '#f59e0b';
            statusDot.style.boxShadow = '0 0 8px #f59e0b';
            statusText.textContent = 'Analyzing...';

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    conversation_id: conversationId 
                })
            });

            const data = await response.json();
            
            // Remove typing indicator
            typingIndicator.remove();

            if (data.conversation_id) {
                conversationId = data.conversation_id;
            }

            if (data.error) {
                appendMessage('assistant', `❌ Error: ${data.error}`);
            } else {
                appendAssistantResponse(data);
            }

        } catch (error) {
            typingIndicator.remove();
            appendMessage('assistant', `❌ Connection error: ${error.message}`);
        } finally {
            statusDot.classList.replace('working', 'online');
            statusDot.style.background = '#10b981';
            statusDot.style.boxShadow = '0 0 8px #10b981';
            statusText.textContent = 'Connected';
            
            queryInput.disabled = false;
            sendBtn.disabled = false;
            queryInput.focus();
        }
    });

    function appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant typing';
        msgDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        `;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv;
    }

    function appendAssistantResponse(data) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // 1. Text Summary
        if (data.summary) {
            const p = document.createElement('p');
            p.textContent = data.summary;
            contentDiv.appendChild(p);
        }

        // 2. SQL Code
        if (data.sql) {
            const block = document.createElement('div');
            block.className = 'block';
            block.innerHTML = `
                <div class="block-header">Generated SQL</div>
                <pre><code class="language-sql">${escapeHtml(data.sql)}</code></pre>
            `;
            contentDiv.appendChild(block);
        }

        // 3. Chart
        if (data.chart) {
            const block = document.createElement('div');
            block.className = 'block';
            block.innerHTML = `<div class="block-header">Visualization</div>`;
            
            const chartDiv = document.createElement('div');
            chartDiv.id = 'chart-' + Math.random().toString(36).substr(2, 9);
            chartDiv.className = 'chart-container';
            block.appendChild(chartDiv);
            contentDiv.appendChild(block);

            // Render Plotly chart after adding to DOM
            setTimeout(() => {
                // Adjust layout for dark theme
                const layout = data.chart.layout || {};
                layout.paper_bgcolor = 'transparent';
                layout.plot_bgcolor = 'transparent';
                layout.font = { color: '#94a3b8' };
                layout.margin = { t: 40, b: 40, l: 40, r: 40 };

                Plotly.newPlot(chartDiv.id, data.chart.data, layout, {responsive: true});
            }, 50);
        }

        // 4. Data Table
        if (data.data && data.data.length > 0 && data.columns) {
            const block = document.createElement('div');
            block.className = 'block';
            block.innerHTML = `<div class="block-header">Data Results (${data.data.length} rows)</div>`;
            
            const template = document.getElementById('table-template');
            const tableClone = template.content.cloneNode(true);
            
            const theadTr = tableClone.querySelector('thead tr');
            data.columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                theadTr.appendChild(th);
            });

            const tbody = tableClone.querySelector('tbody');
            // Limit to 50 rows in UI to prevent freezing
            const displayData = data.data.slice(0, 50);
            displayData.forEach(row => {
                const tr = document.createElement('tr');
                data.columns.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row[col] !== null ? row[col] : 'NULL';
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });

            if (data.data.length > 50) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = data.columns.length;
                td.style.textAlign = 'center';
                td.style.color = '#94a3b8';
                td.textContent = `... showing first 50 of ${data.data.length} rows ...`;
                tr.appendChild(td);
                tbody.appendChild(tr);
            }

            block.appendChild(tableClone);
            contentDiv.appendChild(block);
        }

        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        
        // Apply syntax highlighting
        msgDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        scrollToBottom();
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
