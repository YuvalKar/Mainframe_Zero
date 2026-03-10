# Architecture & Development Status

## Project Overview
We have successfully transitioned from a CLI-only application to a full-stack architecture. The system now features a "Brain" (Python/FastAPI) and a "Face" (React/Vite), allowing for modular growth and a more intuitive user interface.

## Directory Structure
The workspace follows a semi-monorepo approach to maintain organization while allowing for independent toolchain management:
* **Root (`Mainframe_Zero/`)**: Contains the Python Backend, virtual environment (`.venv`), and core AI logic modules.
* **Frontend (`mz_frontend/`)**: A dedicated React project powered by Vite, residing inside the root directory.

## Backend Implementation (Python / FastAPI)
* **Server (`mz_server.py`)**: Runs on `http://localhost:8000`.
* **CORS**: Configured with `CORSMiddleware` to allow secure communication from the React frontend.
* **Core Logic (`mz_core.py`)**: The central brain containing the agentic loop, previously housed in the terminal. It now manages the execution of skills and senses.
* **Communication (WebSockets)**: Moving from a standard POST endpoint to a WebSocket connection (`/ws/chat`) to allow real-time, bi-directional streaming of AI thoughts, actions, and user approvals without blocking the server.

## Frontend Implementation (React + Vite)
* **Development Server**: Accessible at `http://localhost:5173`.
* **Execution**: Can be started from the root using `npm run dev --prefix mz_frontend`.
* **State Management**:
    * `chatLog`: An array of objects tracking the conversation history and AI internal processes in real-time.
    * `connectionStatus`: Tracking the WebSocket connection state (Connected, Disconnected, Pending Approval).
* **Core Features**:
    * **WebSocket Integration**: Maintains an open line to the backend, appending incoming thoughts, chat messages, and action results to the UI instantly.
    * **Auto-Scrolling**: Utilizes `useRef` and `useEffect` hooks to ensure the view stays pinned to the latest messages.
    * **Interface**: A monospace terminal-style layout that renders distinct log types: `[USER]`, `[THOUGHT]`, `[ACTION_RESULT]`, and `[CHAT]`.

## Roadmap for Next Sessions
1. **Visual Refinement**: Implement a true "Mainframe" aesthetic using CSS (neon accents, terminal themes, and distinct color coding for AI thoughts vs. actions).
2. **UI Approval System (Real-Time)**: Implement the skill confirmation step via WebSockets. The server will pause the loop, stream a "pending approval" request to the UI, and wait for the user to click "Approve" or "Deny" before continuing execution.
3. **Profession-Based Routing**: Integrate `react-router` to support unique interfaces for different "Professions" (e.g., specialized 3D controls for the Blender agent).