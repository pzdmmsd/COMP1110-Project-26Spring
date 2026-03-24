from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .edge import Edge

class Node:
    """
    A node on the campus map.
    """

    def __init__(self, node_id: str, description: str = None):
        """
        Constructor. Creates a new Node instance.
        :param node_id: The ID of the Node.
        :param description: The description of the Node. Can be empty.
        """
        self.node_id: str = node_id
        """
        The ID of the Node.
        """
        self.description: str = description if description is not None else ""
        """
        The description of the Node. Can be empty.
        """

        # private, modifications should be done through add_edge() and remove_edge()
        self._edges: list[Edge] = []

    def get_edges(self) -> list[Edge]:
        """
        Returns a copy of the list of edges that are incident to this node.
        :return: A copy of the list of edges that are incident to this node.
        """
        return self._edges.copy()

    def add_edge(self, edge: Edge) -> None:
        """
        Adds an edge to the list of edges incident to this node.
        **IMPORTANT: This method should only be called by the Edge class internally.**
        :param edge: The edge that is incident to this node.
        """
        self._edges.append(edge)

    def remove_edge(self, edge: Edge) -> None:
        """
        Removes an edge from the list of edges incident to this node.
        The edge will also be removed from the other node that is incident to the edge.
        **IMPORTANT: This method should only be called by the CampusMap class internally.**
        :param edge: The edge to be removed.
        """
        self._edges.remove(edge)
        other_node = edge.node2 if edge.node1 == self else edge.node1
        other_node._edges.remove(edge)