# BEGIN stonecutter extension
try:
    import sys
    import os
    # Add parent directory to path to find stonecutter.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from stonecutter import run_signal_engine as run_signal
except ImportError:
    # Fallback to existing implementation
    def run_signal(*args, **kwargs):
        raise ImportError("run_signal_engine not found, please check implementation")
# END stonecutter extension