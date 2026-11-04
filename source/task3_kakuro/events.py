class EventEmitter:
    def __init__(self):
        self.listeners = []

    def subscribe(self, listener):
        self.listeners.append(listener)

    def notify(self, event_type, data):
        for listener in self.listeners:
            listener(event_type, data)

event_bus = EventEmitter()