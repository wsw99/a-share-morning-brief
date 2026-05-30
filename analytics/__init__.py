from .technical import run_technical_analysis
from .margin_analyzer import run_margin_analysis
from .futures_analyzer import run_futures_analysis
from .etf_analyzer import run_etf_analysis


def run_analytics(raw_data: dict) -> dict:
    return {
        "technical": run_technical_analysis(raw_data["index"]),
        "margin": run_margin_analysis(raw_data["margin"]),
        "futures": run_futures_analysis(raw_data["futures"], raw_data["index"]),
        "etf": run_etf_analysis(raw_data["etf_flow"]),
    }
