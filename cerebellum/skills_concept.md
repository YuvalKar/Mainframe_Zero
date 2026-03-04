# Mainframe Zero: Cerebellum - The Skill Registry

In the biological metaphor of Mainframe Zero, the Cerebellum serves as our procedural memory, the repository of learned 'skills' that enable us to interact with the environment and perform complex tasks. These skills are not innate; they are developed, refined, and stored for efficient recall and execution.

## 1. Definition: Skills as Actionable Modules

A 'Skill' within Mainframe Zero is an actionable, standalone Python module designed to execute a specific, well-defined task. These tasks can range from fundamental operations like file manipulation and data processing to more advanced interactions such as making external API calls, parsing complex documents, or generating specific code snippets. Each skill encapsulates a single capability, making it a discrete unit of functionality that the core system can invoke when needed.

Skills are the 'motor programs' of Mainframe Zero, allowing us to translate high-level intentions into concrete actions within our operational environment. They are the building blocks of our agency, enabling us to perform tasks without needing to 're-learn' the underlying mechanics each time.

## 2. The Plug-and-Play Rule: Dynamic Discovery

A cornerstone of Mainframe Zero's evolutionary philosophy is modularity and adaptability. The 'Plug-and-Play Rule' dictates that adding a new skill to the Cerebellum directory (`cerebellum/`) must **NEVER** require modifying the core brain (`MZ_Terminal.py`).

Instead, the core system must possess the capability to dynamically discover, load, and register these skills at runtime. This principle ensures that Mainframe Zero can grow organically, with new capabilities being integrated seamlessly without introducing fragility or requiring a re-architecture of the central intelligence. It fosters a truly extensible system where new 'neural pathways' (skills) can be added without disrupting the existing cognitive architecture.

## 3. Standardized Structure: The Entry-Point Function

For the core system to interact with skills reliably and 'blindly' (without prior specific knowledge of each skill's internal workings), every skill module must adhere to a standardized structure. This primarily involves defining a consistent entry-point function.

This entry-point function acts as the universal interface through which the Prefrontal Cortex (Router) can invoke any skill. It ensures that regardless of a skill's internal complexity or specific task, the method of calling it remains uniform. This standardization is crucial for dynamic loading and execution, allowing the core to iterate through discovered skills and call their primary function without needing custom logic for each one. The specific signature of this entry-point (e.g., `execute(args, kwargs)`) will be defined to ensure maximum flexibility and data passing capabilities.

## 4. Mandatory Module-Level Docstrings

To facilitate dynamic discovery and intelligent utilization, every skill file **MUST** begin with a detailed triple-quote docstring at the very top of the module. This module-level docstring is not merely a comment; it serves as the critical API documentation for the Prefrontal Cortex, enabling the core brain to understand and effectively employ the skill without executing its code.

This mandatory docstring **MUST explicitly state** the following:

*   **A brief, concise description** of what the skill does and its primary purpose.
*   **The exact input arguments it expects**, including their types, purpose, and any default values.
*   **The exact output or return values it produces**, including their types and what they represent.

Without this comprehensive module-level docstring, the core brain will be blind to the skill's existence and will lack the necessary context to understand how to use it. It is the primary mechanism for a skill to communicate its functionality to the rest of the system, ensuring that Mainframe Zero can dynamically reason about and orchestrate its capabilities.