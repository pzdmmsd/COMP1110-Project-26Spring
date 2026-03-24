from enum import StrEnum

class EdgeType(StrEnum):
    """
    The type of edge between two nodes.
    """
    FLAT = "FLAT"
    STAIRS = "STAIRS"
    MINOR_STAIRS = "MINOR_STAIRS"
    ESCALATOR = "ESCALATOR"
    LIFT = "LIFT"