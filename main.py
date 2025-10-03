"""
Pathfinder - Supply Chain Optimization Simulator

Author: Paul Gerber
Requirements: pandas, ortools, folium
"""

import pandas as pd
import random
import folium
from ortools.graph.python import min_cost_flow


def load_data():
    """Loads node and edge data from CSV files."""
    try:
        nodes = pd.read_csv('nodes.csv')
        edges = pd.read_csv('edges.csv')
        return nodes, edges
    except FileNotFoundError as e:
        print(f"CRITICAL: {e}. Ensure 'nodes.csv' and 'edges.csv' are present.")
        return None, None


def create_id_to_index_mapping(node_ids):
    """Creates a dict mapping string node IDs to integer indices."""
    return {id_str: i for i, id_str in enumerate(node_ids)}


def find_optimal_path_ortools(nodes_df, edges_df, start_node_id, end_node_id, weight_column):
    """Finds the optimal path using the OR-Tools Min-Cost Flow solver."""
    node_ids = list(nodes_df['id'])
    id_to_index = create_id_to_index_mapping(node_ids)

    start_node_index = id_to_index.get(start_node_id)
    end_node_index = id_to_index.get(end_node_id)
    if start_node_index is None or end_node_index is None:
        print(f"ERROR: Start or end node not found in nodes file.")
        return None, None

    smcf = min_cost_flow.SimpleMinCostFlow()

    for _, row in edges_df.iterrows():
        smcf.add_arc_with_capacity_and_unit_cost(
            id_to_index[row['source']], id_to_index[row['target']], 1, int(row[weight_column])
        )

    smcf.set_node_supply(start_node_index, 1)
    smcf.set_node_supply(end_node_index, -1)

    status = smcf.solve()

    if status == smcf.OPTIMAL:
        path = [start_node_id]
        current_node_idx = start_node_index
        total_cost = smcf.optimal_cost()
        while node_ids[current_node_idx] != end_node_id:
            for i in range(smcf.num_arcs()):
                if smcf.tail(i) == current_node_idx and smcf.flow(i) > 0:
                    next_node_idx = smcf.head(i)
                    path.append(node_ids[next_node_idx])
                    current_node_idx = next_node_idx
                    break
        return path, total_cost
    else:
        return None, None


def simulate_disruption(edges_df, optimal_path, disruption_factor=10):
    """Selects a random edge on the given path and multiplies its cost."""
    disrupted_edges = edges_df.copy()

    path_edges = list(zip(optimal_path[:-1], optimal_path[1:]))
    if not path_edges:
        print("WARNING: Cannot simulate disruption on an empty path.")
        return disrupted_edges

    on_path_indices = disrupted_edges[disrupted_edges.apply(
        lambda row: (row['source'], row['target']) in path_edges, axis=1
    )].index

    if on_path_indices.empty:
        print("WARNING: Path edges not found in data. Using random edge for disruption.")
        random_index = random.choice(disrupted_edges.index)
    else:
        random_index = random.choice(on_path_indices)

    original_cost = disrupted_edges.loc[random_index, 'cost_eur']
    disrupted_edges.loc[random_index, 'cost_eur'] = original_cost * disruption_factor

    info = disrupted_edges.loc[random_index]
    print("\nEVENT: TARGETED DISRUPTION 🎯")
    print(f"  Applying x{disruption_factor} cost multiplier to edge: {info['source']} -> {info['target']}")

    return disrupted_edges


def create_map(nodes_df, path, color, map_object=None, tooltip=""):
    """Draws nodes and a given path on a Folium map."""
    if map_object is None:
        map_object = folium.Map(location=[40, 0], zoom_start=2)

    for _, node in nodes_df.iterrows():
        folium.CircleMarker(
            location=[node['latitude'], node['longitude']],
            radius=5, popup=f"{node['name']} ({node['type']})",
            color='#3186cc', fill=True, fill_color='#3186cc'
        ).add_to(map_object)

    path_coords = [
        (nodes_df[nodes_df['id'] == node_id].iloc[0]['latitude'],
         nodes_df[nodes_df['id'] == node_id].iloc[0]['longitude'])
        for node_id in path
    ]

    folium.PolyLine(path_coords, color=color, weight=2.5, opacity=1, tooltip=tooltip).add_to(map_object)
    return map_object


def main():
    """Main execution function."""
    print("INFO: Initiating Pathfinder...")
    nodes_df, edges_df = load_data()
    if nodes_df is None or edges_df is None:
        print("CRITICAL: Halting execution due to data loading failure.")
        return

    suppliers = nodes_df[nodes_df['type'] == 'supplier']['id'].tolist()
    markets = nodes_df[nodes_df['type'] == 'market']['id'].tolist()
    start_node = random.choice(suppliers)
    end_node = random.choice(markets)

    print(f"\nINFO: Optimizing new random route from {start_node} to {end_node}.")

    print("\n--- Analysis: Normal Conditions ---")
    path_normal, cost_normal = find_optimal_path_ortools(nodes_df, edges_df, start_node, end_node, 'cost_eur')
    if path_normal:
        print(f"  Optimal Path: {' -> '.join(path_normal)}")
        print(f"  Total Cost: {cost_normal} EUR")

        disrupted_edges_df = simulate_disruption(edges_df, path_normal)

        print("\n--- Analysis: Post-Disruption ---")
        path_disrupted, cost_disrupted = find_optimal_path_ortools(nodes_df, disrupted_edges_df, start_node, end_node, 'cost_eur')

        if path_disrupted:
            print(f"  New Optimal Path: {' -> '.join(path_disrupted)}")
            print(f"  New Total Cost: {cost_disrupted} EUR")
            print(f"  Impact: Cost increased by {cost_disrupted - cost_normal} EUR.")

            print("\nINFO: Generating visualization...")
            map_object = create_map(nodes_df, path_normal, color='blue', tooltip=f"Normal Route: {cost_normal} EUR")
            create_map(nodes_df, path_disrupted, color='red', map_object=map_object, tooltip=f"Disrupted Route: {cost_disrupted} EUR")

            map_filename = 'supply_chain_map.html'
            map_object.save(map_filename)
            print(f"SUCCESS: Map saved to '{map_filename}'")
    else:
        print(f"INFO: No path found from {start_node} to {end_node}.")


if __name__ == "__main__":
    main()