# WebLLM Guide

This document provides context for AI assistants working with WebLLM-based Amplifier applications.

---

## IMPORTANT: WebLLM as an Amplifier Provider

**WebLLM in the Amplifier ecosystem is used as a PROVIDER for Amplifier sessions, not as a standalone JavaScript library.**

### The Correct Architecture

```
Browser App
  |
  +-- Pyodide (Python in WASM)
        |
        +-- amplifier-core
              |
              +-- WebLLM Provider (via JS bridge)
                    |
                    +-- WebLLM Engine (JavaScript)
```

### NOT This (Unless Explicitly Requested)

```
[X] Browser App --> WebLLM Engine (raw JS, no Amplifier)
```

### Why Use WebLLM Through Amplifier?

Using WebLLM as an Amplifier provider (instead of raw JS) gives you:
- **Session management** - Amplifier handles conversation history
- **Tool support** - Use browser-storage, todo, custom tools
- **Provider switching** - Swap to OpenAI/Anthropic without code changes
- **Hooks** - Logging, approval gates, observability
- **Consistency** - Same patterns as CLI Amplifier

Raw JavaScript WebLLM is only appropriate for:
- Quick demos or prototypes
- When the user explicitly requests "no Python" or "pure JavaScript"

---

## What is WebLLM?

WebLLM runs Large Language Models directly in web browsers using WebGPU for hardware acceleration. This enables:

- **Fully offline AI** - Works without internet after initial model download
- **Complete privacy** - Data never leaves the user's device
- **No API costs** - No per-request charges
- **Local inference** - Uses the device's GPU for computation

---

## Requirements

### Browser Support

| Browser | WebGPU Support | Notes |
|---------|---------------|-------|
| Chrome 113+ | ✅ Full | Recommended |
| Edge 113+ | ✅ Full | Recommended |
| Firefox | ⚠️ Behind flag | `dom.webgpu.enabled` |
| Safari 18+ | ✅ Full | macOS Sonoma+ |

### Hardware Requirements

| Model Size | Minimum VRAM | Recommended |
|------------|--------------|-------------|
| 1-3B params | 4GB | 6GB+ |
| 7-8B params | 8GB | 12GB+ |
| 13B+ params | 16GB+ | 24GB+ |

Most integrated GPUs (Intel, Apple M1/M2) have 4-8GB shared memory and can run smaller models.

---

## Available Models

### Recommended Models

| Model | Size | VRAM | Quality | Speed | Best For |
|-------|------|------|---------|-------|----------|
| **Phi-3.5-mini-instruct-q4f16_1-MLC** | 2.4GB | 4GB | Good | Fast | General use, low-end hardware |
| **Llama-3.2-3B-Instruct-q4f16_1-MLC** | 2.1GB | 4GB | Good | Fast | General use |
| **Llama-3.1-8B-Instruct-q4f16_1-MLC** | 4.5GB | 8GB | Better | Medium | Quality-focused |
| **Qwen2.5-7B-Instruct-q4f16_1-MLC** | 4.2GB | 8GB | Better | Medium | Multilingual |

### Quantization Levels

| Quantization | Size | Quality | Speed |
|--------------|------|---------|-------|
| q4f16 | Smallest | Good | Fastest |
| q4f32 | Small | Better | Fast |
| q0f16 | Large | Best | Slower |
| q0f32 | Largest | Best | Slowest |

**Recommendation**: Use `q4f16` for most applications - best balance of size/speed/quality.

---

## Provider Bridge

WebLLM runs in JavaScript, while Amplifier runs in Python (Pyodide). The provider bridges these:

```
┌─────────────────────────────────────────────────────────────┐
│  JavaScript                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WebLLM Engine                                       │   │
│  │  • Loads model via WebGPU                           │   │
│  │  • Runs inference                                    │   │
│  │  • Returns completions                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▲                                  │
│                          │ js_llm_complete(requestJson)     │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Python (Pyodide)                                    │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  WebLLMProvider                               │  │   │
│  │  │  • Implements Provider protocol               │  │   │
│  │  │  • Serializes requests to JSON                │  │   │
│  │  │  • Calls JS bridge function                   │  │   │
│  │  │  • Deserializes responses                     │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## JavaScript Setup

### Basic WebLLM Initialization

```javascript
import { CreateMLCEngine } from '@mlc-ai/web-llm';

// Initialize engine with progress callback
const engine = await CreateMLCEngine('Phi-3.5-mini-instruct-q4f16_1-MLC', {
    initProgressCallback: (progress) => {
        const pct = Math.round(progress.progress * 100);
        console.log(`Loading model: ${pct}%`);
        updateProgressUI(pct);
    }
});

console.log('Model loaded!');
```

### Bridge Function for Amplifier

```javascript
// Create the bridge function that Python will call
async function llmComplete(requestJson) {
    const request = JSON.parse(requestJson);
    
    const response = await engine.chat.completions.create({
        messages: request.messages,
        temperature: request.temperature ?? 0.7,
        max_tokens: request.max_tokens ?? 1024,
        top_p: request.top_p ?? 0.95,
    });
    
    // Return in OpenAI-compatible format
    return JSON.stringify({
        id: response.id,
        object: 'chat.completion',
        created: Date.now(),
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

// Register with Pyodide
pyodide.globals.set('js_llm_complete', llmComplete);
```

---

## Model Loading

### First Load (Network Required)

On first use, models are downloaded from the MLC-AI CDN:

```
Model: Phi-3.5-mini-instruct-q4f16_1-MLC
Size: ~2.4GB
Time: 1-5 minutes depending on connection
```

### Subsequent Loads (Cached)

After first download, models are cached in browser storage:

```
Cache location: Origin Private File System (OPFS)
Load time: 5-15 seconds
Works offline: Yes
```

### Cache Management

```javascript
// Check if model is cached
const cachedModels = await webllm.getCachedModels();
console.log('Cached models:', cachedModels);

// Clear cache (to free space)
await webllm.clearCache();
```

---

## Performance Optimization

### Token Generation Speed

Typical speeds (varies by hardware):

| Hardware | Model | Tokens/sec |
|----------|-------|------------|
| RTX 4090 | 8B q4f16 | 80-120 |
| RTX 3080 | 8B q4f16 | 40-60 |
| M2 MacBook | 3B q4f16 | 30-50 |
| Intel iGPU | 3B q4f16 | 10-20 |

### Memory Management

```javascript
// Check available GPU memory (approximate)
const adapter = await navigator.gpu.requestAdapter();
const device = await adapter.requestDevice();
console.log('Max buffer size:', device.limits.maxBufferSize);

// For low-memory devices, use smaller models
if (device.limits.maxBufferSize < 4 * 1024 * 1024 * 1024) {
    // Use 3B model instead of 8B
    modelId = 'Llama-3.2-3B-Instruct-q4f16_1-MLC';
}
```

### Reduce Memory Pressure

- Close other GPU-intensive tabs
- Use smaller quantization (q4f16)
- Clear browser cache if needed
- Restart browser if experiencing slowdowns

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `WebGPU not supported` | Browser lacks WebGPU | Use Chrome 113+ or Edge 113+ |
| `Out of memory` | Model too large for GPU | Use smaller model or quantization |
| `Model not found` | Invalid model ID | Check model name against MLC catalog |
| `Network error during load` | Download interrupted | Retry, check connection |
| `Shader compilation failed` | GPU driver issue | Update GPU drivers |

### Error Recovery

```javascript
try {
    const engine = await CreateMLCEngine(modelId);
} catch (error) {
    if (error.message.includes('WebGPU')) {
        showError('Your browser does not support WebGPU. Please use Chrome 113+ or Edge 113+.');
    } else if (error.message.includes('memory')) {
        // Try smaller model
        const engine = await CreateMLCEngine('Llama-3.2-3B-Instruct-q4f16_1-MLC');
    } else {
        showError(`Failed to load AI model: ${error.message}`);
    }
}
```

---

## Offline Patterns

### Service Worker for PWA

```javascript
// Register service worker for offline support
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}

// In sw.js - cache the model weights
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('webllm-models').then((cache) => {
            // Model weights are cached automatically by WebLLM
            // This caches your app shell
            return cache.addAll([
                '/',
                '/index.html',
                '/app.js',
            ]);
        })
    );
});
```

### Detect Online/Offline

```javascript
// Show status to user
function updateOnlineStatus() {
    const status = navigator.onLine ? 'Online' : 'Offline';
    document.getElementById('status').textContent = status;
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
```

---

## Best Practices

### 1. Show Loading Progress

Model loading takes time - always show progress:

```javascript
const engine = await CreateMLCEngine(modelId, {
    initProgressCallback: ({ progress, timeElapsed, text }) => {
        showProgress(progress * 100, text);
    }
});
```

### 2. Warm Up the Model

First inference is slower - warm up after loading:

```javascript
// Warm up with a simple request
await engine.chat.completions.create({
    messages: [{ role: 'user', content: 'Hi' }],
    max_tokens: 1
});
console.log('Model warmed up!');
```

### 3. Handle Memory Limits

Monitor and handle memory pressure:

```javascript
// Check memory before loading large model
if (navigator.deviceMemory && navigator.deviceMemory < 8) {
    console.warn('Low memory device - using smaller model');
    modelId = 'Phi-3.5-mini-instruct-q4f16_1-MLC';
}
```

### 4. Provide Fallbacks

Not everyone has WebGPU - offer alternatives:

```javascript
async function initProvider() {
    if (!navigator.gpu) {
        return initAPIProvider(); // Fall back to OpenAI/Anthropic
    }
    try {
        return await initWebLLM();
    } catch (e) {
        console.warn('WebLLM failed, falling back to API:', e);
        return initAPIProvider();
    }
}
```

---

## Model Selection Guide

### For General Chat

**Recommended**: `Phi-3.5-mini-instruct-q4f16_1-MLC`
- Good quality responses
- Fast inference
- Works on most hardware

### For Coding Tasks

**Recommended**: `Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC`
- Specialized for code
- Better code completion
- Requires 8GB+ VRAM

### For Multilingual

**Recommended**: `Qwen2.5-7B-Instruct-q4f16_1-MLC`
- Strong multilingual support
- Good for non-English tasks
- Requires 8GB+ VRAM

### For Low-End Hardware

**Recommended**: `Llama-3.2-1B-Instruct-q4f16_1-MLC`
- Smallest model
- Fast even on iGPUs
- Reduced quality but usable

---

## References

- WebLLM Documentation: https://webllm.mlc.ai/
- MLC-LLM Model List: https://mlc.ai/mlc-llm/docs/
- WebGPU Specification: https://www.w3.org/TR/webgpu/
- Supported Models: https://mlc.ai/mlc-llm/docs/deploy/rest.html#supported-model-architectures
