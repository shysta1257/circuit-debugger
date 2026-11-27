"""Breadboard geometry and internal connectivity.

A standard solderless breadboard has two kinds of strips:

* **Terminal strips**: the middle area. Each numbered column is split by the centre
  gap into two groups of five holes: rows ``a``-``e`` and rows ``f``-``j``. The five
  holes in one group are connected to each other.
* **Power rails**: long strips along the top and bottom edges, each with a ``+`` and a
  ``-`` line. Every hole on one rail line is connected along the whole board (unless
  the board has split rails, in which case the left and right halves are separate).

Holes are named the way they are printed on the board:

* terminal holes: ``"a1"``, ``"j63"`` (row letter + column number)
* rail holes: ``"T+5"``, ``"T-5"``, ``"B+12"``, ``"B-12"`` (Top/Bottom, polarity, position)

Each hole belongs to exactly one *node*: the set of holes that are electrically joined
inside the breadboard. Nodes are what the netlist builder works with.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TOP_ROWS = "abcde"
BOTTOM_ROWS = "fghij"
ROWS = TOP_ROWS + BOTTOM_ROWS
RAIL_SIDES = ("T", "B")
RAIL_POLARITIES = ("+", "-")

_TERMINAL_RE = re.compile(r"^([a-j])(\d+)$")
_RAIL_RE = re.compile(r"^([TB])([+-])(\d+)$")


class InvalidHoleError(ValueError):
    """Raised when a hole name is malformed or outside the board."""


@dataclass(frozen=True, order=True)
class Hole:
    """A single hole on the breadboard.

    ``kind`` is ``"terminal"`` or ``"rail"``. For terminal holes ``row`` is a letter
    ``a``-``j``; for rail holes it is ``"T+"``, ``"T-"``, ``"B+"`` or ``"B-"``.
    ``column`` is 1-based.
    """

    kind: str
    row: str
    column: int

    @property
    def name(self) -> str:
        return f"{self.row}{self.column}"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Breadboard:
    """Geometry of a breadboard.

    Defaults match a common full-size board: 63 terminal columns and 50-hole rails.
    Set ``split_rails=True`` for boards whose power rails are broken in the middle.
    """

    columns: int = 63
    rail_length: int = 50
    split_rails: bool = False

    def __post_init__(self) -> None:
        if self.columns < 1 or self.rail_length < 1:
            raise ValueError("columns and rail_length must be positive")

    # --- parsing -----------------------------------------------------------------

    def hole(self, name: str) -> Hole:
        """Parse a hole name such as ``"a12"`` or ``"T+3"`` and validate it."""
        text = name.strip()
        if m := _TERMINAL_RE.match(text):
            row, col = m.group(1), int(m.group(2))
            if not 1 <= col <= self.columns:
                raise InvalidHoleError(f"column {col} out of range 1-{self.columns}: {name!r}")
            return Hole("terminal", row, col)
        if m := _RAIL_RE.match(text):
            row, pos = m.group(1) + m.group(2), int(m.group(3))
            if not 1 <= pos <= self.rail_length:
                raise InvalidHoleError(
                    f"rail position {pos} out of range 1-{self.rail_length}: {name!r}"
                )
            return Hole("rail", row, pos)
        raise InvalidHoleError(f"not a valid hole name: {name!r}")

    # --- connectivity ------------------------------------------------------------

    def node_of(self, hole: Hole | str) -> str:
        """Return the id of the internal node this hole belongs to.

        Node ids:

        * ``"col12-top"`` / ``"col12-bottom"`` for terminal groups
        * ``"rail-T+"`` for a full rail, or ``"rail-T+-left"`` / ``"rail-T+-right"``
          when rails are split
        """
        h = self.hole(hole) if isinstance(hole, str) else hole
        if h.kind == "terminal":
            half = "top" if h.row in TOP_ROWS else "bottom"
            return f"col{h.column}-{half}"
        if self.split_rails:
            side = "left" if h.column <= (self.rail_length + 1) // 2 else "right"
            return f"rail-{h.row}-{side}"
        return f"rail-{h.row}"

    def connected(self, a: Hole | str, b: Hole | str) -> bool:
        """True if two holes are joined inside the breadboard itself."""
        return self.node_of(a) == self.node_of(b)

    def holes_in_node(self, node: str) -> list[Hole]:
        """All holes that belong to a node id (inverse of :meth:`node_of`)."""
        return [h for h in self.all_holes() if self.node_of(h) == node]

    def all_holes(self) -> list[Hole]:
        holes = [Hole("terminal", r, c) for c in range(1, self.columns + 1) for r in ROWS]
        holes += [
            Hole("rail", s + p, i)
            for s in RAIL_SIDES
            for p in RAIL_POLARITIES
            for i in range(1, self.rail_length + 1)
        ]
        return holes

    def all_nodes(self) -> list[str]:
        return sorted({self.node_of(h) for h in self.all_holes()})

    @staticmethod
    def is_rail_node(node: str) -> bool:
        return node.startswith("rail-")

    @staticmethod
    def rail_polarity(node: str) -> str | None:
        """``"+"`` or ``"-"`` for a rail node, ``None`` for a terminal node."""
        if not node.startswith("rail-"):
            return None
        return node[6]

    def spans_centre_gap(self, a: Hole | str, b: Hole | str) -> bool:
        """True if two terminal holes sit on opposite sides of the centre gap."""
        ha = self.hole(a) if isinstance(a, str) else a
        hb = self.hole(b) if isinstance(b, str) else b
        if ha.kind != "terminal" or hb.kind != "terminal":
            return False
        return (ha.row in TOP_ROWS) != (hb.row in TOP_ROWS)
