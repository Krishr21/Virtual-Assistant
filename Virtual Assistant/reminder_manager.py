import datetime
import threading
import time

class ReminderManager:
    def __init__(self):
        self.reminders = []

    def set_reminder(self, time_str, message):
        try:
            # Support multiple time formats
            try:
                # Try parsing "3:30 pm" format
                reminder_time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
            except ValueError:
                try:
                    # Try parsing "15:30" format
                    reminder_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                except ValueError:
                    # Try parsing "3:30pm" format (no space)
                    reminder_time = datetime.datetime.strptime(time_str, "%I:%M%p").time()
            
            current_time = datetime.datetime.now().time()
            
            # Calculate delay in seconds
            reminder_datetime = datetime.datetime.combine(datetime.date.today(), reminder_time)
            current_datetime = datetime.datetime.combine(datetime.date.today(), current_time)
            
            if reminder_datetime <= current_datetime:
                reminder_datetime += datetime.timedelta(days=1)
            
            delay = (reminder_datetime - current_datetime).total_seconds()
            
            # Create a thread for the reminder
            thread = threading.Thread(target=self._remind, args=(delay, message))
            thread.daemon = True
            thread.start()
            
            return f"Reminder set for {reminder_time.strftime('%I:%M %p')}: {message}"
        except ValueError as e:
            return f"Invalid time format. Please use format like '2:30 pm' or '14:30'. Error: {str(e)}"

    def _remind(self, delay, message):
        time.sleep(delay)
        print("\nREMINDER:", message)
        # The GUI will override this method to add its own notification handling

    def _remind(self, delay, message):
        time.sleep(delay)
        print("\nREMINDER:", message) 