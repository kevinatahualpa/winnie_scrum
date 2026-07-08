(function() {
    'use strict';

    var overlay, messagesEl, form, input, sendBtn, loadingEl, closeBtn;
    var chatHistory = [];
    var openTrigger = null;

    function init() {
        overlay = document.getElementById('aiOverlay');
        if (!overlay) return;

        messagesEl = document.getElementById('aiMessages');
        form = document.getElementById('aiChatForm');
        input = document.getElementById('aiChatInput');
        sendBtn = document.getElementById('aiSendBtn');
        loadingEl = document.getElementById('aiLoading');
        closeBtn = document.getElementById('aiCloseBtn');
        openTrigger = document.getElementById('aiOpenBtn');

        if (openTrigger) {
            openTrigger.addEventListener('click', open);
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', close);
        }
        if (overlay) {
            overlay.addEventListener('click', function(e) {
                if (e.target === overlay) close();
            });
        }
        if (form) {
            form.addEventListener('submit', handleSend);
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && overlay.classList.contains('open')) {
                close();
            }
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                overlay.classList.contains('open') ? close() : open();
            }
        });
    }

    function open() {
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        input.focus();
            document.body.style.overflow = 'hidden';
    }

    function close() {
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    function setLoading(loading) {
        sendBtn.disabled = loading;
        input.disabled = loading;
        loadingEl.style.display = loading ? 'flex' : 'none';
    }

    function addMessage(role, content) {
        var msgEl = document.createElement('div');
        msgEl.className = 'ai-message ' + role;
        msgEl.innerHTML = formatContent(content);
        messagesEl.appendChild(msgEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function formatContent(text) {
        text = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        var codeBlocks = [];
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(_, lang, code) {
            codeBlocks.push(code);
            return '%%CB' + (codeBlocks.length - 1) + '%%';
        });

        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');

        var lines = text.split('\n');
        var result = [];
        var listBuffer = [];

        for (var i = 0; i < lines.length; i++) {
            var match = lines[i].match(/^[-*] (.+)$/);
            if (match) {
                listBuffer.push('<li>' + match[1] + '</li>');
            } else {
                if (listBuffer.length) {
                    result.push('<ul>' + listBuffer.join('') + '</ul>');
                    listBuffer = [];
                }
                result.push(lines[i] || '');
            }
        }
        if (listBuffer.length) {
            result.push('<ul>' + listBuffer.join('') + '</ul>');
        }

        text = result.join('\n');

        text = text.replace(/%%CB(\d+)%%/g, function(_, idx) {
            return '<pre><code>' + codeBlocks[parseInt(idx)] + '</code></pre>';
        });

        text = text.replace(/\n/g, '<br>');
        return text;
    }

    function handleSend(e) {
        e.preventDefault();
        var text = input.value.trim();
        if (!text) return;

        chatHistory.push({role: 'user', content: text});
        addMessage('user', text);
        input.value = '';
        setLoading(true);

        fetch('/api/ai/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({messages: chatHistory})
        })
        .then(function(resp) {
            if (!resp.ok) {
                return resp.json().then(function(err) {
                    throw new Error(err.error || 'Error ' + resp.status);
                });
            }
            return resp.json();
        })
        .then(function(data) {
            chatHistory.push(data.message);
            addMessage('assistant', data.message.content);
        })
        .catch(function(err) {
            addMessage('assistant', 'Lo siento, hubo un error: ' + err.message + '. Intenta de nuevo.');
        })
        .finally(function() {
            setLoading(false);
            input.focus();
        });
    }

    function getCSRFToken() {
        var meta = document.querySelector('meta[name=csrf-token]');
        if (meta && meta.content) return meta.content;
        var cookie = document.cookie.split(';').find(function(c) {
            return c.trim().startsWith('csrftoken=');
        });
        return cookie ? cookie.split('=')[1] : '';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
