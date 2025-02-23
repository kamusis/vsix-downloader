import sys
import datetime
import inspect
import os
import threading
from pathlib import Path
from typing import Any, Optional, Dict, TextIO, List, Union
from enum import Enum
from abc import ABC, abstractmethod
import json

# ANSI color codes for different log levels
class Colors:
    """ANSI color codes for console output"""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

class LogLevel(Enum):
    """Log levels enum"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class BaseLogger(ABC):
    """
    Abstract base class for all loggers.
    Defines the interface that all logger implementations must follow.
    """
    
    @abstractmethod
    def debug(self, message: Any, timestamp: bool = True) -> None:
        """Log a debug message"""
        pass
        
    @abstractmethod
    def info(self, message: Any, timestamp: bool = True) -> None:
        """Log an info message"""
        pass
        
    @abstractmethod
    def warning(self, message: Any, timestamp: bool = True) -> None:
        """Log a warning message"""
        pass
        
    @abstractmethod
    def error(self, message: Any, timestamp: bool = True) -> None:
        """Log an error message"""
        pass
        
    @abstractmethod
    def critical(self, message: Any, timestamp: bool = True) -> None:
        """Log a critical message"""
        pass
    
    def _format_message(self, level: LogLevel, message: Any, timestamp: bool = True) -> str:
        """
        Format a log message with optional timestamp.
        
        Args:
            level: The log level
            message: The message to log
            timestamp: Whether to include a timestamp
            
        Returns:
            str: The formatted message
        """
        if timestamp:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{level.name} {current_time}] {message}"
        return f"[{level.name}] {message}"

    def _get_caller_info(self) -> Dict[str, str]:
        """
        Get information about the caller of the log method.
        
        Returns:
            Dict containing 'function' and 'line' information
        """
        caller_frame = inspect.currentframe().f_back.f_back  # Skip _get_caller_info and log method frames
        return {
            'function': caller_frame.f_code.co_name,
            'line': str(caller_frame.f_lineno)
        }

class DebugLogger(BaseLogger):
    """
    A simple debug logger that can be enabled/disabled via command line arguments.
    Usage:
        logger = DebugLogger()
        logger.debug("Some debug message")  # Only prints if --debug flag is present
    """
    
    def __init__(self, debug_flag: str = "--debug"):
        """
        Initialize the debug logger.
        
        Args:
            debug_flag (str): The command line flag to check for debug mode
        """
        self.enabled = debug_flag in sys.argv
    
    def debug(self, message: Any, timestamp: bool = True) -> None:
        """
        Log a debug message if debug mode is enabled.
        
        Args:
            message: The message to log (can be any type that can be converted to string)
            timestamp: Whether to include a timestamp in the log message
        """
        if not self.enabled:
            return
        print(self._format_message(LogLevel.DEBUG, message, timestamp))
    
    def info(self, message: Any, timestamp: bool = True) -> None:
        """Not implemented for DebugLogger"""
        pass
        
    def warning(self, message: Any, timestamp: bool = True) -> None:
        """Not implemented for DebugLogger"""
        pass
        
    def error(self, message: Any, timestamp: bool = True) -> None:
        """Not implemented for DebugLogger"""
        pass
        
    def critical(self, message: Any, timestamp: bool = True) -> None:
        """Not implemented for DebugLogger"""
        pass
            
    def is_debug_enabled(self) -> bool:
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode is enabled, False otherwise
        """
        return self.enabled

class ConsoleLogger(BaseLogger):
    """
    A logger that outputs colored messages to the console.
    """
    
    def __init__(self, show_caller_info: bool = True, colors: Optional[Dict[str, str]] = None):
        """
        Initialize console logger.
        
        Args:
            show_caller_info: Whether to show caller info in log messages
            colors: Optional color mapping for log levels. Keys should be level names (debug, info, etc.)
                   and values should be color names (cyan, green, etc.)
        """
        self.show_caller_info = show_caller_info
        
        # Convert color names to ANSI codes
        self.color_map = {}
        if colors:
            color_name_to_code = {
                'black': Colors.BLACK,
                'red': Colors.RED,
                'green': Colors.GREEN,
                'yellow': Colors.YELLOW,
                'blue': Colors.BLUE,
                'magenta': Colors.MAGENTA,
                'cyan': Colors.CYAN,
                'white': Colors.WHITE
            }
            
            for level_name, color_name in colors.items():
                try:
                    level = LogLevel[level_name.upper()]
                    if color_name.lower() in color_name_to_code:
                        self.color_map[level] = color_name_to_code[color_name.lower()]
                except (KeyError, AttributeError):
                    print(f"Invalid level or color: {level_name}={color_name}")
        
        # Use default colors for any missing levels
        default_colors = {
            LogLevel.DEBUG: Colors.CYAN,
            LogLevel.INFO: Colors.GREEN,
            LogLevel.WARNING: Colors.YELLOW,
            LogLevel.ERROR: Colors.RED,
            LogLevel.CRITICAL: Colors.MAGENTA
        }
        
        for level, color in default_colors.items():
            if level not in self.color_map:
                self.color_map[level] = color
    
    def _log(self, level: LogLevel, message: Any, timestamp: bool = True) -> None:
        """
        Internal method to handle logging with colors and caller info.
        
        Args:
            level: The log level
            message: The message to log
            timestamp: Whether to include a timestamp
        """
        base_message = self._format_message(level, message, timestamp)
        
        if self.show_caller_info:
            caller_info = self._get_caller_info()
            base_message = f"{base_message} (in {caller_info['function']}:{caller_info['line']})"
        
        color = self.color_map.get(level, "")
        print(f"{color}{base_message}{Colors.RESET}")
    
    def debug(self, message: Any, timestamp: bool = True) -> None:
        """Log a debug message in cyan"""
        self._log(LogLevel.DEBUG, message, timestamp)
    
    def info(self, message: Any, timestamp: bool = True) -> None:
        """Log an info message in green"""
        self._log(LogLevel.INFO, message, timestamp)
    
    def warning(self, message: Any, timestamp: bool = True) -> None:
        """Log a warning message in yellow"""
        self._log(LogLevel.WARNING, message, timestamp)
    
    def error(self, message: Any, timestamp: bool = True) -> None:
        """Log an error message in red"""
        self._log(LogLevel.ERROR, message, timestamp)
    
    def critical(self, message: Any, timestamp: bool = True) -> None:
        """Log a critical message in magenta"""
        self._log(LogLevel.CRITICAL, message, timestamp)

class CompositeLogger(BaseLogger):
    """
    A logger that combines multiple loggers and forwards messages to all of them.
    
    Usage:
        console_logger = ConsoleLogger()
        file_logger = FileLogger("app.log")
        logger = CompositeLogger([console_logger, file_logger])
        logger.info("This message goes to both console and file")
    """
    
    def __init__(self, loggers: List[BaseLogger] = None):
        """
        Initialize the composite logger.
        
        Args:
            loggers: List of logger instances to use. Each must inherit from BaseLogger.
        """
        self.loggers = loggers or []
        self.lock = threading.Lock()
    
    def add_logger(self, logger: BaseLogger) -> None:
        """
        Add a new logger to the composite.
        
        Args:
            logger: Logger instance to add
        
        Raises:
            TypeError: If logger doesn't inherit from BaseLogger
        """
        if not isinstance(logger, BaseLogger):
            raise TypeError("Logger must inherit from BaseLogger")
        with self.lock:
            self.loggers.append(logger)
    
    def remove_logger(self, logger: BaseLogger) -> None:
        """
        Remove a logger from the composite.
        
        Args:
            logger: Logger instance to remove
        """
        with self.lock:
            if logger in self.loggers:
                self.loggers.remove(logger)
    
    def _log_to_all(self, level: LogLevel, message: Any, timestamp: bool = True) -> None:
        """
        Send a log message to all registered loggers.
        
        Args:
            level: Log level to use
            message: Message to log
            timestamp: Whether to include timestamp
        """
        with self.lock:
            loggers = self.loggers.copy()  # Copy to avoid modification during iteration
        
        failed_loggers = []
        for logger in loggers:
            try:
                if level == LogLevel.DEBUG:
                    logger.debug(message, timestamp)
                elif level == LogLevel.INFO:
                    logger.info(message, timestamp)
                elif level == LogLevel.WARNING:
                    logger.warning(message, timestamp)
                elif level == LogLevel.ERROR:
                    logger.error(message, timestamp)
                elif level == LogLevel.CRITICAL:
                    logger.critical(message, timestamp)
            except Exception as e:
                failed_loggers.append((logger, str(e)))
        
        # Handle any failed loggers
        if failed_loggers:
            print("Warning: Some loggers failed:")
            for logger, error in failed_loggers:
                print(f"- {type(logger).__name__}: {error}")
                self.remove_logger(logger)  # Remove failed logger to prevent future errors
    
    def debug(self, message: Any, timestamp: bool = True) -> None:
        """Log a debug message to all loggers"""
        self._log_to_all(LogLevel.DEBUG, message, timestamp)
    
    def info(self, message: Any, timestamp: bool = True) -> None:
        """Log an info message to all loggers"""
        self._log_to_all(LogLevel.INFO, message, timestamp)
    
    def warning(self, message: Any, timestamp: bool = True) -> None:
        """Log a warning message to all loggers"""
        self._log_to_all(LogLevel.WARNING, message, timestamp)
    
    def error(self, message: Any, timestamp: bool = True) -> None:
        """Log an error message to all loggers"""
        self._log_to_all(LogLevel.ERROR, message, timestamp)
    
    def critical(self, message: Any, timestamp: bool = True) -> None:
        """Log a critical message to all loggers"""
        self._log_to_all(LogLevel.CRITICAL, message, timestamp)

class FileLogger(BaseLogger):
    """
    A file logger that creates new timestamp-based log files when size limit is reached.
    
    Example file names:
        app.20250222221500.log  # February 22, 2025 22:15:00
        app.20250222221545.log  # February 22, 2025 22:15:45
    """
    
    def __init__(self, 
                 filepath: str, 
                 max_size_bytes: int = 1024 * 1024,  # 1MB default
                 backup_count: int = 3,
                 encoding: str = 'utf-8'):
        """
        Initialize the file logger.
        
        Args:
            filepath: Path to the log file (base name pattern)
            max_size_bytes: Maximum size of each log file
            backup_count: Number of backup files to keep
            encoding: File encoding
        """
        self.base_filepath = Path(filepath)
        self.max_size_bytes = max_size_bytes
        self.backup_count = backup_count
        self.encoding = encoding
        
        self.lock = threading.Lock()
        self._create_log_directory()
        self.current_filepath = self._get_timestamped_filepath()
        self.file: Optional[TextIO] = None
        self._open_file()
    
    def _create_log_directory(self) -> None:
        """Create the directory for log files if it doesn't exist"""
        self.base_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_timestamped_filepath(self) -> Path:
        """Generate a timestamp-based filename"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return self.base_filepath.parent / f"{self.base_filepath.stem}.{timestamp}{self.base_filepath.suffix}"
    
    def _open_file(self) -> None:
        """Open a new log file"""
        if self.file is not None:
            try:
                self.file.close()
            except Exception:
                pass
            self.file = None
        
        try:
            self.file = open(self.current_filepath, 'w', encoding=self.encoding)
        except Exception as e:
            print(f"Error opening log file {self.current_filepath}: {e}")
            self.file = None
    
    def _cleanup_old_logs(self) -> None:
        """Remove old log files exceeding backup_count"""
        try:
            pattern = f"{self.base_filepath.stem}.*{self.base_filepath.suffix}"
            log_files = sorted(
                self.base_filepath.parent.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep only backup_count files
            for old_log in log_files[self.backup_count:]:
                try:
                    old_log.unlink()
                except Exception as e:
                    print(f"Error removing old log {old_log}: {e}")
        except Exception as e:
            print(f"Error during log cleanup: {e}")
    
    def _check_rotation(self) -> bool:
        """Check if we need to rotate to a new file"""
        try:
            if self.file is None:
                return True
            
            self.file.flush()
            return (self.current_filepath.exists() and 
                   self.current_filepath.stat().st_size >= self.max_size_bytes)
        except Exception:
            return True
    
    def _rotate_if_needed(self) -> None:
        """Create a new log file if needed"""
        if not self._check_rotation():
            return
            
        try:
            # Close current file
            if self.file is not None:
                self.file.close()
                self.file = None
            
            # Create new file with timestamp
            self.current_filepath = self._get_timestamped_filepath()
            self._open_file()
            
            # Cleanup old files
            self._cleanup_old_logs()
        except Exception as e:
            print(f"Error rotating log file: {e}")
    
    def _write_message(self, message: str) -> None:
        """Write a single message to the log file"""
        with self.lock:
            try:
                self._rotate_if_needed()
                if self.file is not None:
                    self.file.write(message + "\n")
                    self.file.flush()
            except Exception as e:
                print(f"Error writing to log file: {e}")
                # Try to recover by creating a new file
                self._rotate_if_needed()
    
    def _log(self, level: LogLevel, message: Any, timestamp: bool = True) -> None:
        """Log a message to the file"""
        formatted_message = self._format_message(level, message, timestamp)
        self._write_message(formatted_message)
    
    def debug(self, message: Any, timestamp: bool = True) -> None:
        """Log a debug message to file"""
        self._log(LogLevel.DEBUG, message, timestamp)
    
    def info(self, message: Any, timestamp: bool = True) -> None:
        """Log an info message to file"""
        self._log(LogLevel.INFO, message, timestamp)
    
    def warning(self, message: Any, timestamp: bool = True) -> None:
        """Log a warning message to file"""
        self._log(LogLevel.WARNING, message, timestamp)
    
    def error(self, message: Any, timestamp: bool = True) -> None:
        """Log an error message to file"""
        self._log(LogLevel.ERROR, message, timestamp)
    
    def critical(self, message: Any, timestamp: bool = True) -> None:
        """Log a critical message to file"""
        self._log(LogLevel.CRITICAL, message, timestamp)
    
    def __del__(self) -> None:
        """Close the file when the logger is destroyed"""
        try:
            if self.file is not None:
                self.file.close()
        except Exception:
            pass

class LoggingConfig:
    """
    Manages logging configuration and logger creation.
    
    Usage:
        config = LoggingConfig()
        logger = config.get_logger()  # Get default composite logger
        logger = config.get_logger('file')  # Get specific logger
    """
    
    DEFAULT_CONFIG = {
        "version": "1.0",
        "global": {
            "timestamp": True,
            "encoding": "utf-8"
        },
        "loggers": {
            "console": {
                "type": "console",
                "enabled": True,
                "show_caller_info": True,
                "colors": {
                    "debug": "cyan",
                    "info": "green",
                    "warning": "yellow",
                    "error": "red",
                    "critical": "magenta"
                }
            },
            "file": {
                "type": "file",
                "enabled": True,
                "filepath": "logs/app.log",
                "max_size_bytes": 1048576,  # 1MB
                "backup_count": 5
            },
            "debug": {
                "type": "debug",
                "enabled": False  # Only enabled with --debug flag
            }
        },
        "default_logger": {
            "type": "composite",
            "loggers": ["console", "file"]
        }
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize logging configuration.
        
        Args:
            config_path: Path to JSON configuration file. If None, uses default config.
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config()
        self._loggers: Dict[str, BaseLogger] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file or use default"""
        if not self.config_path:
            return self.DEFAULT_CONFIG.copy()
            
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults for missing values
                return self._merge_configs(self.DEFAULT_CONFIG.copy(), config)
            else:
                print(f"Config file {self.config_path} not found, using defaults")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config from {self.config_path}: {e}")
            print("Using default configuration")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge custom config with defaults"""
        for key, value in custom.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def save_config(self, path: Optional[Union[str, Path]] = None) -> bool:
        """
        Save current configuration to a JSON file.
        
        Args:
            path: Path to save to. If None, uses the path from initialization.
        
        Returns:
            True if save was successful, False otherwise
        """
        save_path = Path(path) if path else self.config_path
        if not save_path:
            print("No save path specified")
            return False
            
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")
            return False
    
    def _create_console_logger(self, config: Dict[str, Any]) -> ConsoleLogger:
        """Create a ConsoleLogger from configuration"""
        return ConsoleLogger(
            show_caller_info=config.get('show_caller_info', True),
            colors=config.get('colors', {})
        )
    
    def _create_file_logger(self, config: Dict[str, Any]) -> FileLogger:
        """Create a FileLogger from configuration"""
        # Ensure logs directory exists
        filepath = Path(config['filepath'])
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        return FileLogger(
            filepath=str(filepath),
            max_size_bytes=config.get('max_size_bytes', 1024 * 1024),
            backup_count=config.get('backup_count', 3),
            encoding=self.config.get('global', {}).get('encoding', 'utf-8')
        )
    
    def _create_debug_logger(self, config: Dict[str, Any]) -> DebugLogger:
        """Create a DebugLogger from configuration"""
        return DebugLogger()
    
    def _create_composite_logger(self, config: Dict[str, Any]) -> CompositeLogger:
        """Create a CompositeLogger from configuration"""
        logger_names = config.get('loggers', [])
        loggers = []
        
        for name in logger_names:
            logger = self.get_logger(name)
            if logger:
                loggers.append(logger)
        
        return CompositeLogger(loggers)
    
    def get_logger(self, name: str = 'default_logger') -> Optional[BaseLogger]:
        """
        Get a logger by name. Returns None if logger is not found or disabled.
        
        Args:
            name: Name of the logger to get. Uses 'default_logger' if not specified.
        
        Returns:
            Logger instance or None if not found/disabled
        """
        # Return cached logger if available
        if name in self._loggers:
            return self._loggers[name]
        
        # Get logger config
        logger_config = self.config.get('loggers', {}).get(name)
        if name == 'default_logger':
            logger_config = self.config.get('default_logger')
        
        if not logger_config:
            print(f"Logger '{name}' not found in configuration")
            return None
        
        # Skip disabled loggers
        if not logger_config.get('enabled', True):
            if logger_config['type'] == 'debug' and '--debug' in sys.argv:
                pass  # Allow debug logger if --debug flag is present
            else:
                return None
        
        # Create logger based on type
        logger_type = logger_config['type']
        try:
            if logger_type == 'console':
                logger = self._create_console_logger(logger_config)
            elif logger_type == 'file':
                logger = self._create_file_logger(logger_config)
            elif logger_type == 'debug':
                logger = self._create_debug_logger(logger_config)
            elif logger_type == 'composite':
                logger = self._create_composite_logger(logger_config)
            else:
                print(f"Unknown logger type: {logger_type}")
                return None
            
            # Cache and return logger
            self._loggers[name] = logger
            return logger
            
        except Exception as e:
            print(f"Error creating logger '{name}': {e}")
            return None
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.config = self._load_config()
        self._loggers.clear()  # Clear cached loggers

# Example usage
if __name__ == "__main__":
    # Create a logger instance
    config = LoggingConfig()
    logger = config.get_logger()
    
    # Example debug messages
    logger.debug("Starting application...")
    logger.debug("Configuration loaded", timestamp=True)
    
    # Example of some application logic
    x = 42
    logger.debug(f"The value of x is: {x}")
    
    # Example of checking debug status
    if logger is not None:
        print("Logger is enabled!")
    else:
        print("Logger is disabled. Run with --debug to see debug messages.")
