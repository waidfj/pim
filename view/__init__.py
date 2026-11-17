"""View package -- PIM system presentation layer.

The view layer is the *only* place in the system that knows how to render
PIRs, search results and error messages as text a human can read.  By
keeping every print / format decision in one module, the controller can
stay focused on parsing and dispatching commands, and the model can stay
purely about data and behaviour.
"""

from .formatter import Formatter
from .reporter import PrintReporter, Reporter

__all__ = ["Formatter", "Reporter", "PrintReporter"]
from .reporter import InMemoryReporter
