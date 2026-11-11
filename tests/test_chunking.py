import pytest

from src.chunking import chunk_text


def test_hand_example():
    assert chunk_text("abcdefghij", size=4, overlap=1) == ["abcd", "defg", "ghij"]

def test_empty_text():
    assert chunk_text("", size=4, overlap=1) == []


def test_shorter_than_size():
    assert chunk_text("abc", size=10, overlap=2) == ["abc"]


def test_exactly_size():
    assert chunk_text("abcd", size=4, overlap=1) == ["abcd"]


def test_no_redundant_tail():
    assert chunk_text("abcdefg", size=4, overlap=2) == ["abcd", "cdef", "efg"]


def test_bad_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", size=4, overlap=4)


def test_overlap_is_shared():
    size=4
    overlap=2
    chunks =  chunk_text("abcdefg", size, overlap)
    assert chunks[0][size-overlap:]== chunks[1][:overlap]
    