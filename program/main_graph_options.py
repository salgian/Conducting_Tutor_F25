"""
graph_options.py

This module provides functions for selecting and managing graph generation options.
"""

def print_checkbox_menu(options):
    """Display a checkbox menu for options"""
    print("\n=== Graph Selection Menu ===")
    print("Select which graphs to generate:")
    for i, (key, value) in enumerate(options.items(), 1):
        status = "[X]" if value else "[ ]"
        print(f"{i}. {status} {key.replace('generate_', '').replace('_', ' ').title()}")
    print("\nEnter the number to toggle selection, or 'c' to continue: ")


def get_checkbox_input(options):
    """Get user input for checkbox menu"""
    keys = list(options.keys())
    while True:
        choice = input("> ").strip().lower()
        if choice == 'c':
            return options
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                options[key] = not options[key]
                print_checkbox_menu(options)
            else:
                print(f"Please enter a number between 1 and {len(keys)}, or 'c' to continue")
        except ValueError:
            print("Please enter a number or 'c' to continue")


def select_graph_options():
    """Interactive menu for selecting graph options"""
    options = {
        "generate_beat_plot": True,
        "generate_hand_path": True,
        "generate_cluster_graph": True,
        "generate_overtime_graph": True,
        "generate_swaying_graph": True,
        "generate_mirror_x_graph": True,
        "generate_mirror_y_graph": True
    }
    
    print_checkbox_menu(options)
    return get_checkbox_input(options) 