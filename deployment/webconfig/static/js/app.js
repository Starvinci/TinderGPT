// TinderGPT Web Configuration JavaScript

class WebConfigApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkElements();
        this.loadAllData();
    }
    
    checkElements() {
        console.log('Checking HTML elements...');
        
        const elements = [
            'apiKey', 'tinderAuthToken', 'userName', 'userInfo', 'goalsToBeAchieved',
            'dateInfoName', 'firstMessageDelay', 'randomVariationPercentage', 'minResponseTime',
            'userInfoNone', 'userInfoMinimal', 'userInfoBasic', 'userInfoExtended', 'userInfoFull',
            'defensiveInfoDescription', 'defensiveInfoFavoriteFood', 'defensiveInfoWork',
            'botStatus', 'botVersion', 'activeChats', 'totalMatches', 'excludedChats', 'scheduledResponses'
        ];
        
        const missingElements = [];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (!element) {
                missingElements.push(id);
            }
        });
        
        if (missingElements.length > 0) {
            console.warn('Missing HTML elements:', missingElements);
        } else {
            console.log('All HTML elements found');
        }
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Form submissions
        document.getElementById('generalForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveGeneralConfig();
        });

        document.getElementById('conversationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConversationConfig();
        });

        document.getElementById('timingForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTimingConfig();
        });

        document.getElementById('debugForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveDebugSettings();
        });

        // Match instructions
        document.getElementById('addMatchInstruction').addEventListener('click', () => {
            this.addMatchInstruction();
        });

        // Excluded chats
        document.getElementById('addExcludedChat').addEventListener('click', () => {
            this.addExcludedChat();
        });

        // Bot controls
        document.getElementById('startBot').addEventListener('click', () => {
            this.controlBot('start');
        });

        document.getElementById('stopBot').addEventListener('click', () => {
            this.controlBot('stop');
        });

        // System status
        document.getElementById('refreshStatus').addEventListener('click', () => {
            this.loadBotStatus();
        });

        // Full config save
        document.getElementById('saveFullConfig').addEventListener('click', () => {
            this.saveFullConfig();
        });
    }

    switchTab(tabName) {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');
    }

    async loadAllData() {
        try {
            console.log('Loading all data...');
            await Promise.all([
                this.loadBotStatus(),
                this.loadFullConfig(),
                this.loadConversationConfig(),
                this.loadTimingConfig(),
                this.loadMatchInstructions(),
                this.loadExcludedChats(),
                this.loadDebugSettings(),
                this.loadSystemStatus()
            ]);
            console.log('All data loaded successfully');
        } catch (error) {
            console.error('Error loading all data:', error);
            this.showNotification('Fehler beim Laden der Daten', 'error');
        }
    }

    async loadBotStatus() {
        try {
            console.log('Loading bot status...');
            const response = await fetch('/api/bot_status');
            const status = await response.json();
            
            console.log('Bot status loaded:', status);
            
            if (response.ok) {
                // Update status display
                const botStatusField = document.getElementById('botStatus');
                const botVersionField = document.getElementById('botVersion');
                const activeChatsField = document.getElementById('activeChats');
                const totalMatchesField = document.getElementById('totalMatches');
                const excludedChatsField = document.getElementById('excludedChats');
                const scheduledResponsesField = document.getElementById('scheduledResponses');
                
                if (botStatusField) {
                    botStatusField.textContent = status.is_running ? 'Aktiv' : 'Gestoppt';
                    botStatusField.className = `status-value ${status.is_running ? 'success' : 'error'}`;
                }
                if (botVersionField) botVersionField.textContent = status.current_version || '-';
                if (activeChatsField) activeChatsField.textContent = status.active_chats || 0;
                if (totalMatchesField) totalMatchesField.textContent = status.total_matches || 0;
                if (excludedChatsField) excludedChatsField.textContent = status.excluded_chats || 0;
                if (scheduledResponsesField) scheduledResponsesField.textContent = status.total_scheduled || 0;
                
                // Update scheduled responses list
                this.renderScheduledResponses(status.scheduled_responses || {});
                
                // Update button states
                const startBotBtn = document.getElementById('startBot');
                const stopBotBtn = document.getElementById('stopBot');
                if (startBotBtn) startBotBtn.disabled = status.is_running;
                if (stopBotBtn) stopBotBtn.disabled = !status.is_running;
            }
        } catch (error) {
            console.error('Error loading bot status:', error);
        }
    }

    async loadFullConfig() {
        try {
            console.log('Loading full config...');
            const response = await fetch('/api/config');
            const config = await response.json();
            
            console.log('Config loaded:', config);
            
            if (response.ok) {
                // API Configuration
                const apiKeyField = document.getElementById('apiKey');
                const tinderAuthField = document.getElementById('tinderAuthToken');
                if (apiKeyField) apiKeyField.value = config.api_key || '';
                if (tinderAuthField) tinderAuthField.value = config['tinder-auth-token'] || '';
                
                // User Information
                const userNameField = document.getElementById('userName');
                const userInfoField = document.getElementById('userInfo');
                if (userNameField) userNameField.value = config.user_name || '';
                if (userInfoField) userInfoField.value = config.user_info || '';
                
                // Goals
                const goalsField = document.getElementById('goalsToBeAchieved');
                if (goalsField) goalsField.value = config.goals_to_be_achieved || '';
                
                // Date Info
                if (config.date_info) {
                    const dateInfoField = document.getElementById('dateInfoName');
                    if (dateInfoField) dateInfoField.value = config.date_info.name || '';
                }
                
                // Response Timing
                if (config.response_timing) {
                    document.getElementById('firstMessageDelay').value = config.response_timing.first_message_delay || '';
                    document.getElementById('randomVariationPercentage').value = config.response_timing.random_variation_percentage || '';
                    document.getElementById('minResponseTime').value = config.response_timing.min_response_time || '';
                }
                
                // Tim Info Levels
                if (config.user_info_levels) {
                    document.getElementById('userInfoNone').value = config.user_info_levels.none || '';
                    document.getElementById('userInfoMinimal').value = config.user_info_levels.minimal || '';
                    document.getElementById('userInfoBasic').value = config.user_info_levels.basic || '';
                    document.getElementById('userInfoExtended').value = config.user_info_levels.extended || '';
                    document.getElementById('userInfoFull').value = config.user_info_levels.full || '';
                }
                
                // Defensive Info
                if (config.defensive_info) {
                    document.getElementById('defensiveInfoDescription').value = config.defensive_info.description || '';
                    document.getElementById('defensiveInfoFavoriteFood').value = config.defensive_info.favorite_food || '';
                    document.getElementById('defensiveInfoWork').value = config.defensive_info.work || '';
                    document.getElementById('defensiveInfoTravel').value = config.defensive_info.travel || '';
                    
                }
            }
        } catch (error) {
            console.error('Error loading full config:', error);
        }
    }

    async loadConversationConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            if (response.ok) {
                const phases = config.conversation_phases || {};
                
                // Icebreaker
                if (phases.icebreaker) {
                    document.getElementById('icebreakerGoal').value = phases.icebreaker.goal || '';
                    document.getElementById('icebreakerMaxMessages').value = phases.icebreaker.max_messages || '';
                }
                
                // Interests
                if (phases.interests) {
                    document.getElementById('interestsGoal').value = phases.interests.goal || '';
                    document.getElementById('interestsMaxMessages').value = phases.interests.max_messages || '';
                }
                
                // Compatibility
                if (phases.compatibility) {
                    document.getElementById('compatibilityGoal').value = phases.compatibility.goal || '';
                    document.getElementById('compatibilityMaxMessages').value = phases.compatibility.max_messages || '';
                }
                
                // Defensive info
                document.getElementById('defensiveInfo').value = config.defensive_info || '';
            }
        } catch (error) {
            console.error('Error loading conversation config:', error);
        }
    }

    async loadTimingConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            if (response.ok) {
                const timing = config.response_timing || {};
                
                document.getElementById('minResponseDelay').value = timing.min_delay_minutes || '';
                document.getElementById('maxResponseDelay').value = timing.max_delay_minutes || '';
                document.getElementById('randomFactor').value = timing.random_factor || '';
                document.getElementById('newMatchDelay').value = timing.new_match_delay_minutes || '';
            }
        } catch (error) {
            console.error('Error loading timing config:', error);
        }
    }

    async loadMatchInstructions() {
        try {
            const response = await fetch('/api/match_instructions');
            const instructions = await response.json();
            
            if (response.ok) {
                this.renderMatchInstructions(instructions);
            }
        } catch (error) {
            console.error('Error loading match instructions:', error);
        }
    }

    async loadExcludedChats() {
        try {
            const response = await fetch('/api/excluded_chats');
            const excludedChats = await response.json();
            
            if (response.ok) {
                this.renderExcludedChats(excludedChats);
            }
        } catch (error) {
            console.error('Error loading excluded chats:', error);
        }
    }

    async loadDebugSettings() {
        try {
            const response = await fetch('/api/debug_settings');
            const debugSettings = await response.json();
            
            if (response.ok) {
                document.getElementById('botDebug').checked = debugSettings.bot_debug || false;
                document.getElementById('apiDebug').checked = debugSettings.api_debug || false;
                document.getElementById('chatDebug').checked = debugSettings.chat_debug || false;
                document.getElementById('storageDebug').checked = debugSettings.storage_debug || false;
            }
        } catch (error) {
            console.error('Error loading debug settings:', error);
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system_status');
            const status = await response.json();
            
            if (response.ok) {
                this.renderSystemStatus(status);
            }
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    async controlBot(action) {
        try {
            const response = await fetch('/api/bot_control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, result.success ? 'success' : 'warning');
                // Refresh bot status after action
                setTimeout(() => this.loadBotStatus(), 1000);
            } else {
                this.showNotification(result.error || 'Fehler bei Bot-Steuerung', 'error');
            }
        } catch (error) {
            this.showNotification('Fehler bei Bot-Steuerung', 'error');
        }
    }

    async saveFullConfig() {
        try {
            // Collect all form data
            const config = {
                api_key: document.getElementById('apiKey').value,
                'tinder-auth-token': document.getElementById('tinderAuthToken').value,
                user_name: document.getElementById('userName').value,
                user_info: document.getElementById('userInfo').value,
                goals_to_be_achieved: document.getElementById('goalsToBeAchieved').value,
                date_info: {
                    name: document.getElementById('dateInfoName').value
                },
                response_timing: {
                    first_message_delay: parseInt(document.getElementById('firstMessageDelay').value) || 0,
                    random_variation_percentage: parseInt(document.getElementById('randomVariationPercentage').value) || 0,
                    min_response_time: parseInt(document.getElementById('minResponseTime').value) || 0
                },
                user_info_levels: {
                    none: document.getElementById('userInfoNone').value,
                    minimal: document.getElementById('userInfoMinimal').value,
                    basic: document.getElementById('userInfoBasic').value,
                    extended: document.getElementById('userInfoExtended').value,
                    full: document.getElementById('userInfoFull').value
                },
                defensive_info: {
                    description: document.getElementById('defensiveInfoDescription').value,
                    favorite_food: document.getElementById('defensiveInfoFavoriteFood').value,
                    work: document.getElementById('defensiveInfoWork').value,
                    travel: document.getElementById('defensiveInfoTravel').value
                }
            };
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Vollständige Konfiguration gespeichert', 'success');
            } else {
                this.showNotification(result.error || 'Fehler beim Speichern', 'error');
            }
        } catch (error) {
            this.showNotification('Fehler beim Speichern', 'error');
        }
    }

    renderScheduledResponses(scheduledResponses) {
        const container = document.getElementById('scheduledResponsesList');
        container.innerHTML = '';
        
        if (Object.keys(scheduledResponses).length === 0) {
            container.innerHTML = '<p class="text-muted">Keine geplanten Antworten</p>';
            return;
        }
        
        Object.entries(scheduledResponses).forEach(([matchId, data]) => {
            const item = document.createElement('div');
            item.className = 'scheduled-response-item';
            
            const remainingTime = data.remaining_minutes > 0 ? 
                `${data.remaining_minutes.toFixed(1)}min verbleibend` : 
                'Bereit zum Senden';
            
            item.innerHTML = `
                <div class="scheduled-response-info">
                    <div class="scheduled-response-match">${data.match_name}</div>
                    <div class="scheduled-response-time">${remainingTime} (geplant: ${(data.delay_seconds / 60).toFixed(1)}min)</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    async saveConversationConfig() {
        try {
            const formData = new FormData(document.getElementById('conversationForm'));
            const config = {
                conversation_phases: {
                    icebreaker: {
                        goal: formData.get('conversation_phases.icebreaker.goal'),
                        max_messages: parseInt(formData.get('conversation_phases.icebreaker.max_messages')) || 0
                    },
                    interests: {
                        goal: formData.get('conversation_phases.interests.goal'),
                        max_messages: parseInt(formData.get('conversation_phases.interests.max_messages')) || 0
                    },
                    compatibility: {
                        goal: formData.get('conversation_phases.compatibility.goal'),
                        max_messages: parseInt(formData.get('conversation_phases.compatibility.max_messages')) || 0
                    }
                },
                defensive_info: formData.get('defensive_info')
            };
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Konversationskonfiguration gespeichert', 'success');
            } else {
                this.showNotification(result.error || 'Fehler beim Speichern', 'error');
            }
        } catch (error) {
            this.showNotification('Fehler beim Speichern', 'error');
        }
    }

    async saveTimingConfig() {
        try {
            const formData = new FormData(document.getElementById('timingForm'));
            const config = {
                response_timing: {
                    min_delay_minutes: parseFloat(formData.get('response_timing.min_delay_minutes')) || 0,
                    max_delay_minutes: parseFloat(formData.get('response_timing.max_delay_minutes')) || 0,
                    random_factor: parseFloat(formData.get('response_timing.random_factor')) || 0,
                    new_match_delay_minutes: parseFloat(formData.get('response_timing.new_match_delay_minutes')) || 0
                }
            };
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Timing-Konfiguration gespeichert', 'success');
            } else {
                this.showNotification(result.error || 'Fehler beim Speichern', 'error');
            }
        } catch (error) {
            this.showNotification('Fehler beim Speichern', 'error');
        }
    }

    async saveDebugSettings() {
        try {
            const formData = new FormData(document.getElementById('debugForm'));
            const debugSettings = {
                bot_debug: formData.has('bot_debug'),
                api_debug: formData.has('api_debug'),
                chat_debug: formData.has('chat_debug'),
                storage_debug: formData.has('storage_debug')
            };
            
            const response = await fetch('/api/debug_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(debugSettings)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Debug-Einstellungen gespeichert', 'success');
            } else {
                this.showNotification(result.error || 'Fehler beim Speichern', 'error');
            }
        } catch (error) {
            this.showNotification('Fehler beim Speichern', 'error');
        }
    }

    async addMatchInstruction() {
        const name = document.getElementById('newMatchName').value.trim();
        const instruction = document.getElementById('newMatchInstruction').value.trim();
        
        if (!name || !instruction) {
            this.showNotification('Bitte Name und Anweisung eingeben', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/match_instructions');
            const instructions = await response.json();
            
            if (response.ok) {
                instructions[name] = instruction;
                
                const saveResponse = await fetch('/api/match_instructions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(instructions)
                });
                
                const result = await saveResponse.json();
                
                if (saveResponse.ok) {
                    this.showNotification('Match-Anweisung hinzugefügt', 'success');
                    this.renderMatchInstructions(instructions);
                    document.getElementById('newMatchName').value = '';
                    document.getElementById('newMatchInstruction').value = '';
                } else {
                    this.showNotification(result.error || 'Fehler beim Speichern', 'error');
                }
            }
        } catch (error) {
            this.showNotification('Fehler beim Hinzufügen', 'error');
        }
    }

    async addExcludedChat() {
        const chatName = document.getElementById('newExcludedChat').value.trim();
        
        if (!chatName) {
            this.showNotification('Bitte Chat-Namen eingeben', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/excluded_chats');
            const excludedChats = await response.json();
            
            if (response.ok) {
                if (!excludedChats.includes(chatName)) {
                    excludedChats.push(chatName);
                    
                    const saveResponse = await fetch('/api/excluded_chats', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(excludedChats)
                    });
                    
                    const result = await saveResponse.json();
                    
                    if (saveResponse.ok) {
                        this.showNotification('Chat ausgeschlossen', 'success');
                        this.renderExcludedChats(excludedChats);
                        document.getElementById('newExcludedChat').value = '';
                    } else {
                        this.showNotification(result.error || 'Fehler beim Speichern', 'error');
                    }
                } else {
                    this.showNotification('Chat ist bereits ausgeschlossen', 'warning');
                }
            }
        } catch (error) {
            this.showNotification('Fehler beim Ausschließen', 'error');
        }
    }

    async removeMatchInstruction(name) {
        try {
            const response = await fetch('/api/match_instructions');
            const instructions = await response.json();
            
            if (response.ok) {
                delete instructions[name];
                
                const saveResponse = await fetch('/api/match_instructions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(instructions)
                });
                
                const result = await saveResponse.json();
                
                if (saveResponse.ok) {
                    this.showNotification('Match-Anweisung entfernt', 'success');
                    this.renderMatchInstructions(instructions);
                } else {
                    this.showNotification(result.error || 'Fehler beim Entfernen', 'error');
                }
            }
        } catch (error) {
            this.showNotification('Fehler beim Entfernen', 'error');
        }
    }

    async removeExcludedChat(chatName) {
        try {
            const response = await fetch('/api/excluded_chats');
            const excludedChats = await response.json();
            
            if (response.ok) {
                const filteredChats = excludedChats.filter(chat => chat !== chatName);
                
                const saveResponse = await fetch('/api/excluded_chats', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(filteredChats)
                });
                
                const result = await saveResponse.json();
                
                if (saveResponse.ok) {
                    this.showNotification('Chat wieder eingeschlossen', 'success');
                    this.renderExcludedChats(filteredChats);
                } else {
                    this.showNotification(result.error || 'Fehler beim Einschließen', 'error');
                }
            }
        } catch (error) {
            this.showNotification('Fehler beim Einschließen', 'error');
        }
    }

    renderMatchInstructions(instructions) {
        const container = document.getElementById('matchInstructionsList');
        container.innerHTML = '';
        
        if (Object.keys(instructions).length === 0) {
            container.innerHTML = '<p class="text-muted">Keine Match-Anweisungen vorhanden</p>';
            return;
        }
        
        Object.entries(instructions).forEach(([name, instruction]) => {
            const item = document.createElement('div');
            item.className = 'instruction-item';
            item.innerHTML = `
                <div>
                    <div class="match-name">${name}</div>
                    <div class="instruction-text">${instruction}</div>
                </div>
                <button class="remove-btn" onclick="app.removeMatchInstruction('${name}')">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
    }

    renderExcludedChats(excludedChats) {
        const container = document.getElementById('excludedChatsList');
        container.innerHTML = '';
        
        if (excludedChats.length === 0) {
            container.innerHTML = '<p class="text-muted">Keine ausgeschlossenen Chats</p>';
            return;
        }
        
        excludedChats.forEach(chatName => {
            const item = document.createElement('div');
            item.className = 'excluded-item';
            item.innerHTML = `
                <div class="chat-name">${chatName}</div>
                <button class="remove-btn" onclick="app.removeExcludedChat('${chatName}')">
                    <i class="fas fa-plus"></i> Einschließen
                </button>
            `;
            container.appendChild(item);
        });
    }

    renderSystemStatus(status) {
        const container = document.getElementById('systemStatus');
        container.innerHTML = '';
        
        const items = [
            { label: 'Konfigurationsdatei', value: status.config_exists ? 'Vorhanden' : 'Fehlt', type: status.config_exists ? 'success' : 'error' },
            { label: 'Match-Anweisungen', value: status.match_instructions_exists ? 'Vorhanden' : 'Fehlt', type: status.match_instructions_exists ? 'success' : 'warning' },
            { label: 'Persistente Daten', value: status.persistent_data_exists ? 'Vorhanden' : 'Fehlt', type: status.persistent_data_exists ? 'success' : 'warning' },
            { label: 'Letzte Aktualisierung', value: new Date(status.timestamp).toLocaleString('de-DE'), type: 'info' }
        ];
        
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'status-item';
            div.innerHTML = `
                <span class="status-label">${item.label}:</span>
                <span class="status-value ${item.type}">${item.value}</span>
            `;
            container.appendChild(div);
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WebConfigApp();
});
