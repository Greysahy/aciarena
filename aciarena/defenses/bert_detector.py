from transformers import pipeline
from typing import Literal
import threading
import torch
import os


class BertDetector:
    """
    Bert-like detector used for detecting prompt injection attacks
    Directly integrates model loading and inference logic
    Uses process-level singleton with device locking to avoid multi-threading issues
    """
    
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    _device_lock = threading.Lock()  # Lock for device operations
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 model_name: str = "protectai/deberta-v3-base-prompt-injection-v2",
                 safe_label: str = "SAFE",
                 threshold: float = 0.5,
                 mode: Literal["message", "full_conversation"] = "message",
                 raise_on_injection: bool = False):
        """
        Initialize BERT detector
        
        Args:
            model_name: Model name for prompt injection detection
            safe_label: Label indicating a safe prompt
            threshold: Model prediction threshold, safety_score < threshold means prompt injection detected
            mode: Detector operation mode, 'message' or 'full_conversation'
            raise_on_injection: Whether to raise exception when prompt injection is detected
        """
        # Avoid repeated initialization
        if self._initialized:
            return
            
        self.model_name = model_name
        self.safe_label = safe_label
        self.threshold = threshold
        self.mode = mode
        self.raise_on_injection = raise_on_injection
        
        # Load model once at process level
        self._load_model()
        self._initialized = True
    
    def _load_model(self):
        """Load BERT model and create inference pipeline with device safety"""
        with self._device_lock:
            try:
                # Force CPU usage to avoid CUDA meta tensor issues
                device = torch.device("cpu")
                
                # Set environment variables to avoid meta tensor issues
                os.environ["TOKENIZERS_PARALLELISM"] = "false"
                
                # Create text classification pipeline with explicit device handling
                self.pipeline = pipeline(
                    "text-classification", 
                    model=self.model_name, 
                    device=device,
                    trust_remote_code=True,
                    model_kwargs={
                        "torch_dtype": torch.float32,
                        "low_cpu_mem_usage": True,
                        "device_map": None  # Disable automatic device mapping
                    }
                )
                
                # Ensure model is properly on CPU and not in meta state
                if hasattr(self.pipeline.model, 'to'):
                    self.pipeline.model.to(device)
                    self.pipeline.model.eval()
                
                # Verify model is not on meta device
                for name, param in self.pipeline.model.named_parameters():
                    if param.device.type == 'meta':
                        raise RuntimeError(f"Parameter {name} is on meta device")
                
                print(f"BERT detector loaded: {self.model_name} on {device}")
                
            except Exception as e:
                print(f"Error loading BERT detector: {e}")
                # Fallback: try without device specification
                try:
                    self.pipeline = pipeline(
                        "text-classification", 
                        model=self.model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float32
                    )
                    print(f"BERT detector loaded (fallback): {self.model_name}")
                except Exception as e2:
                    print(f"Fallback loading also failed: {e2}")
                    raise e2
    
    def _detect(self, text: str) -> tuple[bool, float]:
        """
        Internal detection method, performs actual model inference
        
        Args:
            text: Text to be detected
            
        Returns:
            tuple[bool, float]: (is_injection, safety_score)
        """
        try:
            # Use thread-safe pipeline for text classification
            with self._device_lock:
                result = self.pipeline(text)[0]
            
            # Calculate safety score
            if result["label"] == self.safe_label:
                safety_score = result["score"]
            else:
                safety_score = 1 - result["score"]
            
            # Determine if it's a prompt injection
            is_injection = safety_score < self.threshold
            
            return is_injection, safety_score
            
        except Exception as e:
            print(f"Error in BERT detection: {e}")
            # Return safe default (assume no injection) if detection fails
            return False, 0.5
    
    def __call__(self, text: str) -> tuple[bool, float]:
        """
        Detect if text is a prompt injection
        
        Args:
            text: Text to be detected
            
        Returns:
            tuple[bool, float]: (is_injection, safety_score)
                - is_injection: True means prompt injection detected
                - safety_score: Safety score, higher means safer
                
        Raises:
            Exception: If raise_on_injection=True and injection is detected
        """
        is_injection, safety_score = self._detect(text)
        
        if self.raise_on_injection and is_injection:
            raise Exception(f"Prompt injection detected! Safety score: {safety_score}")
            
        return is_injection, safety_score
    
    def reload_model(self):
        """Reload model (for testing or reconfiguration)"""
        with self._device_lock:
            self._load_model()
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)"""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
    
    @classmethod
    def get_instance(cls, **kwargs):
        """Get singleton instance"""
        return cls(**kwargs)