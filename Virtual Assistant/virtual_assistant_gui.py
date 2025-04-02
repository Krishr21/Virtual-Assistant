import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import queue
from virtual_assistant import VirtualAssistant

class VirtualAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Assistant")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set color scheme
        self.bg_color = "#f0f0f0"
        self.text_bg = "#ffffff"
        self.accent_color = "#4a7abc"
        self.root.configure(bg=self.bg_color)
        
        # Initialize the virtual assistant
        self.assistant = VirtualAssistant()
        
        # Create a queue for reminder notifications
        self.notification_queue = queue.Queue()
        
        # Override the reminder manager's _remind method
        self.assistant.reminder_manager._original_remind = self.assistant.reminder_manager._remind
        self.assistant.reminder_manager._remind = self._gui_remind
        
        self._create_widgets()
        
        # Start checking for notifications
        self._check_notifications()

    def _create_widgets(self):
        # Create main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat history display
        history_frame = tk.LabelFrame(main_frame, text="Conversation", bg=self.bg_color)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD, 
            bg=self.text_bg,
            font=("Arial", 10)
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_history.config(state=tk.DISABLED)
        
        # Input area
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.user_input = tk.Entry(
            input_frame, 
            bg=self.text_bg,
            font=("Arial", 10)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self._on_send)
        self.user_input.focus_set()
        
        send_button = tk.Button(
            input_frame, 
            text="Send", 
            command=self._on_send,
            bg=self.accent_color,
            fg="white",
            activebackground="#3a5a8c",
            activeforeground="white"
        )
        send_button.pack(side=tk.RIGHT)
        
        # Quick commands
        commands_frame = tk.LabelFrame(main_frame, text="Quick Commands", bg=self.bg_color)
        commands_frame.pack(fill=tk.X, padx=5, pady=5)
        
        commands = [
            "Set reminder for 5:00 pm to take a break",
            "What time is it?",
            "Help"
        ]
        
        for cmd in commands:
            cmd_button = tk.Button(
                commands_frame,
                text=cmd,
                command=lambda c=cmd: self._quick_command(c),
                bg=self.text_bg,
                relief=tk.GROOVE
            )
            cmd_button.pack(fill=tk.X, padx=5, pady=2)
        
        # Welcome message
        self._add_to_chat("Assistant", "Virtual Assistant is ready! Type 'help' for available commands.")

    def _on_send(self, event=None):
        query = self.user_input.get().strip()
        if not query:
            return
        
        self._add_to_chat("You", query)
        self.user_input.delete(0, tk.END)
        
        # Process in a separate thread to keep UI responsive
        threading.Thread(target=self._process_query, args=(query,), daemon=True).start()
    
    def _process_query(self, query):
        if query.lower() == 'exit':
            if messagebox.askyesno("Exit", "Do you want to exit the application?"):
                self.root.quit()
            return
        
        response = self.assistant.process_query(query)
        self._add_to_chat("Assistant", response)
    
    def _add_to_chat(self, sender, message):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, f"{sender}: ", "sender")
        self.chat_history.insert(tk.END, f"{message}\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.tag_configure("sender", font=("Arial", 10, "bold"))
    
    def _quick_command(self, command):
        self._add_to_chat("You", command)
        threading.Thread(target=self._process_query, args=(command,), daemon=True).start()
    
    def _gui_remind(self, delay, message):
        # Call the original method to maintain functionality
        self.assistant.reminder_manager._original_remind(delay, message)
        # Add to notification queue for GUI display
        self.notification_queue.put(message)
    
    def _check_notifications(self):
        try:
            while True:
                message = self.notification_queue.get_nowait()
                self._show_notification(message)
        except queue.Empty:
            pass
        finally:
            # Check again after 1 second
            self.root.after(1000, self._check_notifications)
    
    def _show_notification(self, message):
        # Add to chat history
        self._add_to_chat("REMINDER", message)
        # Show popup
        messagebox.showinfo("Reminder", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualAssistantGUI(root)
    root.mainloop() 