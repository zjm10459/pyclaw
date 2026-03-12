// PyClaw Chat JavaScript

class PyClawChat {
    constructor(gatewayUrl) {
        this.gatewayUrl = gatewayUrl;
        this.ws = null;
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
        
        // 连接 WebSocket
        this.connect();
    }
    
    connect() {
        this.updateStatus('connecting', '连接中...');
        
        try {
            this.ws = new WebSocket(this.gatewayUrl.replace('ws://', 'http://').replace('wss://', 'https://'));
            
            this.ws.onopen = () => {
                this.connected = true;
                this.updateStatus('connected', '已连接');
                this.sendBtn.disabled = false;
                this.addSystemMessage('已连接到 PyClaw Gateway');
                
                // 发送 connect 请求
                this.sendConnect();
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.updateStatus('disconnected', '已断开');
                this.sendBtn.disabled = true;
                this.addSystemMessage('连接已断开');
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
                this.updateStatus('disconnected', '连接失败');
            };
        } catch (error) {
            console.error('连接失败:', error);
            this.updateStatus('disconnected', '连接失败');
        }
    }
    
    sendConnect() {
        const connectMsg = {
            id: 'web-connect-' + Date.now(),
            method: 'connect',
            params: {
                auth: {},
                device: {
                    device_id: 'web-client',
                    name: 'PyClaw Web'
                }
            }
        };
        
        this.ws.send(JSON.stringify(connectMsg));
    }
    
    sendMessage() {
        const content = this.inputEl.value.trim();
        if (!content || !this.connected) return;
        
        // 显示用户消息
        this.addMessage('user', content);
        this.inputEl.value = '';
        
        // 发送 agent 请求
        const agentMsg = {
            id: 'web-agent-' + Date.now(),
            method: 'agent',
            params: {
                sessionKey: 'agent:main:web-user',
                messages: [
                    {
                        role: 'user',
                        content: content
                    }
                ]
            }
        };
        
        this.ws.send(JSON.stringify(agentMsg));
    }
    
    handleMessage(data) {
        try {
            const response = JSON.parse(data);
            console.log('收到响应:', response);
            
            if (response.ok && response.result) {
                const result = response.result;
                
                // 处理 agent 响应
                if (result.content) {
                    this.addMessage('assistant', result.content);
                }
                
                // 处理 connect 响应
                if (result.status === 'hello-ok') {
                    this.addSystemMessage(`Gateway 版本：${result.version}`);
                }
            } else if (response.error) {
                this.addSystemMessage('错误：' + response.error);
            }
        } catch (error) {
            console.error('解析响应失败:', error);
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
