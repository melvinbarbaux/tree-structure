import os
import argparse
import json
import pydot

def build_tree(directory, show_hidden=False, max_depth=None, current_depth=0):
    """
    Constructs the directory tree as a dictionary.

    Args:
        directory (str): Path to the directory to traverse.
        show_hidden (bool, optional): Whether to show hidden files/directories. Defaults to False.
        max_depth (int or None, optional): Maximum depth to explore (None for unlimited depth). Defaults to None.
        current_depth (int, optional): Current depth (used internally for recursion). Defaults to 0.

    Returns:
        dict or str: Directory tree or a message indicating that the maximum depth has been reached.
    """
    if max_depth is not None and current_depth >= max_depth:
        return "... (maximum depth reached)"
    
    tree = {}
    try:
        for item in sorted(os.listdir(directory)):
            # Ignore hidden files/directories if show_hidden is False
            if not show_hidden and item.startswith('.'):
                continue
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                tree[item] = build_tree(full_path, show_hidden, max_depth, current_depth + 1)
            else:
                tree[item] = None
    except PermissionError:
        tree["🚫 Access Denied"] = None
    return tree

def display_tree(tree, prefix=""):
    """
    Displays the directory tree in the terminal as a visual tree.

    Args:
        tree (dict or str): Directory tree to display.
        prefix (str, optional): Prefix for formatting (used recursively). Defaults to "".
    """
    if isinstance(tree, dict):
        for i, (name, content) in enumerate(tree.items()):
            # Choose the symbol based on position
            symbol = "├── " if i < len(tree) - 1 else "└── "
            print(prefix + symbol + name)
            if isinstance(content, dict):
                new_prefix = prefix + ("│   " if i < len(tree) - 1 else "    ")
                display_tree(content, new_prefix)
            elif isinstance(content, str):
                print(prefix + "    " + content)
    else:
        print(prefix + str(tree))

def add_nodes_edges_from_tree(tree, parent_id, graph):
    """
    Recursively adds nodes and edges to the pydot graph from the directory tree.

    Args:
        tree (dict): Directory tree.
        parent_id (str): Unique identifier of the parent node.
        graph (pydot.Dot): Pydot graph to which nodes and edges are added.
    """
    for name, child in tree.items():
        child_id = f"{parent_id}/{name}"
        node = pydot.Node(child_id, label=name, shape='box')
        graph.add_node(node)
        graph.add_edge(pydot.Edge(parent_id, child_id))
        if isinstance(child, dict):
            add_nodes_edges_from_tree(child, child_id, graph)
        elif isinstance(child, str):
            # Add a leaf node indicating depth limit
            leaf_id = f"{child_id}_leaf"
            leaf_node = pydot.Node(leaf_id, label=child, shape='ellipse')
            graph.add_node(leaf_node)
            graph.add_edge(pydot.Edge(child_id, leaf_id))
        # If child is None, it is a file without sub-elements

def generate_tree_image(tree, root_label, output_path):
    """
    Generates a PNG image representing the directory tree.

    Args:
        tree (dict): Directory tree.
        root_label (str): Label of the root node (root directory name).
        output_path (str): Output path for the PNG image.
    """
    # Create a directed graph with a top-to-bottom layout
    graph = pydot.Dot(graph_type='digraph', rankdir="TB")
    
    # Create the root node
    root_id = root_label
    root_node = pydot.Node(root_id, label=root_label, shape='box')
    graph.add_node(root_node)
    
    # Recursively add nodes and edges
    add_nodes_edges_from_tree(tree, root_id, graph)
    
    # Save the image as PNG
    graph.write_png(output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Displays a directory tree in the terminal, saves the tree as JSON, and generates a PNG image."
    )
    parser.add_argument("directory", type=str, help="Path to the directory to analyze")
    parser.add_argument("--show-hidden", action="store_true", default=False,
                        help="Show hidden files and directories (default: no)")
    parser.add_argument("--max-depth", type=int, default=None,
                        help="Maximum depth to explore (no limit by default)")
    args = parser.parse_args()

    directory_to_explore = os.path.abspath(args.directory)
    if not os.path.exists(directory_to_explore):
        print(f"❌ Error: The directory '{directory_to_explore}' does not exist.")
        exit(1)

    # Build the directory tree
    tree = build_tree(directory_to_explore, show_hidden=args.show_hidden, max_depth=args.max_depth)

    # Display the directory tree in the terminal
    print(f"\n📁 Directory Tree: {directory_to_explore}\n")
    display_tree(tree)

    # Save the directory tree as JSON
    json_filename = os.path.join(directory_to_explore, "directory_tree.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=4, ensure_ascii=False)
    print(f"\n📄 The directory tree has been saved as '{json_filename}'")

    # Generate a PNG image of the directory tree
    # The root node will have the label of the directory name or full path if empty
    root_label = os.path.basename(directory_to_explore) or directory_to_explore
    png_filename = os.path.join(directory_to_explore, "directory_tree.png")
    generate_tree_image(tree, root_label, png_filename)
    print(f"\n🖼️ The tree image has been saved as '{png_filename}'")