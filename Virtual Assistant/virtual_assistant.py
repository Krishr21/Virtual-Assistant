import datetime
from reminder_manager import ReminderManager
from nlp_processor import NLPProcessor

class VirtualAssistant:
    def __init__(self):
        self.reminder_manager = ReminderManager()
        self.nlp = NLPProcessor()
        self.commands = {
            'set reminder': self.handle_reminder,
            'help': self.show_help,
            'time': self.get_time
        }

    def process_query(self, query):
        query = query.lower().strip()
        
        # Process with NLP
        nlp_result = self.nlp.process(query)
        intent = nlp_result['intent']
        
        # Handle calculations
        if intent == 'calculation':
            return nlp_result['response']
        
        # Handle general queries
        if intent == 'general_query' and 'response' in nlp_result:
            return nlp_result['response']
        
        # Handle simple intents with direct responses
        if intent in ['greeting', 'farewell', 'gratitude', 'joke']:
            return self.nlp.get_response(intent)
        
        # Handle more complex intents
        entities = nlp_result.get('entities', {})
        if intent == 'set_reminder' and 'time' in entities and 'message' in entities:
            return self.reminder_manager.set_reminder(entities['time'], entities['message'])
        elif intent == 'check_time':
            return self.get_time(query)
        elif intent == 'help':
            return self.show_help(query)
        elif intent == 'weather' and 'location' in entities:
            return f"I would show you the weather for {entities['location']}, but I don't have weather data access yet."
        
        # Fall back to command-based processing if NLP didn't work well
        for command, handler in self.commands.items():
            if command in query:
                return handler(query)
        
        return "I'm sorry, I don't understand that query. You can ask me about various topics, perform calculations, or set reminders. Type 'help' for more information."

    def handle_reminder(self, query):
        # Expected format: "set reminder for [time] to [message]"
        try:
            parts = query.split('for')[1].split('to')
            time_str = parts[0].strip()
            message = parts[1].strip()
            
            return self.reminder_manager.set_reminder(time_str, message)
        except:
            return "Please use the format: set reminder for [time] to [message]"

    def show_help(self, query):
        return """I can help you with:
        - Setting reminders (e.g., "remind me at 3:30 pm to take a break")
        - Checking the time (e.g., "what time is it?")
        - Telling jokes (e.g., "tell me a joke")
        - Basic calculations (e.g., "calculate 5 + 3")
        - Answering questions about various topics (e.g., "what is artificial intelligence?")
        - Basic conversation (greetings, farewells, etc.)
        
        Just type your question or request in natural language, and I'll do my best to help!"""

    def get_time(self, query):
        return f"Current time is: {datetime.datetime.now().strftime('%I:%M %p')}"

if __name__ == "__main__":
    assistant = VirtualAssistant()
    print("Virtual Assistant is ready! Type 'help' for available commands.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = assistant.process_query(user_input)
        print("Assistant:", response) 