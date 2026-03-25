"""Tests for server.fill_cars -- AI opponent generation from rival pool."""
from server.fill_cars import generate_fill_cars


def test_generate_fill_cars_returns_requested_count():
    cars = generate_fill_cars(5)
    assert len(cars) == 5


def test_fill_cars_have_required_fields():
    cars = generate_fill_cars(3)
    for car in cars:
        assert "name" in car
        assert "color" in car
        assert car["player_id"] == "ai"
        assert car["car_id"] is None
        assert "_car_dict" in car


def test_fill_cars_have_unique_names():
    cars = generate_fill_cars(10)
    names = [c["name"] for c in cars]
    assert len(names) == len(set(names))


def test_fill_cars_exclude_names():
    cars = generate_fill_cars(5, exclude_names=["GlassCanon", "BrickHouse"])
    names = [c["name"] for c in cars]
    assert "GlassCanon" not in names
    assert "BrickHouse" not in names


def test_fill_cars_reproducible_with_seed():
    cars1 = generate_fill_cars(5, seed=42)
    cars2 = generate_fill_cars(5, seed=42)
    assert [c["name"] for c in cars1] == [c["name"] for c in cars2]


def test_fill_max_19():
    """Can fill up to 19 (all available rivals)."""
    cars = generate_fill_cars(19)
    assert len(cars) == 19
