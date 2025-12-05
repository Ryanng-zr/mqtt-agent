# Repository Analysis

This repository implements a lightweight MQTT-driven agent that uses Google Gemini for planning and orchestration of backend tools. The agent consumes MQTT messages, validates them against a Pydantic schema, selects a goal, plans tool calls, executes them, and summarizes the results.

## Architecture Overview
- **Entry point:** `app/main.py` configures MQTT connection settings from environment variables, subscribes to a topic, and forwards validated messages into the agent pipeline.
- **Message schema:** `app/mqttPayloadSchema.py` defines the `BaseMessage` envelope for incoming MQTT payloads.
- **Agent pipeline:**
  - `app/selectGoal.py` selects the best goal for a message and classifies it into a goal mode using Gemini.
  - `app/chooseToolCall.py` asks Gemini to plan tool calls based on the payload, goal, and tool descriptions.
  - `app/executeToolCall.py` executes the planned tool calls, collects results, and asks Gemini for a human-readable summary.
- **Tools:** `app/tools.py` houses HTTP-based tool implementations and a registry (`TOOLS`) that exposes descriptions and callables to the planner.
- **LLM client:** `app/llm.py` configures the Gemini model using the `GEMINI_API_KEY` environment variable.

## Data Flow
1. An MQTT payload is received on the configured topic.
2. The payload is parsed and validated into `BaseMessage`.
3. The agent selects a goal and goal mode with Gemini.
4. Gemini plans one or more tool calls; the agent executes them via the local registry.
5. Execution results and context are summarized by Gemini and printed to the console.

## Configuration
- MQTT settings are controlled by environment variables such as `MQTT_BROKER`, `MQTT_PORT`, `MQTT_CLIENT_ID`, and `MQTT_TOPIC_AIR_TRACKS`.
- Backend HTTP targets use `BACKEND_BASE_URL` and `COMMON_HEADERS` in `app/tools.py`.
- Gemini requires `GEMINI_API_KEY` to be set; loading is handled via `dotenv` in `app/llm.py`.

## Notable Behaviors and Considerations
- Tool planning and goal selection rely on structured JSON responses from Gemini; `app/helper.py` extracts JSON objects from model output.
- Tool execution includes basic error handling for missing tools, argument issues, and runtime exceptions.
- The agent currently blocks on `client.loop_forever()` in `app/main.py`; it is designed to run as a long-lived service.

## Potential Follow-ups
- Add tests for schema validation and tool planning to catch malformed payloads early.
- Expand error handling around MQTT connection failures and retry behavior.
- Consider logging structured summaries to persistent storage instead of stdout.
