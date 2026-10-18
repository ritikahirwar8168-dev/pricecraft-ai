"""
PriceCraft AI - Sentry Agent Tracing & Telemetry Engine
Powered by Sentry (sentry-sdk)

Tracks end-to-end agent workflow spans, latency, token usage, tool invocations,
and error reporting. Provides a live telemetry log inspectable in the UI and Sentry dashboard.
"""

import os
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("pricecraft.sentry")

SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# In-memory execution trace buffer for UI inspection
AGENT_TRACES: List[Dict[str, Any]] = []

def init_sentry():
    """Initializes Sentry SDK with performance tracing."""
    if SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                environment=os.getenv("ENVIRONMENT", "production"),
                release="pricecraft-ai@1.0.0",
            )
            logger.info("Sentry agent tracing initialized successfully.")
        except Exception as e:
            logger.warning(f"Sentry initialization notice: {e}")

class AgentSpan:
    """Context manager for tracing agent steps with latency, status, and metadata."""
    def __init__(self, step_name: str, tool_name: str):
        self.step_name = step_name
        self.tool_name = tool_name
        self.start_time = 0.0
        self.duration_ms = 0.0
        self.status = "running"
        self.metadata = {}

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = round((time.perf_counter() - self.start_time) * 1000, 2)
        self.status = "error" if exc_type else "ok"
        trace_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "step": self.step_name,
            "tool": self.tool_name,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.metadata,
        }
        AGENT_TRACES.insert(0, trace_record)
        if len(AGENT_TRACES) > 50:
            AGENT_TRACES.pop()

        if SENTRY_DSN:
            try:
                import sentry_sdk
                with sentry_sdk.configure_scope() as scope:
                    scope.set_extra(self.step_name, trace_record)
            except Exception:
                pass

def get_recent_traces() -> List[Dict[str, Any]]:
    """Returns recent agent execution spans for the UI telemetry monitor."""
    return AGENT_TRACES[:20]
