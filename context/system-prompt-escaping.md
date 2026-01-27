# System Prompt Escaping

When embedding system prompts in browser Amplifier applications, special characters must be properly escaped to avoid breaking JavaScript or Python strings.

## The Problem

System prompts often contain:
- Backticks (`) for code formatting
- Template literal syntax (`${...}`)
- Triple quotes (`"""`) for Python
- Backslashes for escape sequences
- Newlines and special characters

These can break when embedded in JavaScript template literals or Python strings.

## JavaScript Template Literal Escaping

### Characters to Escape

| Character | Escape As | Reason |
|-----------|-----------|--------|
| `` ` `` | `\`` | Closes template literal |
| `${` | `\${` | Template interpolation |
| `\` | `\\` | Escape character |

### Escaping Function

```javascript
function escapeForTemplateLiteral(str) {
    return str
        .replace(/\\/g, '\\\\')   // Backslashes first!
        .replace(/`/g, '\\`')     // Backticks
        .replace(/\$\{/g, '\\${'); // Template syntax
}

// Usage
const SYSTEM_PROMPT = `${escapeForTemplateLiteral(rawPrompt)}`;
```

### Example

```javascript
// RAW prompt with problematic characters
const rawPrompt = `You can use \`code blocks\` and ${variables}.

Here's an example:
\`\`\`python
print("Hello")
\`\`\``;

// ESCAPED for template literal
const escapedPrompt = `You can use \\\`code blocks\\\` and \${variables}.

Here's an example:
\\\`\\\`\\\`python
print("Hello")
\\\`\\\`\\\``;
```

## Python Triple-Quote Escaping

When passing prompts to Pyodide's `runPythonAsync`, you're embedding in Python triple-quoted strings.

### Characters to Escape

| Character | Escape As | Reason |
|-----------|-----------|--------|
| `"""` | `\"\"\"` | Closes triple quote |
| `\` | `\\` | Python escape |

### Escaping Function

```javascript
function escapeForPythonTripleQuote(str) {
    return str
        .replace(/\\/g, '\\\\')      // Backslashes first!
        .replace(/"""/g, '\\"\\"\\"'); // Triple quotes
}
```

### Example

```javascript
const systemPrompt = `Some prompt with """quotes""" inside.`;

// When embedding in Python:
const escaped = escapeForPythonTripleQuote(systemPrompt);
await pyodide.runPythonAsync(`
session.set_system_prompt("""${escaped}""")
`);
```

## Combined Escaping (JS → Python)

When your prompt goes through both JavaScript AND Python, escape for both:

```javascript
function escapeForBoth(str) {
    return str
        // First escape for JavaScript template literal
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\$\{/g, '\\${')
        // Then escape for Python triple quotes
        .replace(/"""/g, '\\"\\"\\"');
}
```

## Real-World Pattern

Here's the complete pattern used in production:

```javascript
const SYSTEM_PROMPT = `You are an AI assistant.

## Code Examples

Use backticks for inline \`code\` and triple backticks for blocks:

\`\`\`python
def hello():
    print("Hello, World!")
\`\`\`

## Variables

Don't confuse \${template} syntax with actual variables.
`;

// When creating the session
async function createSession() {
    // Escape for Python embedding
    const escapedPrompt = SYSTEM_PROMPT
        .replace(/\\/g, '\\\\')
        .replace(/"""/g, '\\"\\"\\"');
    
    await pyodide.runPythonAsync(`
session = create_session(model_id="${modelId}")
session.set_system_prompt("""${escapedPrompt}""")
await session.initialize()
`);
}
```

## Common Mistakes

### ❌ Wrong: Unescaped Backticks

```javascript
// BREAKS - backticks close the template literal
const PROMPT = `Use \`code\` formatting`;
```

### ✅ Correct: Escaped Backticks

```javascript
// WORKS - backticks are escaped
const PROMPT = `Use \\\`code\\\` formatting`;
```

### ❌ Wrong: Unescaped Template Syntax

```javascript
// BREAKS - ${} is interpreted as JS interpolation
const PROMPT = `Don't use ${variables} directly`;
```

### ✅ Correct: Escaped Template Syntax

```javascript
// WORKS - template syntax is escaped
const PROMPT = `Don't use \${variables} directly`;
```

### ❌ Wrong: Triple Quotes in Python

```javascript
// BREAKS - triple quotes close Python string
await pyodide.runPythonAsync(`
session.set_system_prompt("""Use """quotes""" carefully""")
`);
```

### ✅ Correct: Escaped Triple Quotes

```javascript
// WORKS - triple quotes are escaped
const prompt = `Use """quotes""" carefully`;
const escaped = prompt.replace(/"""/g, '\\"\\"\\"');
await pyodide.runPythonAsync(`
session.set_system_prompt("""${escaped}""")
`);
```

## Escape Order Matters!

Always escape backslashes FIRST, then other characters:

```javascript
// ✅ CORRECT ORDER
str.replace(/\\/g, '\\\\')  // Backslashes first
   .replace(/`/g, '\\`')    // Then backticks

// ❌ WRONG ORDER - double-escapes the backtick escapes
str.replace(/`/g, '\\`')    // Creates \`
   .replace(/\\/g, '\\\\')  // Then escapes the \ in \` → \\`
```

## Testing Your Escaping

```javascript
function testEscaping(prompt) {
    try {
        // Test 1: Can it be used in a template literal?
        const inTemplate = `${prompt}`;
        
        // Test 2: Does it round-trip through Python?
        const escaped = prompt.replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"');
        // This would run in Pyodide
        const pythonCode = `test = """${escaped}"""`;
        
        console.log('✅ Escaping looks correct');
        return true;
    } catch (e) {
        console.error('❌ Escaping failed:', e);
        return false;
    }
}
```

## Markdown in System Prompts

Markdown is very common in system prompts. Key characters:

| Markdown | Safe? | Notes |
|----------|-------|-------|
| `# Headers` | ✅ | No escaping needed |
| `**bold**` | ✅ | No escaping needed |
| `*italic*` | ✅ | No escaping needed |
| `` `code` `` | ⚠️ | Escape backticks |
| `[links](url)` | ✅ | No escaping needed |
| `> quotes` | ✅ | No escaping needed |
| `---` | ✅ | No escaping needed |
| `\|tables\|` | ✅ | No escaping needed |
| ```` ```code blocks``` ```` | ⚠️ | Escape backticks |

## Quick Reference

```javascript
// For JavaScript template literals:
prompt.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$\{/g, '\\${')

// For Python triple-quoted strings:
prompt.replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"')

// For both (JS template → Python string):
prompt.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$\{/g, '\\${').replace(/"""/g, '\\"\\"\\"')
```
