# Architecture & Development Status

## Project Overview
We have successfully transitioned from a CLI-only application to a full-stack architecture. The system now features a "Brain" (Python/FastAPI) and a "Face" (React/Vite), allowing for modular growth and a more intuitive user interface.

## Directory Structure
The workspace follows a semi-monorepo approach to maintain organization while allowing for independent toolchain management:
* **Root (`Mainframe_Zero/`)**: Contains the Python Backend, virtual environment (`.venv`), and core AI logic modules.
* **Frontend (`mz_frontend/`)**: A dedicated React project powered by Vite, residing inside the root directory.

## Backend Implementation (Python / FastAPI)
* **Server (`mz_server.py`)**: Runs on `http://localhost:8000`.
* **CORS**: Configured with `CORSMiddleware` to allow secure communication from the React frontend (running on port 5173).
* **Endpoint**: The `/chat` POST endpoint receives `UserRequest` objects and triggers the agentic loop.
* **Agentic Loop (`MZ_Terminal.py`)**: Modified to collect "thoughts," action results, and chat responses into a JSON-serializable log rather than printing directly to the terminal.
* **Temporary Skill Execution**: The manual `(y/n)` confirmation for active skills in the `cerebellum` was temporarily disabled in the code to prevent the FastAPI server from hanging during API requests.

## Frontend Implementation (React + Vite)
* **Development Server**: Accessible at `http://localhost:5173`.
* **Execution**: Can be started from the root using `npm run dev --prefix mz_frontend`.
* **State Management**:
    * `chatLog`: An array of objects tracking the conversation history and AI internal processes.
    * `isLoading`: A boolean controlling UI states (disabling inputs) during active API calls.
* **Core Features**:
    * **Asynchronous Fetch**: Sends user input to the backend and appends the returned log to the state.
    * **Auto-Scrolling**: Utilizes `useRef` and `useEffect` hooks to ensure the view stays pinned to the latest messages.
    * **Interface**: A monospace terminal-style layout that renders distinct log types: `[USER]`, `[THOUGHT]`, `[ACTION_RESULT]`, and `[CHAT]`.

## Roadmap for Next Sessions
1. **Visual Refinement**: Implement a true "Mainframe" aesthetic using CSS (neon accents, terminal themes, and distinct color coding for AI thoughts vs. actions).
2. **UI Approval System**: Re-implement the skill confirmation step by having the server pause and return a "pending approval" status, which the React UI will handle with interactive "Approve/Deny" buttons.
3. **Profession-Based Routing**: Integrate `react-router` to support unique interfaces for different "Professions" (e.g., specialized 3D controls for the Blender agent).