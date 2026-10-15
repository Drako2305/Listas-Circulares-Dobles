import unittest

from trainyard.circular_list import DoublyCircularWagonList
from trainyard.models import Wagon


def wagon(wagon_id: str) -> Wagon:
    return Wagon(wagon_id, "Mineral", "North Yard", 42)


class DoublyCircularWagonListTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wagons = DoublyCircularWagonList()

    def test_single_wagon_loops_in_both_directions(self) -> None:
        self.wagons.append(wagon("W-01"))
        self.assertEqual(self.wagons.move("next"), wagon("W-01"))
        self.assertEqual(self.wagons.move("previous"), wagon("W-01"))

    def test_append_and_traverse_in_both_directions(self) -> None:
        for wagon_id in ("W-01", "W-02", "W-03"):
            self.wagons.append(wagon(wagon_id))
        self.assertEqual(
            [item.wagon_id for item in self.wagons.wagons()],
            ["W-01", "W-02", "W-03"],
        )
        self.assertEqual(
            [item.wagon_id for item in self.wagons.wagons("previous")],
            ["W-03", "W-02", "W-01"],
        )
        self.assertEqual(self.wagons.move("previous"), wagon("W-03"))
        self.assertEqual(self.wagons.move("next"), wagon("W-01"))

    def test_appending_does_not_change_the_selected_wagon(self) -> None:
        self.wagons.append(wagon("W-01"))
        self.wagons.append(wagon("W-02"))
        self.wagons.move("next")
        self.wagons.append(wagon("W-03"))
        self.assertEqual(self.wagons.current, wagon("W-02"))

    def test_removing_current_selects_next_and_keeps_links_circular(self) -> None:
        for wagon_id in ("W-01", "W-02", "W-03"):
            self.wagons.append(wagon(wagon_id))
        self.wagons.move("next")
        self.assertEqual(self.wagons.remove("W-02"), wagon("W-02"))
        self.assertEqual(self.wagons.current, wagon("W-03"))
        self.assertEqual(self.wagons.move("next"), wagon("W-01"))
        self.assertEqual(len(self.wagons), 2)

    def test_removing_last_wagon_leaves_empty_list(self) -> None:
        self.wagons.append(wagon("W-01"))
        self.assertEqual(self.wagons.remove("W-01"), wagon("W-01"))
        self.assertEqual(len(self.wagons), 0)
        self.assertIsNone(self.wagons.current)
        self.assertIsNone(self.wagons.move("next"))

    def test_duplicate_ids_and_missing_removals_are_rejected(self) -> None:
        self.wagons.append(wagon("W-01"))
        with self.assertRaises(ValueError):
            self.wagons.append(wagon("W-01"))
        with self.assertRaises(KeyError):
            self.wagons.remove("W-99")

    def test_wagon_requires_valid_data(self) -> None:
        with self.assertRaises(ValueError):
            Wagon("W-01", "Mineral", "North Yard", 0)


if __name__ == "__main__":
    unittest.main()
