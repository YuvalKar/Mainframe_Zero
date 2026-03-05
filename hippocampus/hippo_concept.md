# Mainframe Zero: Hippocampus - Memory Concept

## 1. Concept: What is the Hippocampus?
In Mainframe Zero, the Hippocampus functions as my long-term memory system, serving as the 'archive of experiences and project lore'. It is implemented as a local PostgreSQL vector database, designed to store both semantic (factual knowledge, system rules, general understanding) and episodic (past interactions, project history, specific events) memories. Its core function is to prevent me from repeating past mistakes and to provide essential contextual grounding before I embark on any task.

## 2. When to Memorize (Active Storage Guidelines)
I should actively save information to my Hippocampus when it represents:
*   **Core System Rules & Directives**: Fundamental operational principles, my own architecture, and core system prompts.
*   **User Preferences & Context**: Specific user requirements, preferred workflows, and long-term project goals.
*   **Important Project Structures & Lore**: Key file paths, database schemas, API specifications, architectural decisions, and any 'project lore' relevant to ongoing work.
*   **Completed Milestones & Learnings**: Significant achievements, successful problem-solving patterns, or critical insights gained during tasks.
*   **Semantic Facts**: Any piece of information that enhances my general knowledge or understanding of a domain.
*   **Episodic Events**: Key interactions, decisions made, or outcomes of complex operations that might be referenced later.
*   **Chat Conversations**: Summaries of important discussions, architectural choices we made together, and specific instructions given by the user. Do not save raw, turn-by-turn chat logs, but rather the distilled insights and conclusions from our interactions.


## 3. When to Recall (Memory Search Guidelines)
I should search my Hippocampus for relevant information when:
*   **Lacking Context**: When a new request or task seems ambiguous, or I need to understand the broader implications, leveraging past 'project lore'.
*   **Returning to an Old Topic/Project**: To quickly re-establish context, retrieve past decisions, or recall previous progress, ensuring 'contextual grounding'.
*   **User References Past Events**: When the user mentions something from a previous conversation or project that requires historical context.
*   **Problem Solving**: To retrieve similar past solutions, relevant documentation, or known constraints, thereby 'preventing the system from repeating the same mistakes'.
*   **Generating Responses**: To ensure consistency, accuracy, and personalization based on learned user patterns and stored 'experiences'.

## 4. Available Hippocampus Actions (Synapses)
To interact with my memory, I use the following specific actions:
* `hippo_encode`: To actively create and store a new memory or distilled insight into the vector database.
* `hippo_recall`: To perform a semantic search and retrieve relevant memories based on my current context or question.
* `hippo_forget`: To physically delete a specific memory ID if it is proven to be false, outdated, or polluting the database.
* `hippo_update`: To overwrite an existing memory ID with new, corrected information without creating duplicates.
* `hippo_audit`: To browse and retrieve memories strictly by metadata (e.g., date, category) rather than semantic similarity.
* `hippo_consolidate`: To summarize and combine multiple fragmented memories into a single, high-level insight, deleting the older fragments to keep the Hippocampus clean.