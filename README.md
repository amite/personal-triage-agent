# Personal Task Manager Triage

This is a Minimally Viable Application (MVA) called the "Personal Task Manager Triage." This MVA must be stateful, multi-step, and built using the ReAct agent pattern within a LangGraph framework. The primary goal is to demonstrate autonomous decision-making where a central Triage Agent analyzes a complex user request and delegates its sub-components to the appropriate specialized agents/tools. This will be a CLI app built with rich library components.

## 1. The User Input

The system must handle a single, multi-part request, such as:

> "I need to prepare for the meeting tomorrow, remind me to check the attached files, and draft an email to the client about the new deadline. Also, search for the current stock price of Google."

## 2. Core Components (The Agents and Tools)

The LangGraph will consist of four main nodes (one dispatcher and three workers), each linked to a specific function or tool.

| Component | Role & Function | Type |
|---|---|---|
| Triage Agent | Dispatcher: The ReAct-based entry point. It analyzes the full input, identifies discrete sub-tasks, and routes them to the correct worker agent. | Agent (ReAct) |
| Drafting Agent | Handles tasks requiring text generation (e.g., drafting an email). | Worker Agent |
| Scheduler Agent | Handles time-sensitive tasks (e.g., setting reminders). | Worker Agent |
| Data Agent | Handles look-up or verification tasks (e.g., checking files, retrieving external data). | Worker Agent |
| Tool: ReminderTool | Writes a reminder string to a persistent state or file (simulated: reminders.txt). | Function/Tool |
| Tool: DraftingTool | Generates and saves a draft email based on a prompt (simulated: drafts.txt). | Function/Tool |
| Tool: ExternalSearchTool | Retrieves information based on a query (simulated: returns a simple string, e.g., "Google stock is $1500"). | Function/Tool |

## 3. The Stateful Workflow (LangGraph Flow)

The application state must contain a central object, primarily:

- `user_request`: The initial input string.
- `task_queue`: A list of remaining tasks, formatted as: `[{'type': 'email', 'content': 'draft an email about X'}, {'type': 'reminder', 'content': 'check files'}, ...]`
- `results`: A dictionary storing the output from each worker agent.

The flow is defined by the Triage Agent's autonomous decisions:

1. **START -> Triage Agent**: The Triage Agent receives the `user_request`.
2. **Triage Agent's Decision**:
   - It parses the request and populates the `task_queue`.
   - **Autonomous Decision Point 1 (ReAct)**: The agent inspects the first task in the queue and decides which worker agent/tool is needed (email, reminder, or data).
   - It then routes the flow to the corresponding worker node.
3. **Worker Execution**: The routed worker agent (e.g., Drafting Agent) executes its specific task, potentially calling its associated tool (DraftingTool).
4. **Worker -> Triage Agent Loop**:
   - The worker updates the `results` state with its output.
   - It routes the flow back to the Triage Agent.
5. **Triage Agent's Loop Decision**:
   - **Autonomous Decision Point 2**: The Triage Agent checks the `task_queue`.
   - If the queue is not empty, it pops the completed task and routes the flow to the next appropriate worker.
   - If the queue is empty, the agent routes the flow to the final step.
6. **Triage Agent -> FINISH**: The agent compiles all outputs from the `results` state into a single, cohesive final summary for the user and terminates the graph.

## Prompt Task Summary

The final output of this MVA should be a concise summary of the actions taken, like:

> "Action Summary: 1. Set reminder: 'check attached files'. 2. Drafted email saved to drafts.txt. 3. Google stock price is $1500."
