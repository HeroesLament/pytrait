import pytest

from examples.basics import Sheep

@pytest.fixture
def dolly() -> Sheep:
    """A fixture providing a fresh Sheep instance named Dolly."""
    return Sheep(_name="Dolly")


def test_sheep_talk(dolly, capsys):
    """Ensure that Sheep.talk() prints the expected output."""
    dolly.talk()
    captured = capsys.readouterr()
    assert "Dolly pauses briefly... baaaaah!" in captured.out


def test_sheep_shear(dolly, capsys):
    """
    Check that Sheep.shear() modifies the 'naked' state,
    and that subsequent 'talk()' changes output.
    """
    # Initial talk
    dolly.talk()
    captured_initial = capsys.readouterr()
    assert "Dolly pauses briefly... baaaaah!" in captured_initial.out
    assert dolly.is_naked() is False

    # Shear Dolly
    dolly.shear()
    captured_shear = capsys.readouterr()
    # After shearing, Dolly is now naked
    assert "Dolly gets a haircut!" in captured_shear.out
    assert dolly.is_naked() is True

    # Talk again, ensure different noise
    dolly.talk()
    captured_after = capsys.readouterr()
    # Now Dolly's noise() should be "baaaaah?"
    assert "Dolly pauses briefly... baaaaah?" in captured_after.out
