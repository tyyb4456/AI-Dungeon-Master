from graph_builder import start_session_node
from langgraph.graph import StateGraph, END
from utils.game_state import GameState

# Initialize graph
builder = StateGraph(GameState)

from graph_builder import (
    start_session_node,
    world_and_quest_node,
    narration_node,
    action_input_node,
    action_resolution_node
)

# Add nodes
builder.add_node("start_session", start_session_node)
builder.add_node("world_and_quest", world_and_quest_node)
builder.add_node("narration", narration_node)
builder.add_node("action_input", action_input_node)
builder.add_node("action_resolution", action_resolution_node)

# Define flow
builder.set_entry_point("start_session")

# Setup edges (flow connections)
builder.add_edge("start_session", "world_and_quest")
builder.add_edge("world_and_quest", "narration")
builder.add_edge("narration", "action_input")
builder.add_edge("action_input", "action_resolution")

# 📢 ♻️ Loop back: After resolving an action → narrate again!
builder.add_edge("action_resolution", "narration")


# Compile the graph
graph = builder.compile()

# Run it
if __name__ == "__main__":
    final_state = graph.invoke(GameState())
    print("\n✅ Session Initialized:")
    print(final_state)
