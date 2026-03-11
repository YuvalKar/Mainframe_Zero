# Mainframe Zero: The App (Specialty) Architecture

## What is an "App"?
In the Mainframe Zero ecosystem, an **App** (short for Application or Specialty) is a modular, domain-specific toolkit. 

If the Core (`mz_core.py`) is the brain stem that handles basic reasoning, routing, and memory, an App is a specialized "lobe" (like the visual cortex or motor cortex) that is only activated when needed. Examples include `blender_for_uefn`, `tender_reviewer`, or even the self-modifying `mainframe_architect`.

## Purpose: Why do we use Apps?
1. **Keeping the Core Lightweight:** The Core Engine should not know how to manipulate 3D vertices in Blender or parse government PDF tables. It only needs to know *how to ask* an App to do it.
2. **Preventing Tool Hallucination:** Giving an AI agent 500 different tools at once confuses it. By isolating tools into Apps, the AI only sees the tools relevant to its current domain.
3. **Encapsulation & Safety:** If the Blender App crashes or has heavy asset dependencies (like `.blend` files or large Python libraries), it doesn't pollute or break the rest of the system.

## How it Works: The Contract
An App is completely dormant until the `AttentionManager` shifts the system's focus to a task that requires it. 

When activated, the Core dynamically imports the App and looks for a specific "Contract" function: `register_to_core(core_system, attention_data)`. 
Through this function, the App "injects" its specialized capabilities into the Core for the duration of the task.

## Anatomy of an App
A standard App lives inside the `apps/` directory and follows the biological architecture of the Mainframe:

```text
apps/
└── my_special_app/
    ├── __init__.py           # The Ambassador. Contains `register_to_core()`.
    ├── senses/               # Domain-specific perception tools (Read-only).
    │   └── read_data.py      # e.g., scanning a specific 3D scene or parsing a doc.
    └── cerebellum/           # Domain-specific motor skills (Actions).
        └── do_action.py      # e.g., generating a mesh or sending an email.
```

## The Special Case: Mainframe Architect
There is one deliberate exception to the strict isolation rules: the mainframe_architect app.
1. **Meta-Programming:** This App is designed to expand Mainframe Zero itself.
2. **Root Access:** While standard Apps are strictly confined to their .attentions/attn_xxx workspace to prevent accidental damage, the Architect has "root access" to the entire Mainframe_Zero directory.
3. **Capabilities:** It uses its meta-senses to read the system's own Python code and its meta-motor skills to generate new App boilerplates, modify the Core, or write configurations. It is the system's tool for self-improvement.

## App vs. Attention
It is crucial to understand the difference between these two core concepts:
- The App is the Factory & Tools (e.g., The Blender Toolkit). It is static code.
- The Attention is the Work Order & Context (e.g., "Build a Rusty Pipe"). It is dynamic state.
- Many different Attentions can use the same App simultaneously or sequentially.

## Building a New App
To create a new App, you must:
- Create a lowercase, underscore-separated folder in apps/.
- Create an __init__.py with the register_to_core function.
- Add specific tools to local senses/ and cerebellum/ folders.
- Update the Core (when necessary) to scan the active App's folders for tools.
