// PyClaw Chat JavaScript - 通过 pyclaw-web 后端代理（不直接连 Gateway）

class PyClawChat {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;  // pyclaw-web 后端地址
        this.connected = false;
        this.messagesEl = document.getElementById('chat-messages');
        this.inputEl = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.wsStatusEl = document.getElementById('ws-status');
        this.wsTextEl = document.getElementById('ws-text');
        
        this.init();
    }
    
    init() {
        // 绑定事件
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        document.getElementById('clear-chat').addEventListener('click', () => {
            this.messagesEl.innerHTML = '';
            this.addSystemMessage('对话已清空');
        });
        
        // 检查后端连接状态
        this.checkStatus();
    }
    
    async checkStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/status`);
            const status = await response.json();
            
            if (status.status === 'online') {
                this.connected = true;
                this.updateStatus('connected', '已连接 (通过后端代理)');
                this.sendBtn.disabled = false;
                this.addSystemMessage('已连接到 PyClaw Web 后端');
            } else {
                throw new Error('后端未在线');
            }
        } catch (error) {
            console.error('连接失败:', error);
            this.connected = false;
            this.updateStatus('disconnected', '连接失败');
            this.sendBtn.disabled = true;
            this.addSystemMessage('无法连接到后端：' + error.message);
        }
    }
    
    async sendMessage() {
        const content = this.inputEl.value.trim();
        if (!content || !this.connected) return;
        
        // 显示用户消息
        this.addMessage('user', content);
        this.inputEl.value = '';
        this.sendBtn.disabled = true;
        
        try {
            // 通过 HTTP POST 发送到后端
            const response = await fetch(`${this.baseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: 'agent:main:web-user',
                    message: content,
                    mode: 'single',
                }),
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addMessage('assistant', result.message);
            } else {
                this.addSystemMessage('错误：' + result.message);
            }
        } catch (error) {
            console.error('发送失败:', error);
            this.addSystemMessage('发送失败：' + error.message);
        } finally {
            this.sendBtn.disabled = false;
        }
    }
    
    addMessage(role, content) {
        const msgEl = document.createElement('div');
        msgEl.className = `message ${role}`;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN');
        msgEl.innerHTML = `
            <div class="message-content">
                ${this.escapeHtml(content)}
                ${document.getElementById('show-timestamp').checked ? 
                    `<div class="message-time">${timestamp}</div>` : ''}
            </div>
        `;
        
        this.messagesEl.appendChild(msgEl);
        this.scrollToBottom();
    }
    
    addSystemMessage(content) {
        const msgEl = document.createElement('div');
        msgEl.className = 'message system';
        msgEl.innerHTML = `<div class="message-content">${this.escapeHtml(content)}</div>`;
        this.messagesEl.appendChild(msgEl);
        this.scrollToBottom();
    }
    
    updateStatus(status, text) {
        this.wsStatusEl.className = `status-dot ${status}`;
        this.wsTextEl.textContent = text;
    }
    
    scrollToBottom() {
        if (document.getElementById('auto-scroll').checked) {
            this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }
}

// 初始化聊天
const gatewayUrl = window.location.protocol === 'https:' 
    ? 'wss://127.0.0.1:18790' 
    : 'ws://127.0.0.1:18790';

const chat = new PyClawChat(gatewayUrl);
