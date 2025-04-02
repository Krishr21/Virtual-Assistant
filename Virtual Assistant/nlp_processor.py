import re
import datetime
import random

class NLPProcessor:
    def __init__(self):
        # Define intents and their patterns
        self.intent_patterns = {
            'greeting': [
                r'hello', r'hi', r'hey', r'greetings', r'good morning', 
                r'good afternoon', r'good evening', r'howdy'
            ],
            'farewell': [
                r'bye', r'goodbye', r'see you', r'later', r'good night'
            ],
            'gratitude': [
                r'thank you', r'thanks', r'appreciate it', r'grateful'
            ],
            'set_reminder': [
                r'remind me', r'set reminder', r'set a reminder', 
                r'create reminder', r'make a reminder'
            ],
            'check_time': [
                r'what time', r'current time', r'time now', r'clock'
            ],
            'help': [
                r'help', r'assist', r'support', r'guide', r'how to'
            ],
            'weather': [
                r'weather', r'temperature', r'forecast', r'rain', r'sunny'
            ],
            'joke': [
                r'joke', r'funny', r'make me laugh', r'tell me a joke'
            ],
            'general_query': [
                r'what is', r'how to', r'who is', r'where is', r'when is',
                r'explain', r'tell me about', r'define', r'describe'
            ],
            'calculation': [
                r'calculate', r'compute', r'solve', r'evaluate',
                r'\d+\s*[\+\-\*\/]\s*\d+'  # Basic math operations
            ]
        }
        
        # Responses for simple intents
        self.responses = {
            'greeting': [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Hey! How can I assist you?"
            ],
            'farewell': [
                "Goodbye! Have a great day!",
                "See you later! Take care!",
                "Bye! Come back anytime you need assistance."
            ],
            'gratitude': [
                "You're welcome!",
                "Happy to help!",
                "Anytime! Is there anything else you need?"
            ],
            'help': [
                "I can help you with setting reminders, checking the time, telling jokes, and more. Just ask!"
            ],
            'joke': [
                "Why don't scientists trust atoms? Because they make up everything!",
                "What do you call a fake noodle? An impasta!",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "What's the best thing about Switzerland? I don't know, but the flag is a big plus."
            ]
        }
        
        # Entity extraction patterns
        self.time_pattern = r'(\d{1,2})(?::|\.)(\d{2})?\s*(am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)?'
        self.date_pattern = r'(today|tomorrow|next week|next month|on\s+\w+)'
        
        # Add knowledge base for common queries
        self.knowledge_base = {
            'python': "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            'javascript': "JavaScript is a programming language commonly used for web development.",
            'artificial intelligence': "AI is the simulation of human intelligence by machines.",
            'machine learning': "Machine learning is a subset of AI that enables systems to learn from data.",
            'blockchain': "Blockchain is a distributed ledger technology that enables secure, decentralized record-keeping.",
            'quantum computing': "Quantum computing uses quantum mechanics to perform complex calculations.",
            'virtual reality': "Virtual reality (VR) is a simulated experience that can be similar to or completely different from the real world.",
            'internet': "The Internet is a global network of connected computers.",
            'climate change': "Climate change refers to long-term shifts in global weather patterns and temperatures.",
            'renewable energy': "Renewable energy comes from naturally replenishing sources like sun, wind, and water."
        }
        
        # Add calculation functions
        self.math_operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else "Cannot divide by zero"
        }
        
    def process(self, text):
        """Process text and return intent, entities, and confidence"""
        text = text.lower()
        
        # First check if it's a calculation
        if self._is_calculation(text):
            return {
                'intent': 'calculation',
                'confidence': 1.0,
                'response': self._process_calculation(text)
            }
        
        # Then check for general queries
        query_terms = self._extract_query_terms(text)
        if query_terms:
            response = self._search_knowledge_base(query_terms)
            if response:
                return {
                    'intent': 'general_query',
                    'confidence': 0.8,
                    'response': response
                }
        
        # Fall back to existing intent detection
        intent, confidence = self._detect_intent(text)
        entities = {}
        
        if intent == 'set_reminder':
            entities = self._extract_reminder_entities(text)
        elif intent == 'weather':
            entities = self._extract_location(text)
            
        return {
            'intent': intent,
            'confidence': confidence,
            'entities': entities
        }
    
    def _detect_intent(self, text):
        """Detect the intent of the text"""
        max_confidence = 0
        detected_intent = 'unknown'
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(r'\b' + pattern + r'\b', text):
                    # Simple confidence calculation based on pattern match length
                    confidence = len(pattern) / len(text) if len(text) > 0 else 0
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_intent = intent
        
        return detected_intent, max_confidence
    
    def _extract_reminder_entities(self, text):
        """Extract time and message for reminders"""
        entities = {}
        
        # Extract time
        time_match = re.search(self.time_pattern, text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            # Normalize period to lowercase and remove dots
            if period:
                period = period.lower().replace('.', '')
            
                # If period is specified (am/pm), keep in 12-hour format
                if 'pm' in period and hour < 12:
                    hour += 12
                elif 'am' in period and hour == 12:
                    hour = 0
                
                # Format in 12-hour format
                if hour > 12:
                    hour -= 12
                entities['time'] = f"{hour}:{minute:02d} {period[:2]}"  # Only keep 'am' or 'pm'
            else:
                # If no period specified, convert 24-hour to 12-hour format
                if hour >= 12:
                    period = 'pm'
                    if hour > 12:
                        hour -= 12
                else:
                    period = 'am'
                    if hour == 0:
                        hour = 12
                entities['time'] = f"{hour}:{minute:02d} {period}"
            
        # Extract message (everything after "to" or "about")
        message_match = re.search(r'(?:to|about)\s+(.*?)(?:$|at\s+\d)', text)
        if message_match:
            entities['message'] = message_match.group(1).strip()
        
        return entities
    
    def _extract_location(self, text):
        """Extract location for weather queries"""
        entities = {}
        
        # Look for location patterns like "in [location]" or "for [location]"
        location_match = re.search(r'(?:in|for|at)\s+([a-zA-Z\s]+)(?:$|\?)', text)
        if location_match:
            entities['location'] = location_match.group(1).strip()
        
        return entities
    
    def get_response(self, intent):
        """Get a random response for simple intents"""
        if intent in self.responses:
            return random.choice(self.responses[intent])
        return None

    def _is_calculation(self, text):
        """Check if the text contains a mathematical expression"""
        return any(op in text for op in '+-*/')

    def _process_calculation(self, text):
        """Process basic mathematical calculations"""
        try:
            # Extract numbers and operator
            parts = re.findall(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)', text)
            if parts:
                num1 = float(parts[0][0])
                op = parts[0][1]
                num2 = float(parts[0][2])
                result = self.math_operators[op](num1, num2)
                return f"The result is {result}"
        except:
            return "Sorry, I couldn't process that calculation."
        return None

    def _extract_query_terms(self, text):
        """Extract key terms from the query"""
        # Remove common question words and stop words
        stop_words = {'what', 'is', 'are', 'how', 'to', 'the', 'a', 'an', 'in', 'on', 'at', 'for'}
        words = text.lower().split()
        query_terms = [w for w in words if w not in stop_words]
        return ' '.join(query_terms)

    def _search_knowledge_base(self, query):
        """Search the knowledge base for relevant information"""
        # Simple fuzzy matching
        best_match = None
        highest_score = 0
        
        for topic, info in self.knowledge_base.items():
            score = self._calculate_similarity(query, topic)
            if score > highest_score and score > 0.5:  # Threshold for relevance
                highest_score = score
                best_match = info
        
        return best_match

    def _calculate_similarity(self, query, topic):
        """Calculate simple similarity score between query and topic"""
        query_words = set(query.lower().split())
        topic_words = set(topic.lower().split())
        intersection = query_words.intersection(topic_words)
        return len(intersection) / max(len(query_words), len(topic_words)) 