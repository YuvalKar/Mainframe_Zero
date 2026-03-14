# Mainframe Zero: The Hierarchical Attention System

## What is "Attention"?
In the Mainframe Zero architecture, **Attention** is a virtual "context bubble" that functions as a node within a hierarchical tree. 

Instead of an AI agent having access to the entire system or being completely isolated, Attention uses a **Relative Level of Detail (LOD)** approach. The system dynamically defines its context based on the "degrees of separation" from the currently active node, regardless of the tree's overall depth or width.

## Purpose: Why do we need it?
When building a complex, multi-agent hierarchical system, giving the AI too much context leads to "drift" (hallucinations, losing focus). Giving it too little context leads to "amnesia". 

The Hierarchical Attention system solves this by dynamically loading context based on proximity:
1. **LOD 0 (The Self):** The active node. The agent has full access to this node's detailed chat history, active assets, and specific instructions.
2. **LOD 1 (First-Degree Relatives):** The immediate parent, direct children, and siblings. The agent receives a detailed summary of these nodes, keeping them within immediate reach.
3. **LOD 2 (Second-Degree Relatives):** Grandparents or grandchildren. The agent receives only a brief, condensed summary of their existence and purpose.
4. **Beyond LOD 2:** Out of scope. Anything further away effectively does not exist in the current working memory, preventing cognitive overload and saving token costs.
5. **Seamless Context Switching:** You can pause a highly detailed task, shift Attention to an entirely different branch, and later return to the exact state of the previous task without mixing up the AI's memory.

## How it Works (Under the Hood)
The lifecycle of an Attention state is managed by the `AttentionManager` using a PostgreSQL database.

### 1. Creation & Storage
When a new Attention is created:
* It generates a unique ID (e.g., `attn_1b574f1e`).
* It inserts a new record into the `attentions` PostgreSQL table.
* It records its `parent_id` to establish its place in the hierarchical tree.
* If files are needed, they are mapped in the `working_files` JSONB field.
* `short_summary` and `detailed_summary` can be updated later.


### 2. Context Assembly & Routing
When the Core shifts focus to an `attention_id`:
* It queries the PostgreSQL database.
* It uses a recursive SQL query (e.g., `WITH RECURSIVE`) to efficiently climb up and down the tree, gathering the "manifest" of inherited rules and relatives (LOD 1 and LOD 2) in a single database call.
* It dynamically loads the `required_app` using `importlib` and mounts only the relevant Senses and Motor Skills for that specific LOD.

## Anatomy of an Attention Object
This is the internal structure stored in the PostgreSQL database. The self-referencing `parent_id` enables the infinite tree structure

## Future Expansion
Vector Database Integration (pgvector): Leveraging our existing PostgreSQL infrastructure to add semantic search over past tasks and chat history. This will allow the Core to retrieve distant "forgotten" knowledge that falls outside of the current LOD scope by finding vector similarities in the chat_history table.