from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Wagon:
    wagon_id: str
    cargo: str
    destination: str
    weight_tonnes: float

    def __post_init__(self) -> None:
        for field_name in ("wagon_id", "cargo", "destination"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty.")
            object.__setattr__(self, field_name, value.strip())

        try:
            weight = float(self.weight_tonnes)
        except (TypeError, ValueError) as error:
            raise ValueError("weight_tonnes must be a positive number.") from error

        if weight <= 0:
            raise ValueError("weight_tonnes must be a positive number.")
        object.__setattr__(self, "weight_tonnes", weight)

    def to_dict(self) -> dict[str, str | float]:
        return asdict(self)
