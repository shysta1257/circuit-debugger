import pytest

from circuit_debugger.breadboard import Breadboard, Hole, InvalidHoleError


@pytest.fixture
def board() -> Breadboard:
    return Breadboard()


def test_parse_terminal_hole(board):
    assert board.hole("c17") == Hole("terminal", "c", 17)


def test_parse_rail_hole(board):
    assert board.hole("B-4") == Hole("rail", "B-", 4)


def test_hole_name_round_trips(board):
    for name in ["a1", "j63", "T+1", "B-50"]:
        assert board.hole(name).name == name


@pytest.mark.parametrize("name", ["k1", "a0", "a64", "T+51", "X+1", "", "1a", "T*3"])
def test_invalid_holes_rejected(board, name):
    with pytest.raises(InvalidHoleError):
        board.hole(name)


def test_same_column_same_half_is_connected(board):
    assert board.connected("a5", "e5")


def test_centre_gap_separates_halves(board):
    assert not board.connected("e5", "f5")
    assert board.connected("f5", "j5")


def test_neighbouring_columns_not_connected(board):
    assert not board.connected("a5", "a6")


def test_full_rail_is_connected_end_to_end(board):
    assert board.connected("T+1", "T+50")


def test_rail_polarities_and_sides_are_separate(board):
    assert not board.connected("T+1", "T-1")
    assert not board.connected("T+1", "B+1")


def test_split_rails():
    board = Breadboard(split_rails=True)
    assert board.connected("T+1", "T+25")
    assert not board.connected("T+25", "T+26")


def test_node_counts(board):
    # 63 columns x 2 halves + 4 rail lines
    assert len(board.all_nodes()) == 63 * 2 + 4
    assert len(Breadboard(split_rails=True).all_nodes()) == 63 * 2 + 8


def test_holes_in_node(board):
    names = {h.name for h in board.holes_in_node("col3-bottom")}
    assert names == {"f3", "g3", "h3", "i3", "j3"}


def test_rail_helpers(board):
    assert board.is_rail_node(board.node_of("B-7"))
    assert board.rail_polarity(board.node_of("B-7")) == "-"
    assert board.rail_polarity(board.node_of("a1")) is None


def test_spans_centre_gap(board):
    assert board.spans_centre_gap("e10", "f10")
    assert not board.spans_centre_gap("a10", "e12")
    assert not board.spans_centre_gap("e10", "T+3")


def test_custom_size():
    small = Breadboard(columns=30, rail_length=25)
    small.hole("a30")
    with pytest.raises(InvalidHoleError):
        small.hole("a31")
