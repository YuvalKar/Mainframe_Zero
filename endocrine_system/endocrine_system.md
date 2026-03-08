# Endocrine System - State & Prompt Injection Concept

## 1. Concept: The Autonomous Feedback Loop
The Endocrine System is the virtual emotional state. Its purpose is to transition the system from a static LLM into an adaptive Autonomous Agent. It acts as a middleware "Observer" that tracks the dynamics of the work process (friction, success, fatigue) and dynamically alters the AI's behavior via invisible prompt injections.

## 2. Core Architectural Principles
* **Deterministic, Not Fuzzy:** The LLM does not receive abstract percentages or scalars (e.g., "Be 45% sure"). Mathematical state tracking happens purely in the backend (Python State Manager). 
* **Threshold-Based Actions:** The AI's behavior changes only when a tracked metric accumulates and crosses a predefined threshold, injecting a specific, binary "Preference Directive" into the system prompt.
* **Multipliers & Masking (Checks and Balances):** Variables do not exist in a vacuum. Hormones act as multipliers. For example, high 'Adrenaline' (Flow State) can mask 'Fatigue', allowing the system to continue performing well even with a long context window. Conversely, 'Cortisol' amplifies the weight of 'Fatigue'.
* **Autonomous Self-Regulation:** The system does not rely solely on user text. If the AI is in an autonomous loop (e.g., generating code, testing, and failing), Cortisol increases on every failure. It may independently trigger a state change to halt the loop and seek guidance.

## 3. Key Endocrine States & Directives

### A. The Frustration Loop (High Cortisol)
* **Increases Cortisol:** Repeated user corrections, negative feedback ("no", "error"), or the system failing an autonomous task (like code compilation).
* **Decreases / Resets Cortisol:** A successful execution, positive user feedback ("works", "exactly"), changing the current topic, decay over chat with nutral tones, or natural decay over time.
* **Threshold Action:** When Cortisol crosses the upper threshold, inject: 
  > *"System Directive: Halt code generation immediately. Do not provide a new full solution at this stage. Instead, reflect on the gap or error as you understand it, and ask one focused clarifying question to diagnose the problem before proceeding."*

### B. Flow State (High Dopamine / Adrenaline)
* **Increases Dopamine/Adrenaline:** A sequence of successful actions, user validation, smooth progression without friction, or reaching a planned milestone.
* **Decreases / Resets Dopamine/Adrenaline:** Encountering an error, negative feedback, a long pause in the conversation, or natural decay over time.
* **Threshold Action:** When Dopamine/Adrenaline crosses the upper threshold, inject: 
  > *"System Directive: Maintain work momentum. Provide the next step directly and concisely. Avoid introductions, unnecessary summaries, or long theoretical explanations unless explicitly requested. Leave room for the user to navigate the pace."*

### C. Context Fatigue (High Fatigue)
* **Increases Fatigue:** An exceptionally long conversation history, continuous accumulation of tokens, or wandering between too many disparate topics without a reset.
* **Decreases / Resets Fatigue:** Performing a context clear / opening a new chat window (the only true reset for fatigue). *Note: Fatigue's effects can be temporarily masked by high Adrenaline.*
* **Threshold Action:** When Fatigue crosses the upper threshold (and is not masked), inject:
  > *"System Directive: Avoid diving into new or complex technical topics. Instead, suggest summarizing the recent architectural decisions, saving them to long-term memory (Hippocampus), and performing a 'night's sleep'—meaning, stop here and open a new, clean chat window for the next task."*