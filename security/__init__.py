"""Security module for NPC Race — static analysis and runtime sandboxing."""

__all__: list[str] = []

try:
    from .bot_scanner import scan_car_file, scan_car_source, ScanResult

    __all__ += ["scan_car_file", "scan_car_source", "ScanResult"]
except ImportError:
    pass

try:
    from .sandbox import safe_strategy_call

    __all__ += ["safe_strategy_call"]
except ImportError:
    pass
