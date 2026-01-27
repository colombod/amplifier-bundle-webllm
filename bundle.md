---
bundle:
  name: webllm
  version: 1.0.0
  description: Browser-based local LLM inference via WebGPU with Amplifier integration

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/microsoft/amplifier-bundle-webruntime@main#subdirectory=behaviors/webruntime
  - bundle: webllm:behaviors/webllm
---

# WebLLM Bundle

**Run local LLMs in the browser with WebGPU acceleration.**

Build browser-based AI applications using WebLLM for inference and Amplifier for session management.

## What This Bundle Provides

### From webruntime (included)
- **webruntime-developer** agent for building browser Amplifier apps
- Pyodide integration patterns
- Autonomous Playwright testing

### WebLLM-Specific
- WebLLM provider bridge for Amplifier
- Model selection guidance
- WebGPU optimization patterns

## Quick Start

```
"Build me a WebLLM chat app as a single HTML file"
"Create an offline AI assistant with Phi-3.5"
"Make a browser-based coding helper"
```

## Supported Models

| Model | Size | VRAM | Best For |
|-------|------|------|----------|
| Phi-3.5-mini-instruct-q4f16_1-MLC | 2.4GB | 4GB | General use |
| Llama-3.2-3B-Instruct-q4f16_1-MLC | 2.1GB | 4GB | Fast responses |
| Qwen2.5-7B-Instruct-q4f16_1-MLC | 4.2GB | 8GB | Multilingual |

## How It Works

1. **WebLLM** loads model weights via WebGPU
2. **Pyodide** runs amplifier-core in the browser
3. **Provider bridge** connects WebLLM to Amplifier sessions
4. **Tools** execute in JavaScript, results flow back to Python

---

@webllm:context/webllm-guide.md

---

@foundation:context/shared/common-system-base.md
