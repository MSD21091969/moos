"""Streaming support for Ollama responses."""
from typing import Callable, Generator
import ollama


def stream_chat(
    model: str,
    messages: list[dict],
    options: dict | None = None,
    callback: Callable[[str], None] | None = None,
) -> str:
    """
    Stream a chat response from Ollama.
    
    Args:
        model: Model name
        messages: Chat messages
        options: Ollama options dict
        callback: Called for each token (for real-time display)
        
    Returns:
        Complete response text
    """
    full_response = ""
    
    for chunk in ollama.chat(
        model=model,
        messages=messages,
        options=options,
        stream=True,
    ):
        content = chunk.get("message", {}).get("content", "")
        full_response += content
        
        if callback:
            callback(content)
    
    return full_response


def stream_generate(
    model: str,
    prompt: str,
    options: dict | None = None,
    callback: Callable[[str], None] | None = None,
) -> str:
    """
    Stream a generate response from Ollama.
    
    Args:
        model: Model name
        prompt: Input prompt
        options: Ollama options dict
        callback: Called for each token
        
    Returns:
        Complete response text
    """
    full_response = ""
    
    for chunk in ollama.generate(
        model=model,
        prompt=prompt,
        options=options,
        stream=True,
    ):
        content = chunk.get("response", "")
        full_response += content
        
        if callback:
            callback(content)
    
    return full_response


def print_callback(token: str) -> None:
    """Default callback that prints to stdout."""
    print(token, end="", flush=True)
