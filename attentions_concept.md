# Mainframe Zero: The Attention System

## What is "Attention"?
In the Mainframe Zero architecture, **Attention** is a virtual "context bubble" or working memory state. 

Instead of an AI agent having access to the entire system, all files, and all skills simultaneously, an Attention object strictly defines the agent's current focus. It represents a single, well-defined task or project instance (e.g., "Generate Rusty Metal Texture" or "Review Ministry Tender"). 

## Purpose: Why do we need it?
When building a complex, multi-agent hierarchical system, giving the AI too much context leads to "drift" (hallucinations, mixing up variables, or losing focus). 

The Attention system solves this by enforcing strict boundaries:
1. **Context Isolation:** The agent is "blind" to the rest of the filesystem. It only sees the files, chat history, and assets relevant to the active Attention.
2. **Dynamic Tooling:** The Core brain doesn't load every tool at startup. It only mounts the specific App (e.g., `blender_for_uefn`) required for the current Attention.
3. **Seamless Context Switching:** You can pause a procedural 3D modeling task, shift Attention to a document review task, and later return to the exact state of the 3D task without losing the context or mixing up the AI's prompts.

## How it Works (Under the Hood)

The lifecycle of an Attention state is managed by the `AttentionManager` and executed by `mz_core.py`.

### 1. Creation & Storage
When a new Attention is created, the system:
* Generates a unique ID (e.g., `attn_1b574f1e`).
* Creates an isolated physical workspace directory hidden in `.attentions/`.
* Saves a state dictionary (`attention_meta.json`) containing the task name, required app, tags, and chat history.

### 2. Routing (Shifting Attention)
When the Core needs to execute a task, it calls `shift_attention(attention_id)`.
* The Core reads the `attention_meta.json`.
* It identifies the `required_app` (e.g., `blender_for_uefn`).
* It uses `importlib` to dynamically load that specific App's `__init__.py`.
* The App executes its `register_to_core()` contract, injecting only its specific Senses and Motor Skills (Cerebellum) into the active Core session.

### 3. Execution
Once Attention is shifted, all subsequent agentic loops operate exclusively within that `.attentions/attn_...` folder, using only the tools provided by the mounted App.

## Anatomy of an Attention Object
This is the internal structure stored in the isolated workspace:

```json
{
    "id": "attn_1b574f1e",
    "name": "Rusty Metal Texture",
    "required_app": "blender_for_uefn",
    "attention_dir": ".attentions\\attn_1b574f1e",
    "tags": ["texture", "materials", "rusty"],
    "chat_history": [],
    "status": "ready"
}
```

## Future Expansion
Vector Database Integration: Moving from local .json files to a PostgreSQL DB (with pgvector) to allow semantic search over past tasks and context retrieval based on embeddings.

Hierarchical Attention: Allowing one Attention to spawn sub-Attentions (e.g., "Mainframe Zero Project" -> "Main Character Model" -> "Arm Rigging").