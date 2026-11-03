class EventEmitter:
    def __init__(self):
        self.listeners = []

    def subscribe(self, listener):
        self.listeners.append(listener)

    def notify(self, event_type, data):
        for listener in self.listeners:
            listener(event_type, data)

# Global event manager instance
event_bus = EventEmitter()