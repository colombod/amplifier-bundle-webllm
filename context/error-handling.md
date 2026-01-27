# WebLLM Error Handling

This guide covers common errors and how to handle them gracefully.

## Error Categories

1. **WebGPU Errors** - Browser/hardware compatibility
2. **Model Loading Errors** - Download/cache issues
3. **Inference Errors** - Runtime generation issues
4. **Memory Errors** - Out of VRAM/RAM

## WebGPU Errors

### WebGPU Not Supported

```javascript
if (!navigator.gpu) {
    showError({
        title: 'WebGPU Not Available',
        message: 'Your browser does not support WebGPU.',
        suggestions: [
            'Use Chrome 113+ or Edge 113+',
            'Enable WebGPU in Firefox: about:config → dom.webgpu.enabled',
            'Update Safari to version 18+',
            'Make sure hardware acceleration is enabled'
        ]
    });
    return;
}
```

### No GPU Adapter

```javascript
const adapter = await navigator.gpu.requestAdapter();
if (!adapter) {
    showError({
        title: 'No GPU Found',
        message: 'WebGPU is available but no compatible GPU was found.',
        suggestions: [
            'Update your GPU drivers',
            'Check that your GPU supports WebGPU',
            'Close other GPU-intensive applications',
            'Try restarting your browser'
        ]
    });
    return;
}
```

### Checking Specific Capabilities

```javascript
async function checkWebGPUCapabilities() {
    try {
        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) throw new Error('No adapter');
        
        const device = await adapter.requestDevice();
        const info = await adapter.requestAdapterInfo();
        
        return {
            supported: true,
            vendor: info.vendor,
            architecture: info.architecture,
            device: info.device,
            maxBufferSize: device.limits.maxBufferSize,
            maxComputeWorkgroupsPerDimension: device.limits.maxComputeWorkgroupsPerDimension
        };
    } catch (e) {
        return { supported: false, error: e.message };
    }
}
```

## Model Loading Errors

### Network Errors

```javascript
try {
    llmEngine = await CreateMLCEngine(modelId, {
        initProgressCallback: onProgress
    });
} catch (e) {
    if (e.message.includes('fetch') || e.message.includes('network')) {
        showError({
            title: 'Download Failed',
            message: 'Could not download the AI model.',
            suggestions: [
                'Check your internet connection',
                'The model server may be temporarily unavailable',
                'Try again in a few minutes',
                'Check if your firewall blocks CDN access'
            ]
        });
    }
}
```

### Model Not Found

```javascript
try {
    llmEngine = await CreateMLCEngine(modelId, options);
} catch (e) {
    if (e.message.includes('not found') || e.message.includes('404')) {
        showError({
            title: 'Model Not Found',
            message: `The model "${modelId}" was not found.`,
            suggestions: [
                'Check the model ID is spelled correctly',
                'The model may have been removed or renamed',
                'Try a different model from the list'
            ]
        });
    }
}
```

### Shader Compilation Errors

```javascript
try {
    llmEngine = await CreateMLCEngine(modelId, options);
} catch (e) {
    if (e.message.includes('shader') || e.message.includes('compilation')) {
        showError({
            title: 'GPU Shader Error',
            message: 'Failed to compile GPU shaders for this model.',
            suggestions: [
                'Update your GPU drivers to the latest version',
                'Try a smaller model',
                'Restart your browser',
                'This GPU may not be fully compatible'
            ]
        });
    }
}
```

## Memory Errors

### Out of Memory During Load

```javascript
try {
    llmEngine = await CreateMLCEngine(modelId, options);
} catch (e) {
    if (e.message.includes('memory') || e.message.includes('OOM') || 
        e.message.includes('allocation')) {
        showError({
            title: 'Out of Memory',
            message: 'Not enough GPU memory to load this model.',
            suggestions: [
                'Try a smaller model (1B or 3B instead of 7B)',
                'Close other browser tabs',
                'Close other GPU-intensive applications',
                'Restart your browser to free memory'
            ],
            action: {
                label: 'Try Smaller Model',
                onClick: () => loadModel('Llama-3.2-1B-Instruct-q4f16_1-MLC')
            }
        });
    }
}
```

### Out of Memory During Inference

```javascript
async function safeGenerate(messages) {
    try {
        return await llmEngine.chat.completions.create({
            messages,
            max_tokens: 1024  // Limit output length
        });
    } catch (e) {
        if (e.message.includes('memory')) {
            // Try with shorter output
            return await llmEngine.chat.completions.create({
                messages,
                max_tokens: 256
            });
        }
        throw e;
    }
}
```

## Inference Errors

### Generation Timeout

```javascript
async function generateWithTimeout(messages, timeoutMs = 60000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
        const result = await llmEngine.chat.completions.create({
            messages,
            max_tokens: 1024
        });
        clearTimeout(timeoutId);
        return result;
    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            throw new Error('Generation timed out. The model may be overloaded.');
        }
        throw e;
    }
}
```

### Invalid Response

```javascript
function validateResponse(response) {
    if (!response?.choices?.[0]?.message?.content) {
        console.warn('Invalid response structure:', response);
        return {
            content: 'I encountered an issue generating a response. Please try again.',
            isError: true
        };
    }
    return {
        content: response.choices[0].message.content,
        isError: false
    };
}
```

## Comprehensive Error Handler

```javascript
class WebLLMErrorHandler {
    static handle(error, context = {}) {
        const errorInfo = this.classify(error);
        
        console.error(`[WebLLM] ${errorInfo.type}:`, error);
        
        return {
            type: errorInfo.type,
            title: errorInfo.title,
            message: errorInfo.message,
            suggestions: errorInfo.suggestions,
            recoverable: errorInfo.recoverable,
            originalError: error
        };
    }
    
    static classify(error) {
        const msg = error.message?.toLowerCase() || '';
        
        // WebGPU errors
        if (msg.includes('webgpu') || !navigator.gpu) {
            return {
                type: 'WEBGPU_UNAVAILABLE',
                title: 'WebGPU Not Available',
                message: 'Your browser does not support WebGPU.',
                suggestions: ['Use Chrome 113+', 'Use Edge 113+', 'Update Safari to 18+'],
                recoverable: false
            };
        }
        
        // Memory errors
        if (msg.includes('memory') || msg.includes('oom') || msg.includes('allocation')) {
            return {
                type: 'OUT_OF_MEMORY',
                title: 'Out of Memory',
                message: 'Not enough GPU memory.',
                suggestions: ['Try a smaller model', 'Close other applications', 'Restart browser'],
                recoverable: true
            };
        }
        
        // Network errors
        if (msg.includes('fetch') || msg.includes('network') || msg.includes('failed to load')) {
            return {
                type: 'NETWORK_ERROR',
                title: 'Network Error',
                message: 'Could not download required files.',
                suggestions: ['Check internet connection', 'Try again later'],
                recoverable: true
            };
        }
        
        // Shader errors
        if (msg.includes('shader') || msg.includes('compilation')) {
            return {
                type: 'SHADER_ERROR',
                title: 'GPU Shader Error',
                message: 'Failed to compile GPU code.',
                suggestions: ['Update GPU drivers', 'Try a different model'],
                recoverable: true
            };
        }
        
        // Default
        return {
            type: 'UNKNOWN',
            title: 'Error',
            message: error.message || 'An unexpected error occurred.',
            suggestions: ['Refresh the page', 'Try again'],
            recoverable: true
        };
    }
}

// Usage
try {
    await initWebLLM();
} catch (e) {
    const errorInfo = WebLLMErrorHandler.handle(e);
    showErrorUI(errorInfo);
    
    if (errorInfo.recoverable && errorInfo.type === 'OUT_OF_MEMORY') {
        // Offer to try smaller model
        offerSmallerModel();
    }
}
```

## User-Friendly Error UI

```javascript
function showError(errorInfo) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-card';
    errorDiv.innerHTML = `
        <div class="error-icon">⚠️</div>
        <h3 class="error-title">${errorInfo.title}</h3>
        <p class="error-message">${errorInfo.message}</p>
        <ul class="error-suggestions">
            ${errorInfo.suggestions.map(s => `<li>${s}</li>`).join('')}
        </ul>
        ${errorInfo.action ? `
            <button class="error-action" onclick="${errorInfo.action.onClick}">
                ${errorInfo.action.label}
            </button>
        ` : ''}
    `;
    document.body.appendChild(errorDiv);
}
```

## Fallback Strategies

### Progressive Model Fallback

```javascript
const MODEL_FALLBACK_CHAIN = [
    'Phi-3.5-mini-instruct-q4f16_1-MLC',
    'Llama-3.2-3B-Instruct-q4f16_1-MLC',
    'Llama-3.2-1B-Instruct-q4f16_1-MLC'
];

async function loadWithFallback() {
    for (const modelId of MODEL_FALLBACK_CHAIN) {
        try {
            console.log(`Trying model: ${modelId}`);
            return await CreateMLCEngine(modelId, options);
        } catch (e) {
            console.warn(`Failed to load ${modelId}:`, e.message);
            if (modelId === MODEL_FALLBACK_CHAIN[MODEL_FALLBACK_CHAIN.length - 1]) {
                throw new Error('All models failed to load');
            }
        }
    }
}
```

### API Fallback (Hybrid Mode)

```javascript
async function generateWithFallback(messages) {
    // Try local WebLLM first
    if (llmEngine) {
        try {
            return await llmEngine.chat.completions.create({ messages });
        } catch (e) {
            console.warn('Local generation failed, falling back to API');
        }
    }
    
    // Fall back to API if available
    if (OPENAI_API_KEY) {
        return await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: 'gpt-4o-mini', messages })
        }).then(r => r.json());
    }
    
    throw new Error('No generation method available');
}
```
