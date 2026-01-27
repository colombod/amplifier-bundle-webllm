# WebLLM Model Selection Guide

Choosing the right model depends on your use case, target hardware, and quality requirements.

## Recommended Models

| Model | Size | VRAM | Quality | Speed | Best For |
|-------|------|------|---------|-------|----------|
| **Phi-3.5-mini-instruct-q4f16_1-MLC** | 2.4GB | 4GB | ★★★★☆ | Fast | **Default choice** - best balance |
| **Llama-3.2-3B-Instruct-q4f16_1-MLC** | 2.1GB | 4GB | ★★★★☆ | Fast | General chat, good reasoning |
| **Llama-3.2-1B-Instruct-q4f16_1-MLC** | 0.7GB | 2GB | ★★★☆☆ | Very Fast | Low-end hardware, quick responses |
| **Qwen2.5-1.5B-Instruct-q4f16_1-MLC** | 1.0GB | 3GB | ★★★☆☆ | Fast | Multilingual, compact |
| **Qwen2.5-7B-Instruct-q4f16_1-MLC** | 4.2GB | 8GB | ★★★★★ | Medium | High quality, multilingual |
| **Llama-3.1-8B-Instruct-q4f16_1-MLC** | 4.5GB | 8GB | ★★★★★ | Medium | Best reasoning |
| **Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC** | 4.2GB | 8GB | ★★★★★ | Medium | Code generation |

## Selection by Use Case

### General Chat / Assistants
**Recommended:** `Phi-3.5-mini-instruct-q4f16_1-MLC`
- Best quality-to-size ratio
- Good instruction following
- Works on most hardware

### Code Generation
**Recommended:** `Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC`
- Specialized for code
- Better completions and explanations
- Requires 8GB+ VRAM

### Multilingual Applications
**Recommended:** `Qwen2.5-7B-Instruct-q4f16_1-MLC`
- Strong non-English support
- Good for translation tasks
- Requires 8GB+ VRAM

### Low-End Hardware / Mobile
**Recommended:** `Llama-3.2-1B-Instruct-q4f16_1-MLC`
- Smallest model
- Works on integrated GPUs
- Fast responses, lower quality

### Maximum Quality (No Constraints)
**Recommended:** `Llama-3.1-8B-Instruct-q4f16_1-MLC`
- Best reasoning capability
- Longest coherent responses
- Requires 8GB+ VRAM

## Hardware Requirements

### By GPU Type

| GPU Type | Recommended Models |
|----------|-------------------|
| **Integrated (Intel/AMD)** | 1B, 1.5B models |
| **Apple M1/M2** | Up to 3B models |
| **Apple M1/M2 Pro/Max** | Up to 8B models |
| **RTX 3060/4060 (8GB)** | Up to 7B-8B models |
| **RTX 3080/4080+ (12GB+)** | Any model |

### Checking Available VRAM

```javascript
async function checkGPUMemory() {
    const adapter = await navigator.gpu.requestAdapter();
    const device = await adapter.requestDevice();
    const maxBuffer = device.limits.maxBufferSize;
    
    // Rough VRAM estimate (not exact)
    const estimatedVRAM = maxBuffer / (1024 * 1024 * 1024);
    console.log(`Estimated available: ~${estimatedVRAM.toFixed(1)}GB`);
    
    return estimatedVRAM;
}
```

## Quantization Levels

Models come in different quantization levels affecting size/quality:

| Quantization | Size | Quality | Speed | When to Use |
|--------------|------|---------|-------|-------------|
| **q4f16** | Smallest | Good | Fastest | **Default choice** |
| **q4f32** | Small | Better | Fast | Slightly better quality |
| **q0f16** | Large | Best | Slower | Quality critical |
| **q0f32** | Largest | Best | Slowest | Maximum quality |

**Recommendation:** Always use `q4f16` unless you have a specific reason not to.

## Model Selector Implementation

```javascript
const AVAILABLE_MODELS = [
    { 
        id: 'Phi-3.5-mini-instruct-q4f16_1-MLC', 
        name: 'Phi 3.5 Mini', 
        size: '2.4GB',
        vram: 4,
        recommended: true 
    },
    { 
        id: 'Llama-3.2-3B-Instruct-q4f16_1-MLC', 
        name: 'Llama 3.2 3B', 
        size: '2.1GB',
        vram: 4
    },
    { 
        id: 'Llama-3.2-1B-Instruct-q4f16_1-MLC', 
        name: 'Llama 3.2 1B (Fast)', 
        size: '0.7GB',
        vram: 2
    },
    { 
        id: 'Qwen2.5-1.5B-Instruct-q4f16_1-MLC', 
        name: 'Qwen 2.5 1.5B', 
        size: '1.0GB',
        vram: 3
    },
    { 
        id: 'Qwen2.5-7B-Instruct-q4f16_1-MLC', 
        name: 'Qwen 2.5 7B', 
        size: '4.2GB',
        vram: 8
    },
    { 
        id: 'Llama-3.1-8B-Instruct-q4f16_1-MLC', 
        name: 'Llama 3.1 8B', 
        size: '4.5GB',
        vram: 8
    }
];

function filterModelsByVRAM(availableVRAM) {
    return AVAILABLE_MODELS.filter(m => m.vram <= availableVRAM);
}

function getRecommendedModel(availableVRAM) {
    const suitable = filterModelsByVRAM(availableVRAM);
    return suitable.find(m => m.recommended) || suitable[suitable.length - 1];
}
```

## Auto-Selection Pattern

```javascript
async function selectBestModel() {
    const adapter = await navigator.gpu.requestAdapter();
    const info = await adapter.requestAdapterInfo();
    
    // Check for known GPU types
    const vendor = info.vendor.toLowerCase();
    const device = info.device.toLowerCase();
    
    // Apple Silicon
    if (vendor.includes('apple')) {
        if (device.includes('pro') || device.includes('max')) {
            return 'Llama-3.1-8B-Instruct-q4f16_1-MLC';
        }
        return 'Phi-3.5-mini-instruct-q4f16_1-MLC';
    }
    
    // NVIDIA
    if (vendor.includes('nvidia')) {
        // High-end cards
        if (device.includes('4090') || device.includes('4080') || 
            device.includes('3090') || device.includes('a100')) {
            return 'Llama-3.1-8B-Instruct-q4f16_1-MLC';
        }
        // Mid-range
        if (device.includes('4070') || device.includes('3080') || 
            device.includes('3070')) {
            return 'Qwen2.5-7B-Instruct-q4f16_1-MLC';
        }
        // Entry level
        return 'Phi-3.5-mini-instruct-q4f16_1-MLC';
    }
    
    // Intel/AMD integrated - use smallest
    if (vendor.includes('intel') || vendor.includes('amd')) {
        return 'Llama-3.2-1B-Instruct-q4f16_1-MLC';
    }
    
    // Default safe choice
    return 'Phi-3.5-mini-instruct-q4f16_1-MLC';
}
```

## Performance Expectations

### Tokens per Second (Approximate)

| Model | RTX 4090 | RTX 3080 | M2 MacBook | Intel iGPU |
|-------|----------|----------|------------|------------|
| 1B | 150+ | 100+ | 80+ | 30-40 |
| 3B | 100+ | 60+ | 40+ | 15-25 |
| 7-8B | 80+ | 40+ | 25+ | N/A |

### First Token Latency

| Model | Typical | With Warm-up |
|-------|---------|--------------|
| 1B | 0.5-1s | 0.2-0.5s |
| 3B | 1-2s | 0.5-1s |
| 7-8B | 2-4s | 1-2s |

## Model Warm-up

First inference is always slower. Warm up after loading:

```javascript
async function warmUpModel(engine) {
    console.log('Warming up model...');
    await engine.chat.completions.create({
        messages: [{ role: 'user', content: 'Hi' }],
        max_tokens: 1
    });
    console.log('Model ready!');
}
```

## Caching Behavior

Models are cached in the browser's Origin Private File System (OPFS):

- **First load:** Downloads from MLC CDN (slow)
- **Subsequent loads:** Uses cached model (fast)
- **Cache persists:** Until browser data cleared

```javascript
// Check cached models
import { getCachedModels, clearCache } from '@mlc-ai/web-llm';

const cached = await getCachedModels();
console.log('Cached models:', cached);

// Clear cache if needed
await clearCache();
```
