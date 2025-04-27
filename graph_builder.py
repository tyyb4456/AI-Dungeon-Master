from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from utils.game_state import GameState
from langchain_core.prompts import PromptTemplate

from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import re
import random
from utils.inventory_manager import add_item_to_inventory, show_inventory, remove_item_from_inventory


# Load environment variables
load_dotenv()

model = ChatGroq(
    model="deepseek-r1-distill-llama-70b",
    temperature=0.5
)

# 1️⃣ Define the Start Session Node
def start_session_node(input_state: GameState) -> GameState:
    print("\n🎲 Welcome to AI Dungeon Master!\n")

    # Simulate user input collection (we’ll replace this with UI/CLI later)
    player_name = input("Enter your character name: ")
    character_class = input("Choose your class (e.g., Rogue, Mage, Paladin): ")
    setting = input("Choose your setting (Fantasy, Sci-Fi, etc.): ")

    # Optional preferences (can be extended)
    preferences = {
        "difficulty": input("Choose difficulty (Easy/Medium/Hard): ")
    }

    # Update and return new state
    return GameState(
        player_name=player_name,
        character_class=character_class,
        setting=setting,
        preferences=preferences,
        game_started=True
    )

def world_and_quest_node(input_state: GameState) -> GameState:
    with open("prompts/world_and_quest_prompt.txt", "r", encoding="utf-8") as file:
        raw_prompt = file.read()

    prompt = PromptTemplate.from_template(raw_prompt)
    formatted_prompt = prompt.format(
        player_name=input_state.player_name,
        character_class=input_state.character_class,
        setting=input_state.setting,
        preferences=input_state.preferences
    )

    # Send to LLM
    result = model.invoke(formatted_prompt).content

    # For simplicity, we can split it based on known markers
    sections = result.split("\n")
    world_intro = sections[0]
    location_intro = sections[1]
    npcs = [sections[2]]  # Can parse this better later
    main_quest = sections[3]

    return input_state.copy(update={
        "world_intro": world_intro,
        "location_intro": location_intro,
        "npcs": npcs,
        "main_quest": main_quest
    })

def narration_node(input_state: GameState) -> GameState:
    with open("prompts/narration_prompt.txt", "r", encoding="utf-8") as file:
        raw_prompt = file.read()

    # Check if coming after initial setup or after action resolution
    world_intro = input_state.world_intro
    location_intro = input_state.location_intro
    npcs = input_state.npcs
    main_quest = input_state.main_quest

    if input_state.action_result:  # If an action just happened
        location_intro = input_state.action_result  # Use new event as location description
        npcs = ""  # Optionally update npcs
        main_quest = ""  # Optionally update quest (or keep it)

    prompt = PromptTemplate.from_template(raw_prompt)
    formatted_prompt = prompt.format(
        world_intro=world_intro,
        location_intro=location_intro,
        npcs=npcs,
        main_quest=main_quest
    )

    # Call LLM
    result = model.invoke(formatted_prompt).content

    # Basic next action detection
    actions = []
    # lines = result.split("\n")
    matches = re.findall(r'\d+\.\s(.+)', result)
    for action in matches:
        actions.append(action.strip())

    # 📌 SAFETY: if no actions found, add defaults
    if not actions:
        actions = [
            "Explore further into the ruins",
            "Return to Eclipse Plaza",
            "Search for hidden runes",
            "Set up camp and rest"
        ]

    return input_state.copy(update={
        "current_scene": result,
        "available_actions": actions
    })


def action_input_node(input_state: GameState) -> GameState:
    print("\n🎲 Current Scene:")
    print(input_state.current_scene)

    print("\n🛡️ Available Actions:")
    for idx, action in enumerate(input_state.available_actions):
        print(f"{idx + 1}. {action}")

    # Get player's choice
    try:
        choice = int(input("\n👉 Choose an action (enter number): ")) - 1
        if choice < 0 or choice >= len(input_state.available_actions):
            print("❗ Invalid choice, selecting default (first option).")
            choice = 0
    except ValueError:
        print("❗ Invalid input, selecting default (first option).")
        choice = 0

    selected_action = input_state.available_actions[choice]

    return input_state.copy(update={
        "selected_action": selected_action
    })

from utils.dice_roller import roll_dice

def action_resolution_node(input_state: GameState) -> GameState:
    # Roll dice
    dice_result = roll_dice()
    roll_outcome = "success" if dice_result >= 10 else "failure"

    print(f"\n🎲 You rolled a {dice_result}! ({roll_outcome.upper()})")

    with open("prompts/action_resolution_prompt.txt", "r", encoding="utf-8") as file:
        raw_prompt = file.read()

    # Update prompt to include dice result
    prompt = PromptTemplate.from_template(raw_prompt)
    formatted_prompt = prompt.format(
        current_scene=input_state.current_scene,
        selected_action=input_state.selected_action,
        dice_roll=dice_result,
        roll_outcome=roll_outcome
        
    )

    # Call LLM
    result = model.invoke(formatted_prompt).content

    # After getting result
    new_actions = []

    # Find numbered list items (regex pattern)
    matches = re.findall(r'\d+\.\s(.+)', result)
    for action in matches:
        new_actions.append(action.strip())

    # 🎁 Chance to give loot if success
    updated_inventory = input_state.inventory
    if roll_outcome == "success" and dice_result >= 15:
        # Award an item!
        loot_items = ["Healing Potion", "Silver Sword", "Ancient Scroll", "Mystic Ring"]
        found_item = random.choice(loot_items)
        print(f"\n🎁 You found a {found_item}!")
        updated_inventory = add_item_to_inventory(updated_inventory, found_item)

    # 💥 Damage if fail
    updated_hp = input_state.health_points
    if roll_outcome == "failure":
        damage = random.randint(5, 15)
        updated_hp -= damage
        updated_hp = max(0, updated_hp)
        print(f"\n💥 You got hurt and lost {damage} HP! (Current HP: {updated_hp}/{input_state.max_health_points})")

        if updated_hp == 0:
            print("\n☠️ You have fallen in battle... Game Over!")

    # Prompt user for next action
    user_action = input("\n🎮 Choose your action (or type 'inventory' or 'use [item]'):\n> ").strip().lower()

    if user_action == "inventory":
        print("\n🎒 Your Inventory:")
        print(show_inventory(updated_inventory))
        return input_state.copy(update={
            "action_result": result,
            "new_available_actions": new_actions,
            "last_dice_roll": dice_result,
            "last_roll_outcome": roll_outcome,
            "inventory": updated_inventory,
            "health_points": updated_hp
        })

    elif user_action.startswith("use "):
        item_to_use = user_action.replace("use ", "").strip().title()

        if item_to_use in updated_inventory:
            print(f"\n🧪 You used {item_to_use}!")
            updated_inventory = remove_item_from_inventory(updated_inventory, item_to_use)

            if item_to_use == "Healing Potion":
                heal_amount = random.randint(10, 30)
                updated_hp += heal_amount
                updated_hp = min(updated_hp, input_state.max_health_points)
                print(f"❤️ You healed for {heal_amount} HP! (Current HP: {updated_hp}/{input_state.max_health_points})")

            # Optional: Apply item effects here (e.g., healing)
            return input_state.copy(update={
                "inventory": updated_inventory,
                "action_result": result,
                "new_available_actions": new_actions,
                "last_dice_roll": dice_result,
                "last_roll_outcome": roll_outcome,
                "health_points": updated_hp
            })
        else:
            print(f"\n⚠️ You don't have {item_to_use}!")
            return input_state.copy(update={
                "action_result": result,
                "new_available_actions": new_actions,
                "last_dice_roll": dice_result,
                "last_roll_outcome": roll_outcome,
                "inventory": updated_inventory,
                "health_points": updated_hp
            })

    # Default: continue to next node
    return input_state.copy(update={
        "action_result": result,
        "new_available_actions": new_actions,
        "last_dice_roll": dice_result,
        "last_roll_outcome": roll_outcome,
        "inventory": updated_inventory,
        "health_points": updated_hp
    })



from utils.elevenlabs_tts import text_to_speech_file

def voice_output_node(input_state: GameState) -> GameState:
    # 🚫 If previous failure, skip TTS
    if input_state.voice_output_disabled:
        return input_state
    
    try:
        text1 = (
            input_state.world_intro + "\n" +
            input_state.location_intro + "\n" +
            input_state.main_quest + "\n" +
            "\n".join(input_state.npcs)  # ✅ Fix: join list to string
        )
        text2 = (
            input_state.current_scene + "\n" +
            input_state.selected_action + "\n" +
            input_state.action_result
        )
        text3 = (
            input_state.last_roll_outcome + "\n" +
            str(input_state.last_dice_roll) + "\n" +    # ✅ Fix: cast int to str
            "\n".join(input_state.inventory) + "\n" +
            f"Health: {input_state.health_points} HP"
        )

        text4 = "\n".join(input_state.new_available_actions)  # ✅ Again join list of actions

        audio_file_path1 = text_to_speech_file(text1, "audio1.mp3")
        audio_file_path2 = text_to_speech_file(text2, "audio2.mp3")
        audio_file_path3 = text_to_speech_file(text3, "audio3.mp3")
        audio_file_path4 = text_to_speech_file(text4, "audio4.mp3")


        return input_state.copy(update={
            "audio_file_path1": audio_file_path1,
            "audio_file_path2": audio_file_path2,
            "audio_file_path3": audio_file_path3,
            "audio_file_path4": audio_file_path4
        })
    except Exception as e:
        print(f"🚨 Error in voice output: {e}")
        print("⚡ Disabling future voice output and continuing the game...")
        return input_state.copy(update={"voice_output_disabled": True})