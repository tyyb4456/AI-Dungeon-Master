# 📄 utils/player_stats.py

def display_player_stats(game_state):
    print("\n" + "="*30)
    print("🧝‍♂️ PLAYER STATS")
    print("="*30)
    print(f"🎖️ Level: {game_state.level}")
    print(f"⚡ XP: {game_state.experience_points}")
    print(f"❤️ HP: {game_state.player_hp}/{game_state.max_hp}")
    
    print("\n🎒 Inventory:")
    if game_state.inventory:
        for item in game_state.inventory:
            print(f"- {item}")
    else:
        print("- (Empty)")
    
    print("="*30 + "\n")
    return game_state