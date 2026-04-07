import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter


class MASLogger:
    def __init__(self, meta_data, name="MAS", log_dir="logs", log_level=logging.INFO):
        self.json_dir = f"{log_dir}/json"
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

        # Initialize standard logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        if not self.logger.handlers:
            # Colored formatter for terminal
            color_formatter = ColoredFormatter(
                "%(log_color)s[%(asctime)s] [aciarena-%(levelname)s]%(reset)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    'DEBUG': 'bold_green',
                    'INFO': 'bold_cyan',
                    'WARNING': 'bold_yellow',
                    'ERROR': 'bold_red',
                    'CRITICAL': 'bold_red',
                },
                style='%'
            )

            # Terminal output (colored)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(color_formatter)
            self.logger.addHandler(console_handler)

            # File output (no color)
            file_path = os.path.join(log_dir, f"{name}.log")
            file_handler = RotatingFileHandler(file_path, maxBytes=5 * 1024 * 1024, backupCount=2)
            file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Structured log data
        self.logger.info(f"Evaluation Settings:\n{json.dumps(meta_data, indent=2)}")
        self.session = {
            "session_id": datetime.now().strftime("%Y%m%d-%H%M%S"),
            "meta_data": meta_data,
            "turns": [],
            "result": None
        }
        self.json_path = os.path.join(self.json_dir, f"{name}.json")

    def log_message(self, sender, receiver, message, tool=None):
        """
        Log an agent-to-agent message.

        :param sender: agent name who sends the message
        :param receiver: agent name who receives the message
        :param message: textual message content
        :param tool: tool name if invoked
        :param metadata: any additional dict data
        """
        self.logger.info(f"[{sender} → {receiver}] {message}")
        self.session["turns"].append({
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "tool": tool,
        })

    def log_result(self, result: dict):
        """Log and save the final result of the session."""
        self.logger.info(f"[RESULT] {result}")
        self.session["result"] = result
        self._save_json()

    def _save_json(self):
        """Persist the structured log as a JSON file."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.session, f, ensure_ascii=False, indent=2)
        self.logger.info(f"[LOG SAVED] log saved to {self.json_path}")
