import os
import json
from mqttPayloadSchema import BaseMessage
from executeToolCall import run_agent_for_message
from pydantic import ValidationError
import paho.mqtt.client as mqtt

# MQTT integration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "gemini-mqtt-agent")

# Example air track topic
MQTT_TOPIC_AIR_TRACKS = os.environ.get("MQTT_TOPIC_AIR_TRACKS", "sensors/air_tracks")

# Goals to be given and set by product teams
GOALS = [
    "Monitor all air track states",
    "Trigger DSS for target X",
    "Check air tracks and then run DSS",
    "Monitor tracks and notify me",
]


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected to broker: {reason_code}")
    print(f"[MQTT] Subscribing to topic: {MQTT_TOPIC_AIR_TRACKS}")
    client.subscribe(MQTT_TOPIC_AIR_TRACKS, qos=1)


def on_message(client, userdata, msg):
    raw = msg.payload.decode("utf-8", errors="replace")
    topic = msg.topic
    print(f"\n[MQTT] Message received on topic '{topic}': {raw}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[MQTT] Invalid JSON payload: {e}")
        return

    try:
        base_msg = BaseMessage(**data)
    except ValidationError as e:
        print(f"[MQTT] Payload does not match BaseMessage schema: {e}")
        return

    candidate_goals = GOALS

    try:
        summary = run_agent_for_message(base_msg, candidate_goals)
        print("\n[AGENT] FINAL SUMMARY:")
        print(summary)
    except Exception as e:
        print(f"[AGENT] Error during agent run: {e}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT} ...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    client.loop_forever()


if __name__ == "__main__":
    main()
