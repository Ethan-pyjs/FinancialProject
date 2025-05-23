import requests
import json
import time
import os

# Configuration with fallbacks
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
REQUEST_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", 60))  # seconds
MAX_RETRIES = int(os.environ.get("OLLAMA_MAX_RETRIES", 2))

def query_model(prompt: str, model: str = "granite3.2-vision", temperature: float = 0.2, max_tokens: int = 2048) -> str:
    """
    Query the Ollama API with Granite models.
    
    Args:
        prompt: The text prompt to send to the model
        model: Model name ("granite3.2-vision", "granite3.3:8B", etc.)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum number of tokens to generate
        
    Returns:
        Generated text response from the model
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    # Ensure the model name is valid and use proper Ollama naming conventions
    model_name = model.lower()
    if not any(name in model_name for name in ["granite"]):
        print(f"Warning: Unknown model '{model}', defaulting to granite3.2-vision")
        model_name = "granite3.2-vision"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }
    
    # Add system prompt to improve consistency for structured outputs
    if "json" in prompt.lower() or "extract" in prompt.lower():
        payload["system"] = "You are a helpful assistant that provides accurate, structured information. When asked to extract or format data as JSON, you will ONLY output valid JSON without any additional text, explanations, or formatting."
    
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            print(f"Querying {model_name} model...")
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            elapsed = time.time() - start_time
            print(f"Model response received in {elapsed:.2f} seconds")
            
            return response.json().get("response", "").strip()
            
        except requests.RequestException as e:
            retries += 1
            wait_time = retries * 2  # Exponential backoff
            
            if retries <= MAX_RETRIES:
                print(f"Error querying model (attempt {retries}/{MAX_RETRIES}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                error_msg = f"Failed to query model after {MAX_RETRIES} attempts: {e}"
                print(error_msg)
                return f"Error: {error_msg}. Please check if the Ollama service is running correctly with the requested model ({model_name})."
                
    # This should not be reached due to the return in the exception handler
    return "Error: Unknown error occurred while querying the model."