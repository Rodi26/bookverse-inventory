



import logging
import sys
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LogConfig(BaseModel):
    
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    include_request_id: bool = True
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    
    model_config = ConfigDict(env_prefix="LOG_")


def setup_logging(config: LogConfig = None, service_name: str = "bookverse") -> None:
    
    
    
    
    if config is None:
        config = LogConfig()
    
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    
    log_format = f"[{service_name}] {config.format}"
    formatter = logging.Formatter(log_format)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if config.log_to_file and config.log_file_path:
        try:
            file_handler = logging.FileHandler(config.log_file_path)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to set up file logging: {e}")
    
    logging.info(f"✅ Logging configured for {service_name} (level: {config.level})")


def get_logger(name: str) -> logging.Logger:
    
    
    
        
    return logging.getLogger(name)


def log_request_start(logger: logging.Logger, method: str, path: str, request_id: str = None):
    
    
    request_info = f"{method} {path}"
    if request_id:
        request_info += f" [ID: {request_id}]"
    
    logger.info(f"📥 Request started: {request_info}")


def log_request_end(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str = None
):
    
    
    request_info = f"{method} {path}"
    if request_id:
        request_info += f" [ID: {request_id}]"
    
    if status_code >= 500:
        emoji = "❌"
        log_level = logging.ERROR
    elif status_code >= 400:
        emoji = "⚠️"
        log_level = logging.WARNING
    else:
        emoji = "✅"
        log_level = logging.INFO
    
    logger.log(
        log_level,
        f"{emoji} Request completed: {request_info} - {status_code} ({duration_ms:.1f}ms)"
    )


def log_service_startup(logger: logging.Logger, service_name: str, version: str, port: int = None):
    
    
    startup_msg = f"🚀 {service_name} v{version} starting up"
    if port:
        startup_msg += f" on port {port}"
    
    logger.info(startup_msg)


def log_service_shutdown(logger: logging.Logger, service_name: str):
    
    
    logger.info(f"🛑 {service_name} shutting down")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str = None,
    request_id: str = None
):
    
    
    error_msg = f"❌ {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" (Context: {context})"
    
    if request_id:
        error_msg += f" [ID: {request_id}]"
    
    logger.error(error_msg, exc_info=True)


def log_demo_info(logger: logging.Logger, message: str):
    
    
    logger.info(f"🎯 DEMO: {message}")


def log_duplication_eliminated(logger: logging.Logger, component: str, lines_saved: int):
    
    
    logger.info(f"♻️ COMMONS: {component} - eliminated {lines_saved} lines of duplicate code")
