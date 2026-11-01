# server_tools – simple server controls (Windows)

Double-click a file. They work with the Docker version of CyberQuest (started by `run.bat`).
CyberQuest = container `cyberquest` · Knowledge Base (RAG) = container `cyberquest-rag`.

| File | What it does |
|---|---|
| `stop_server.bat` | Stops the web app. Data is kept. |
| `restart_server.bat` | Restarts the web app and waits until `/health/` answers. |
| `pause_server.bat` | Pauses the web app. Run it again to resume. |
| `start_knowledgebase.bat` | Starts the Knowledge Base container. |
| `stop_knowledgebase.bat` | Stops the Knowledge Base. CyberQuest keeps working without it. |
| `restart_knowledgebase.bat` | Restarts the Knowledge Base and waits until it is healthy. |
| `check_knowledgebase.bat` | Checks container, `/health`, the model setting, an optional test question, and the web app. |

First start everything once with `run.bat`. If you use `run_local.bat` (no Docker), stop with CTRL+C and close the small
"CyberQuest Knowledge Base" window instead.
