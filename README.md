# clipboardai

 https://clipboardai-clg1.onrender.com


┌──────────────────────┐
│ File 1: Monitor      │ ← Watches clipboard
└──────────┬───────────┘
           │ Detects change
           ▼
┌──────────────────────┐
│ File 2: Detector     │ ← Identifies content type
└──────────┬───────────┘
           │ "It's Python code!"
           ▼
┌──────────────────────┐
│ File 3: ClipboardAI  │ ← Coordinates handlers
└──────────┬───────────┘
           │ Notifies all handlers
           ▼
┌──────────────────────┐
│ Handler says:        │
│ "Fix typos in this!" │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ File 5: PromptMgr    │ ← Gets the RIGHT instructions for AI
└──────────┬───────────┘  "You are a code typo fixer..."
           │
           ▼
┌──────────────────────┐
│ File 4: AI Processor │ ← Calls OpenAI/Groq API
└──────────┬───────────┘
           │ AI fixes the typos
           ▼
     "def calculate..."  ✨ Fixed code!
