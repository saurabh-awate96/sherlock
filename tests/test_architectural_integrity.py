import unittest
import os
import json
import threading
import time
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.architectural_core import (
    LamportClock, EventBus, Event, 
    CryptographicAuditLog, PerformanceGuard,
    EventType, global_clock
)

class TestArchitecturalIntegrity(unittest.TestCase):
    
    def setUp(self):
        self.test_log_file = "test_audit.log"
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
            
    def tearDown(self):
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_lamport_clock_integrity(self):
        """Pillar 1: Verify Temporal Integrity (Monotonicity)"""
        clock = LamportClock()
        t1 = clock.tick()
        t2 = clock.tick()
        self.assertTrue(t2 > t1, "Local clock must be strictly monotonic")
        
        # Simulate message receipt with higher timestamp
        t3 = clock.update(t2 + 10)
        self.assertTrue(t3 > t2 + 10, "Clock must jump ahead of received timestamp")
        
        # Concurrent access test
        def ticker():
            for _ in range(100):
                clock.tick()
        
        threads = [threading.Thread(target=ticker) for _ in range(5)]
        start_val = clock.current
        for t in threads: t.start()
        for t in threads: t.join()
        
        self.assertEqual(clock.current, start_val + 500, "Thread-safe increments failed")

    def test_event_bus_decoupling(self):
        """Pillar 2: Verify Structural Integrity (Decoupling)"""
        bus = EventBus()
        received_events = []
        
        def subscriber(event):
            received_events.append(event)
            
        bus.subscribe(EventType.OBSERVATION.value, subscriber)
        
        payload = {"data": "test"}
        bus.publish(EventType.OBSERVATION.value, "test_source", payload)
        
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].payload, payload)
        self.assertEqual(received_events[0].source, "test_source")
        self.assertTrue(received_events[0].logical_time > 0)

    def test_audit_log_immutability(self):
        """Pillar 3: Verify Security (Immutable Hash Chain)"""
        log = CryptographicAuditLog(self.test_log_file)
        bus = EventBus()
        bus.set_audit_log(log)
        
        # Generate some events
        bus.publish(EventType.SYSTEM.value, "test", {"msg": "event 1"})
        bus.publish(EventType.SYSTEM.value, "test", {"msg": "event 2"})
        
        # Verify file exists and has content
        with open(self.test_log_file, 'r') as f:
            lines = f.readlines()
            
        self.assertTrue(len(lines) >= 3) # Genesis + 2 events
        self.assertIn("GENESIS_HASH", lines[0])
        
        # Verify hash chain
        entry1 = json.loads(lines[1])
        entry2 = json.loads(lines[2])
        
        self.assertEqual(entry2['prev_hash'], entry1['cur_hash'], "Hash chain broken!")

    def test_performance_guard(self):
        """Pillar 4: Verify Performance Integrity (N+1 Detection)"""
        guard = PerformanceGuard()
        
        # Simulate N+1 problem
        for _ in range(105):
            guard.record_operation("db_query", "get_user")
            
        alerts = guard.check_thresholds()
        self.assertIn("db_query:get_user", alerts)

if __name__ == '__main__':
    unittest.main()
