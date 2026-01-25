"""WebLLM provider for Amplifier.

Provides local LLM inference in browser via WebGPU. This provider bridges
Python code running in Pyodide to the WebLLM JavaScript library.
"""

from .provider import WebLLMProvider

# The JavaScript bridge function - set by browser before provider is used
_js_llm_complete = None


def set_llm_bridge(complete_fn):
    """Set the JavaScript bridge function for LLM completions.

    This must be called from JavaScript before using the provider.

    Example JavaScript setup:
        // Create WebLLM engine first
        const engine = await CreateMLCEngine('Phi-3.5-mini-instruct-q4f16_1-MLC');

        // Create bridge function
        async function llmComplete(requestJson) {
            const request = JSON.parse(requestJson);
            const response = await engine.chat.completions.create({
                messages: request.messages,
                temperature: request.temperature ?? 0.7,
                max_tokens: request.max_tokens ?? 1024,
            });
            return JSON.stringify({
                choices: [{ message: { role: 'assistant', content: response.choices[0].message.content } }],
                usage: response.usage
            });
        }

        // Register with Python
        pyodide.globals.set('js_llm_complete', llmComplete);
        pyodide.runPython(`
            from amplifier_module_provider_webllm import set_llm_bridge
            import js
            set_llm_bridge(js.js_llm_complete)
        `)
    """
    global _js_llm_complete
    _js_llm_complete = complete_fn


def get_llm_bridge():
    """Get the current LLM bridge function."""
    return _js_llm_complete


async def mount(coordinator, config: dict):
    """Mount the WebLLM provider.

    Args:
        coordinator: The Amplifier coordinator
        config: Provider configuration
            - default_model: Model ID (default: "Phi-3.5-mini-instruct-q4f16_1-MLC")
            - temperature: Default temperature (default: 0.7)
            - max_tokens: Default max tokens (default: 1024)
    """
    provider = WebLLMProvider(config)
    coordinator.mount_points["providers"][provider.name] = provider

    # Set as default provider if none set
    if coordinator.config.get("session", {}).get("provider") is None:
        if "session" not in coordinator.config:
            coordinator.config["session"] = {}
        coordinator.config["session"]["provider"] = provider.name

    return None  # No cleanup needed
