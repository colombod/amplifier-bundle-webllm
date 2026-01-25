# provider-webllm

WebLLM provider for Amplifier - enables local LLM inference in browsers via WebGPU.

## Overview

This provider bridges Amplifier (running in Pyodide) to the WebLLM JavaScript library, enabling fully local, offline-capable AI applications in web browsers.

## Requirements

- WebGPU-capable browser (Chrome 113+, Edge 113+, Safari 18+)
- Sufficient GPU memory for chosen model (4GB+ for small models)
- Initial network connection for model download (cached afterward)

## Installation

This module is included with `amplifier-bundle-webllm`. To use it standalone:

```yaml
providers:
  - module: provider-webllm
    source: git+https://github.com/microsoft/amplifier-bundle-webllm@main#subdirectory=modules/provider-webllm
    config:
      default_model: "Phi-3.5-mini-instruct-q4f16_1-MLC"
```

## JavaScript Bridge Setup

Before using this provider, JavaScript must:

1. Load and initialize WebLLM
2. Create a bridge function
3. Register it with Python

```javascript
import { CreateMLCEngine } from '@mlc-ai/web-llm';

// 1. Initialize WebLLM engine
const engine = await CreateMLCEngine('Phi-3.5-mini-instruct-q4f16_1-MLC', {
    initProgressCallback: (progress) => {
        console.log(`Loading: ${Math.round(progress.progress * 100)}%`);
    }
});

// 2. Create bridge function
async function llmComplete(requestJson) {
    const request = JSON.parse(requestJson);
    
    const response = await engine.chat.completions.create({
        messages: request.messages,
        temperature: request.temperature ?? 0.7,
        max_tokens: request.max_tokens ?? 1024,
        top_p: request.top_p ?? 0.95,
    });
    
    return JSON.stringify({
        model: engine.currentModelId,
        choices: [{
            index: 0,
            message: {
                role: 'assistant',
                content: response.choices[0].message.content
            },
            finish_reason: response.choices[0].finish_reason
        }],
        usage: response.usage
    });
}

// 3. Register with Pyodide
pyodide.globals.set('js_llm_complete', llmComplete);
await pyodide.runPythonAsync(`
    from amplifier_module_provider_webllm import set_llm_bridge
    import js
    set_llm_bridge(js.js_llm_complete)
`);
```

## Configuration

```yaml
providers:
  - module: provider-webllm
    source: webllm:modules/provider-webllm
    config:
      # Model to use (must match JS engine initialization)
      default_model: "Phi-3.5-mini-instruct-q4f16_1-MLC"
      
      # Default generation parameters
      temperature: 0.7
      max_tokens: 1024
      top_p: 0.95
```

## Supported Models

| Model | Size | VRAM | Notes |
|-------|------|------|-------|
| Phi-3.5-mini-instruct-q4f16_1-MLC | 2.4GB | 4GB | Recommended default |
| Llama-3.2-3B-Instruct-q4f16_1-MLC | 2.1GB | 4GB | Good alternative |
| Llama-3.1-8B-Instruct-q4f16_1-MLC | 4.5GB | 8GB | Higher quality |
| Qwen2.5-7B-Instruct-q4f16_1-MLC | 4.2GB | 8GB | Good multilingual |

See [MLC-LLM docs](https://mlc.ai/mlc-llm/docs/) for full model list.

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Bridge not initialized" | `set_llm_bridge()` not called | Run JS setup code first |
| "WebGPU not supported" | Browser lacks WebGPU | Use Chrome 113+ |
| "Out of memory" | Model too large | Use smaller model |

## Streaming (Future)

Streaming is not yet implemented. The `stream()` method currently falls back to non-streaming completion.

## Architecture

```
┌─────────────────────────────────────────┐
│  JavaScript                             │
│  ├── WebLLM Engine (model, inference)   │
│  └── llmComplete() bridge function      │
└─────────────────┬───────────────────────┘
                  │ JSON
                  ▼
┌─────────────────────────────────────────┐
│  Python (Pyodide)                       │
│  ├── WebLLMProvider (Provider protocol) │
│  └── Amplifier session                  │
└─────────────────────────────────────────┘
```

## License

MIT
