class EventType:
    """Tên các sự kiện solver phát ra cho UI (xem EVENTS.md)."""
    INIT = "INIT"                    # bắt đầu giải
    DOMAIN_UPDATE = "DOMAIN_UPDATE"  # miền của một ô bị thu hẹp (lan truyền ràng buộc)
    ASSIGN = "ASSIGN"                # thử gán giá trị cho một ô
    BACKTRACK = "BACKTRACK"          # hoàn tác một phép gán
    SOLVED = "SOLVED"                # tìm được nghiệm
    FAILED = "FAILED"                # không có nghiệm hoặc chạm giới hạn


class EventEmitter:
    """Bus sự kiện đơn giản: solver gọi notify, UI đăng ký listener bằng subscribe.

    Listener có chữ ký listener(event_type, data), trong đó data là dict.
    """
    def __init__(self):
        self.listeners = []

    def subscribe(self, listener):
        self.listeners.append(listener)

    def unsubscribe(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def notify(self, event_type, data=None):
        payload = data if data is not None else {}
        for listener in list(self.listeners):
            listener(event_type, payload)


event_bus = EventEmitter()
