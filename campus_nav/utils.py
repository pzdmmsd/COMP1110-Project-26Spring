import csv
from pathlib import Path

from .models import *

NODES_CSV_PATH = "data/NODES.csv"
NODES_CSV_GOOGLE_SHEET_GID = "1774115251"
EDGES_CSV_PATH = "data/EDGES.csv"
EDGES_CSV_GOOGLE_SHEET_GID = "171496836"
GOOGLE_SHEETS_ID = "2PACX-1vRUqgKeU2uVyHsbVwYAIsMW-OqxgqaBB-GGY8w4thwaozPplOu1bN5rJgLzUPufFrIWL8p-QdaMI4Np"

def construct_map_from_csv(nodes_file: str = None, edges_file: str = None) -> CampusMap:
    """
    Constructs a CampusMap object from the given CSV files containing nodes and edges information.
    :param nodes_file: The path to the CSV file containing nodes information. If None, it defaults to NODES_CSV_PATH.
    :param edges_file: The path to the CSV file containing edges information. If None, it defaults to EDGES_CSV_PATH.
    :return: The constructed CampusMap object.
    """
    if nodes_file is None: nodes_file = Path(__file__).resolve().parent / NODES_CSV_PATH
    if edges_file is None: edges_file = Path(__file__).resolve().parent / EDGES_CSV_PATH

    campus_map: CampusMap = CampusMap()

    # Read nodes
    nodes_col_keys = ["node_id", "node_description"]
    with open(str(nodes_file), mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            node_id, node_description = (row[key] for key in nodes_col_keys)
            campus_map.add_node(Node(node_id, node_description))

    # Read edges
    edges_col_keys = ["node_1_id", "node_2_id", "edge_type", "time_cost"]
    with open(str(edges_file), mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            node1_id, node2_id, edge_type, edge_time_cost = (row[key] for key in edges_col_keys)
            edge_type = EdgeType(edge_type)
            edge_time_cost = int(edge_time_cost)
            campus_map.add_edge(node1_id, node2_id, edge_type, edge_time_cost)
    return campus_map

def fetch_csv_from_google_sheet(nodes_csv_path: str = None, edges_csv_path: str = None) -> None:
    """
    Fetches the NODES and EDGES CSV data from the Google Sheets and saves them to the specified paths.
    Existing files will be overwritten.
    :param nodes_csv_path: The path to save the NODES CSV file. If None, it defaults to NODES_CSV_PATH.
    :param edges_csv_path: The path to save the EDGES CSV file. If None, it defaults to EDGES_CSV_PATH.
    """
    url_format = "https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub?gid={GID}&single=true&output=csv"
    if nodes_csv_path is None: nodes_csv_path = Path(__file__).resolve().parent / NODES_CSV_PATH
    if edges_csv_path is None: edges_csv_path = Path(__file__).resolve().parent / EDGES_CSV_PATH

    nodes_csv_url = url_format.format(SHEET_ID=GOOGLE_SHEETS_ID, GID=NODES_CSV_GOOGLE_SHEET_GID)
    edges_csv_url = url_format.format(SHEET_ID=GOOGLE_SHEETS_ID, GID=EDGES_CSV_GOOGLE_SHEET_GID)

    import requests
    # Fetch and save NODES CSV
    response = requests.get(nodes_csv_url)
    response.raise_for_status()  # Check if the request was successful
    with open(nodes_csv_path, 'wb') as f:
        f.write(response.content)

    # Fetch and save EDGES CSV
    response = requests.get(edges_csv_url)
    response.raise_for_status()  # Check if the request was successful
    with open(edges_csv_path, 'wb') as f:
        f.write(response.content)
