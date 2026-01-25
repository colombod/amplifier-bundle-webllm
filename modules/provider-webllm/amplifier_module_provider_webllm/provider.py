"""WebLLM provider implementation."""

import json

from amplifier_core.protocols import Provider, ChatRequest, ChatResponse, Message

from . import get_llm_bridge


class WebLLMProvider(Provider):
    """Provider that runs LLM inference locally via WebLLM/WebGPU.

    This provider bridges Python code in Pyodide to the WebLLM JavaScript
    library. It requires a JavaScript bridge function to be set up before use.

    The bridge function handles:
    - Model loading and management (done in JS)
    - WebGPU inference (done in JS)
    - Request/response serialization (JSON)
    """

    name = "webllm"

    def __init__(self, config: dict):
        """Initialize the WebLLM provider.

        Args:
            config: Provider configuration
                - default_model: Model identifier
                - temperature: Default sampling temperature
                - max_tokens: Default max tokens to generate
                - top_p: Default nucleus sampling parameter
        """
        self.default_model = config.get(
            "default_model", "Phi-3.5-mini-instruct-q4f16_1-MLC"
        )
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 1024)
        self.default_top_p = config.get("top_p", 0.95)

    @property
    def model(self) -> str:
        """Return the default model ID."""
        return self.default_model

    def _check_bridge(self) -> tuple[bool, str | None]:
        """Check if the JavaScript bridge is set up."""
        bridge = get_llm_bridge()
        if bridge is None:
            return False, (
                "WebLLM bridge not initialized. "
                "JavaScript must call set_llm_bridge() with a completion function. "
                "See provider-webllm documentation for setup instructions."
            )
        return True, None

    async def complete(self, request: ChatRequest, **kwargs) -> ChatResponse:
        """Complete a chat request using WebLLM.

        Args:
            request: The chat completion request
            **kwargs: Additional arguments (passed to JS bridge)

        Returns:
            ChatResponse with the model's response

        Raises:
            RuntimeError: If bridge not initialized or inference fails
        """
        # Check bridge is set up
        bridge_ok, error = self._check_bridge()
        if not bridge_ok:
            raise RuntimeError(error)

        bridge = get_llm_bridge()

        # Build request for JS bridge
        js_request = {
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            "temperature": request.temperature
            if request.temperature is not None
            else self.default_temperature,
            "max_tokens": request.max_tokens
            if request.max_tokens is not None
            else self.default_max_tokens,
            "top_p": request.top_p if request.top_p is not None else self.default_top_p,
        }

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in js_request:
                js_request[key] = value

        try:
            # Call JavaScript bridge
            request_json = json.dumps(js_request)
            response_json = await bridge(request_json)
            response_data = json.loads(response_json)

            # Parse response
            if "error" in response_data:
                raise RuntimeError(f"WebLLM error: {response_data['error']}")

            # Extract message from response
            choices = response_data.get("choices", [])
            if not choices:
                raise RuntimeError("WebLLM returned no choices")

            message_data = choices[0].get("message", {})
            content = message_data.get("content", "")

            # Build response
            response_message = Message(role="assistant", content=content)

            # Extract usage if available
            usage = response_data.get("usage", {})

            return ChatResponse(
                message=response_message,
                model=response_data.get("model", self.default_model),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                finish_reason=choices[0].get("finish_reason", "stop"),
                raw_response=response_data,
            )

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse WebLLM response: {e}")
        except Exception as e:
            if "WebLLM" in str(e) or "bridge" in str(e).lower():
                raise
            raise RuntimeError(f"WebLLM inference failed: {e}")

    async def stream(self, request: ChatRequest, **kwargs):
        """Stream a chat completion (not yet implemented).

        WebLLM supports streaming, but this requires additional bridge setup.
        For now, falls back to non-streaming completion.

        Args:
            request: The chat completion request
            **kwargs: Additional arguments

        Yields:
            ChatResponse chunks (currently yields single complete response)
        """
        # TODO: Implement streaming with JS callback bridge
        response = await self.complete(request, **kwargs)
        yield response
