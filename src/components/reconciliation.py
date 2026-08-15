from src.components.base import ControlComponent


def two_way_match(
    source,
    target,
    keys,
    compare,
    tolerance,
):
    """
    Compare source and target records using configurable keys
    and field-level tolerances.

    Returns:
        {
            "status": "PASS" or "BREACH",
            "breach_count": int,
            "breaches": list
        }
    """

    # Create lookup dictionaries using reconciliation keys.
    source_lookup = {
        tuple(row[key] for key in keys): row
        for row in source
    }

    target_lookup = {
        tuple(row[key] for key in keys): row
        for row in target
    }

    breaches = []

    # Check records existing in either source or target.
    all_keys = set(source_lookup) | set(target_lookup)

    for key in all_keys:

        source_row = source_lookup.get(key)
        target_row = target_lookup.get(key)

        # Missing from source
        if source_row is None:
            breaches.append(
                {
                    "key": key,
                    "type": "MISSING_SOURCE",
                }
            )
            continue

        # Missing from target
        if target_row is None:
            breaches.append(
                {
                    "key": key,
                    "type": "MISSING_TARGET",
                }
            )
            continue

        # Compare configured fields.
        for field in compare:

            source_value = source_row[field]
            target_value = target_row[field]

            difference = abs(source_value - target_value)

            field_tolerance = tolerance.get(field, {})

            absolute_tolerance = field_tolerance.get(
                "absolute",
                0,
            )

            relative_tolerance = field_tolerance.get(
                "relative",
                0,
            )

            # Relative tolerance is calculated against
            # the source value.
            if source_value != 0:
                relative_difference = (
                    difference / abs(source_value)
                )
            else:
                relative_difference = (
                    float("inf")
                    if difference != 0
                    else 0
                )

            within_absolute = (
                difference <= absolute_tolerance
            )

            within_relative = (
                relative_difference <= relative_tolerance
            )

            if not (
                within_absolute
                or within_relative
            ):
                breaches.append(
                    {
                        "key": key,
                        "type": "VALUE_MISMATCH",
                        "field": field,
                        "source_value": source_value,
                        "target_value": target_value,
                        "difference": difference,
                    }
                )

    return {
        "status": (
            "PASS"
            if not breaches
            else "BREACH"
        ),
        "breach_count": len(breaches),
        "breaches": breaches,
    }


class TwoWayMatchControl(ControlComponent):
    def __init__(self, version="1.0"):
        super().__init__(
            name="reconciliation.two_way_match",
            version=version,
        )

    def execute(self, data):
        return two_way_match(**data)