
from flask import Flask, render_template, request, jsonify
import threading
import time
import json
import os
import uuid
import datetime
from virtual_assistant import VirtualAssistant

app = Flask(__name__)
assistant = VirtualAssistant()

# File to store reminders
REMINDERS_FILE = 'reminders.json'

# Load existing reminders from file
def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

# Save reminders to file
def save_reminders(reminders_list):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders_list, f)

# Initialize reminders from file
reminders = load_reminders()
# Track which reminders have been shown in chat
shown_reminders = set()
# Track active reminders (those that are scheduled but not yet triggered)
active_reminders = {}

# Override the reminder manager's _remind method
original_remind = assistant.reminder_manager._remind
def web_remind(delay, message):
    # Generate a unique ID for this reminder
    reminder_id = str(uuid.uuid4())
    
    # Calculate when this reminder will trigger
    trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=delay)
    formatted_time = trigger_time.strftime("%I:%M %p")
    
    # Add to reminders list
    new_reminder = {
        "id": reminder_id,
        "time": time.strftime("%H:%M:%S"),
        "trigger_time": formatted_time,
        "message": message,
        "triggered": False
    }
    reminders.append(new_reminder)
    save_reminders(reminders)
    
    # Store in active reminders
    active_reminders[reminder_id] = {
        "delay": delay,
        "message": message,
        "start_time": time.time()
    }
    
    # Start a thread to handle this reminder
    def reminder_thread():
        time.sleep(delay)
        # Mark as triggered
        for r in reminders:
            if r["id"] == reminder_id:
                r["triggered"] = True
                save_reminders(reminders)
                break
        # Remove from active reminders
        if reminder_id in active_reminders:
            del active_reminders[reminder_id]

    thread = threading.Thread(target=reminder_thread)
    thread.daemon = True
    thread.start()

assistant.reminder_manager._remind = web_remind

# Store conversation history
conversation = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query', '')
    
    # Add user query to conversation
    conversation.append({"sender": "You", "message": query})
    
    # Process the query
    response = assistant.process_query(query)
    
    # Add assistant response to conversation
    conversation.append({"sender": "Assistant", "message": response})
    
    return jsonify({
        "response": response,
        "conversation": conversation,
        "reminders": reminders
    })

@app.route('/check_reminders')
def check_reminders():
    # Find triggered reminders that haven't been shown yet
    triggered_reminders = []
    for reminder in reminders:
        if reminder.get("triggered", False) and reminder["id"] not in shown_reminders:
            triggered_reminders.append(reminder)
            shown_reminders.add(reminder["id"])
    
    return jsonify({
        "reminders": reminders,
        "triggered": triggered_reminders
    })

@app.route('/delete_reminder', methods=['POST'])
def delete_reminder():
    reminder_id = request.json.get('id', '')
    
    global reminders
    reminders = [r for r in reminders if r['id'] != reminder_id]
    save_reminders(reminders)
    
    # Also remove from active reminders if it's there
    if reminder_id in active_reminders:
        del active_reminders[reminder_id]
    
    return jsonify({"success": True, "reminders": reminders})

# Create templates directory and HTML file
if not os.path.exists('templates'):
    os.makedirs('templates')

with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Virtual Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    <style>
        :root {
            --primary-color: #5c6bc0;
            --primary-light: #8e99f3;
            --primary-dark: #26418f;
            --secondary-color: #ff7043;
            --text-color: #333333;
            --text-light: #757575;
            --bg-color: #f5f7fa;
            --card-color: #ffffff;
            --danger-color: #f44336;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --border-radius: 12px;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 0;
            margin: 0;
            min-height: 100vh;
        }
        
        .app-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .app-header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        
        .app-logo {
            display: flex;
            align-items: center;
            font-size: 24px;
            font-weight: 500;
            color: var(--primary-color);
        }
        
        .app-logo i {
            margin-right: 10px;
            font-size: 32px;
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 25px;
        }
        
        .chat-section {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 120px);
        }
        
        .chat-container {
            flex-grow: 1;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 20px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .message {
            margin-bottom: 16px;
            max-width: 85%;
            position: relative;
        }
        
        .message-content {
            padding: 12px 16px;
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .user {
            margin-left: auto;
        }
        
        .user .message-content {
            background-color: var(--primary-color);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .assistant .message-content {
            background-color: #f0f2f5;
            color: var(--text-color);
            border-bottom-left-radius: 4px;
        }
        
        .reminder .message-content {
            background-color: #fff3e0;
            color: var(--text-color);
            border-left: 3px solid var(--warning-color);
        }
        
        .sender {
            font-size: 12px;
            color: var(--text-light);
            margin-bottom: 4px;
            font-weight: 500;
        }
        
        .input-container {
            display: flex;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 15px;
            position: relative;
        }
        
        #user-input {
            flex-grow: 1;
            border: none;
            background-color: transparent;
            padding: 10px 15px;
            font-size: 16px;
            outline: none;
            color: var(--text-color);
        }
        
        .send-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .send-btn:hover {
            background-color: var(--primary-dark);
        }
        
        .quick-commands {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .quick-command {
            background-color: var(--card-color);
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-color);
        }
        
        .quick-command:hover {
            background-color: var(--primary-light);
            color: white;
            border-color: var(--primary-light);
        }
        
        .reminders-section {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 20px;
            height: fit-content;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            color: var(--primary-color);
        }
        
        .section-header i {
            margin-right: 10px;
        }
        
        .reminder-item {
            background-color: #f9f9f9;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            position: relative;
            transition: all 0.2s;
            border-left: 4px solid var(--primary-color);
        }
        
        .reminder-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .reminder-time {
            font-size: 12px;
            color: var(--text-light);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        
        .reminder-time i {
            font-size: 14px;
            margin-right: 5px;
        }
        
        .reminder-message {
            font-weight: 500;
            margin-right: 25px;
        }
        
        .delete-reminder {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: transparent;
            color: var(--text-light);
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 18px;
        }
        
        .delete-reminder:hover {
            background-color: rgba(244, 67, 54, 0.1);
            color: var(--danger-color);
        }
        
        .triggered {
            border-left-color: var(--warning-color);
            background-color: #fff8e6;
        }
        
        .no-reminders {
            color: var(--text-light);
            font-style: italic;
            text-align: center;
            padding: 20px 0;
        }
        
        .clear-all-btn {
            background-color: var(--danger-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px;
            width: 100%;
            cursor: pointer;
            transition: background-color 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 15px;
        }
        
        .clear-all-btn i {
            margin-right: 8px;
        }
        
        .clear-all-btn:hover {
            background-color: #d32f2f;
        }
        
        @media (max-width: 900px) {
            .main-container {
                grid-template-columns: 1fr;
            }
            
            .chat-section, .reminders-section {
                height: auto;
                max-height: none;
            }
            
            .chat-container {
                height: 400px;
            }
        }
        
        .quick-command-group {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--card-color);
            padding: 8px;
            border-radius: 20px;
            border: 1px solid rgba(0,0,0,0.08);
        }
        
        .reminder-inputs {
            display: flex;
            gap: 8px;
        }
        
        .time-input {
            width: 100px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 14px;
            outline: none;
        }
        
        .message-input {
            width: 200px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 14px;
            outline: none;
        }
        
        .set-reminder-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 15px;
            padding: 8px 16px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .set-reminder-btn:hover {
            background-color: var(--primary-dark);
        }
    </style>
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <div class="app-logo">
                <span>Virtual Assistant</span>
            </div>
        </header>
        
        <div class="main-container">
            <div class="chat-section">
                <div class="chat-container" id="chat-container">
                    <div class="message assistant">
                        <div class="sender">Assistant</div>
                        <div class="message-content">
                            Virtual Assistant is ready! Type 'help' for available commands.
                        </div>
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="user-input" placeholder="Type your message here..." autofocus>
                    <button class="send-btn" onclick="sendMessage()">
                        <i class="material-icons">send</i>
                    </button>
                </div>
                
                <div class="quick-commands">
                    <div class="quick-command-group">
                        <div class="reminder-inputs">
                            <input type="time" id="reminder-time" class="time-input">
                            <input type="text" id="reminder-message" class="message-input" placeholder="Reminder message">
                        </div>
                        <button class="set-reminder-btn" onclick="setQuickReminder()">
                            Set Reminder
                        </button>
                    </div>
                    <button class="quick-command" onclick="quickCommand('What time is it?')">
                        Check time
                    </button>
                    <button class="quick-command" onclick="quickCommand('Tell me a joke')">
                        Tell a joke
                    </button>
                    <button class="quick-command" onclick="quickCommand('Help')">
                        Help
                    </button>
                </div>
            </div>
            
            <div class="reminders-section">
                <div class="section-header">
                    <i class="material-icons">notifications</i>
                    <h2>Reminders</h2>
                </div>
                
                <div id="reminders-list">
                    <div class="no-reminders">No reminders set</div>
                </div>
                
                <button id="clear-all-btn" class="clear-all-btn" onclick="clearAllReminders()" style="display: none;">
                    <i class="material-icons">delete_sweep</i>
                    Clear All Reminders
                </button>
            </div>
        </div>
    </div>

    <script>
        // Handle Enter key in input field
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Send message to backend
        function sendMessage() {
            const userInput = document.getElementById('user-input');
            const query = userInput.value.trim();
            
            if (!query) return;
            
            // Add user message to chat
            addMessageToChat('You', query, 'user');
            
            // Clear input field
            userInput.value = '';
            
            // Send to backend
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                // Add assistant response to chat
                addMessageToChat('Assistant', data.response, 'assistant');
                
                // Update reminders list
                updateRemindersList(data.reminders);
            });
        }
        
        // Add message to chat container
        function addMessageToChat(sender, message, messageClass) {
            const chatContainer = document.getElementById('chat-container');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${messageClass}`;
            
            const senderDiv = document.createElement('div');
            senderDiv.className = 'sender';
            senderDiv.textContent = sender;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message;
            
            messageDiv.appendChild(senderDiv);
            messageDiv.appendChild(contentDiv);
            
            chatContainer.appendChild(messageDiv);
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Handle quick command buttons
        function quickCommand(command) {
            document.getElementById('user-input').value = command;
            sendMessage();
        }
        
        // Update reminders list
        function updateRemindersList(reminders) {
            const remindersList = document.getElementById('reminders-list');
            const clearAllBtn = document.getElementById('clear-all-btn');
            
            // Clear current list
            remindersList.innerHTML = '';
            
            if (reminders.length === 0) {
                const noReminders = document.createElement('div');
                noReminders.className = 'no-reminders';
                noReminders.textContent = 'No reminders set';
                remindersList.appendChild(noReminders);
                clearAllBtn.style.display = 'none';
                return;
            }
            
            // Show clear all button
            clearAllBtn.style.display = 'flex';
            
            // Add each reminder
            reminders.forEach(reminder => {
                const reminderItem = document.createElement('div');
                reminderItem.className = 'reminder-item';
                if (reminder.triggered) {
                    reminderItem.className += ' triggered';
                }
                reminderItem.dataset.id = reminder.id;
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'reminder-time';
                
                const timeIcon = document.createElement('i');
                timeIcon.className = 'material-icons';
                timeIcon.textContent = reminder.triggered ? 'notifications_active' : 'schedule';
                timeDiv.appendChild(timeIcon);
                
                const timeText = document.createElement('span');
                if (reminder.trigger_time) {
                    timeText.textContent = `Set to trigger at: ${reminder.trigger_time}`;
                } else {
                    timeText.textContent = `Set at: ${reminder.time}`;
                }
                timeDiv.appendChild(timeText);
                
                const messageDiv = document.createElement('div');
                messageDiv.className = 'reminder-message';
                messageDiv.textContent = reminder.message;
                
                const deleteButton = document.createElement('button');
                deleteButton.className = 'delete-reminder';
                deleteButton.innerHTML = '<i class="material-icons">close</i>';
                deleteButton.onclick = function() {
                    deleteReminder(reminder.id);
                };
                
                reminderItem.appendChild(timeDiv);
                reminderItem.appendChild(messageDiv);
                reminderItem.appendChild(deleteButton);
                
                remindersList.appendChild(reminderItem);
            });
        }
        
        // Delete a reminder
        function deleteReminder(id) {
            fetch('/delete_reminder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: id })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateRemindersList(data.reminders);
                    addMessageToChat('System', `Reminder deleted successfully`, 'assistant');
                }
            });
        }
        
        // Clear all reminders
        function clearAllReminders() {
            if (confirm('Are you sure you want to delete all reminders?')) {
                const reminderItems = document.querySelectorAll('.reminder-item');
                let promises = [];
                
                reminderItems.forEach(item => {
                    const id = item.dataset.id;
                    const promise = fetch('/delete_reminder', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ id: id })
                    });
                    promises.push(promise);
                });
                
                Promise.all(promises).then(() => {
                    fetch('/check_reminders')
                        .then(response => response.json())
                        .then(data => {
                            updateRemindersList(data.reminders);
                            addMessageToChat('System', 'All reminders cleared', 'assistant');
                        });
                });
            }
        }
        
        // Check for reminders periodically
        setInterval(() => {
            fetch('/check_reminders')
            .then(response => response.json())
            .then(data => {
                updateRemindersList(data.reminders);
                
                // Show triggered reminders in chat
                if (data.triggered && data.triggered.length > 0) {
                    data.triggered.forEach(reminder => {
                        addMessageToChat('REMINDER', reminder.message, 'reminder');
                        // Show browser notification
                        if (Notification.permission === "granted") {
                            new Notification("Reminder", { body: reminder.message });
                        }
                    });
                }
            });
        }, 1000);
        
        // Request notification permission
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }
        
        // Initial load of reminders
        fetch('/check_reminders')
            .then(response => response.json())
            .then(data => {
                updateRemindersList(data.reminders);
            });
        
        function setQuickReminder() {
            const timeInput = document.getElementById('reminder-time');
            const messageInput = document.getElementById('reminder-message');
            
            if (!timeInput.value || !messageInput.value) {
                alert('Please enter both time and message for the reminder');
                return;
            }
            
            // Convert 24h time to 12h format with am/pm
            const timeValue = timeInput.value;
            const [hours, minutes] = timeValue.split(':');
            const hour = parseInt(hours);
            const ampm = hour >= 12 ? 'pm' : 'am';
            const hour12 = hour % 12 || 12;
            const time12 = `${hour12}:${minutes} ${ampm}`;
            
            const command = `Remind me at ${time12} to ${messageInput.value}`;
            quickCommand(command);
            
            // Clear inputs
            messageInput.value = '';
        }
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("Web-based Virtual Assistant is starting...")
    print("Open your browser and go to http://127.0.0.1:5000")
    app.run(debug=True) 