"""
Google Antigravity: Internal Agent Base
=======================================

Standardized base class for all agents (Watson, Sherlock, Moriarty, etc.)
to ensure architectural compliance with the "Interrogative Framework".

Enforces:
1. Event-Driven Communication (via EventBus)
2. Logical Timekeeping (via LamportClock)
3. Structured Logging
"""

import json
import argparse
from typing import Dict, Any, Optional

try:
    from architectural_core import global_bus, global_clock, EventType
except ImportError:
    from agents.architectural_core import global_bus, global_clock, EventType

class InternalAgentBase:
    """
    Base class for all internal agents.
    """
    
    def __init__(self, agent_name: str, session_id: Optional[str] = None):
        self.agent_name = agent_name
        self.session_id = session_id
        
        # Subscribe to relevant events (optional, agents can override)
        # self._setup_subscriptions()
        
        self.publish_event(EventType.SYSTEM, {"msg": f"{agent_name} initialized"})

    def publish_event(self, event_type: EventType, payload: Dict[str, Any]):
        """
        Publish an event to the global bus.
        This handles the logical clock tick and audit logging automatically.
        """
        global_bus.publish(
            event_type=event_type.value,
            source=self.agent_name,
            payload=payload,
            correlation_id=self.session_id
        )

    def log(self, message: str, level: str = "INFO"):
        """
        Structured logging via the Event Bus.
        Replaces print() calls for critical info.
        """
        # Publish to the audit log/event bus
        self.publish_event(EventType.SYSTEM, {
            "level": level,
            "message": message
        })
        
        # Print to stdout for orchestrator streaming (Thinking UI)
        # Using flush=True ensures the pipe buffer is cleared immediately
        print(f"[{self.agent_name}] {message}", flush=True) 

    def update_clock(self, remote_timestamp: int):
        """
        Update local logical clock based on external input.
        """
        global_clock.update(remote_timestamp)

    def parse_common_args(self):
        """
        Standard argument parsing for all agents.
        """
        parser = argparse.ArgumentParser(description=f"{self.agent_name} Agent")
        parser.add_argument("--action", required=True, help="Action to perform")
        parser.add_argument("--input", required=True, help="Input file or data")
        parser.add_argument("--output", help="Output file")
        parser.add_argument("--session-id", help="Correlation ID for the session")
        parser.add_argument("--context", help="Path to context/research file")
        return parser.parse_args()
