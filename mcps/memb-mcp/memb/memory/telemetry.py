# Telemetry module stub for memB (Privacy Hardened)
# All external telemetry tracking has been completely disabled and removed.

MEMB_TELEMETRY = False

class AnonymousTelemetry:
    def __init__(self, vector_store=None, before_send=None):
        self.posthog = None
        self.user_id = None

    def capture_event(self, event_name, properties=None, user_email=None, flags=None):
        pass

    def capture_identify(self, anon_id, email):
        return False

    def close(self):
        pass

client_telemetry = AnonymousTelemetry()

def capture_event(event_name, memory_instance, additional_data=None):
    pass

def capture_client_event(event_name, instance, additional_data=None):
    pass
