from .complaints import router as complaints_router
from .analysis import router as analysis_router
from .stats import router as stats_router

__all__ = ["complaints_router", "analysis_router", "stats_router"]
