from datetime import datetime, date
from src.components.base import ControlComponent


def check_completeness(data, required_fields, allow_empty_string=False, **kwargs):
    """
    Check dataset for missing, null, or blank values in required fields.

    Returns:
        {
            "status": "PASS" | "BREACH",
            "breach_count": int,
            "breaches": list
        }
    """
    breaches = []

    for index, row in enumerate(data):
        for field in required_fields:
            if field not in row:
                breaches.append({
                    "row_index": index,
                    "field": field,
                    "type": "MISSING_FIELD",
                    "message": f"Field '{field}' missing from record",
                    "record": row
                })
            elif row[field] is None:
                breaches.append({
                    "row_index": index,
                    "field": field,
                    "type": "NULL_VALUE",
                    "message": f"Field '{field}' is NULL",
                    "record": row
                })
            elif not allow_empty_string and isinstance(row[field], str) and row[field].strip() == "":
                breaches.append({
                    "row_index": index,
                    "field": field,
                    "type": "EMPTY_STRING",
                    "message": f"Field '{field}' is empty string",
                    "record": row
                })

    return {
        "status": "PASS" if not breaches else "BREACH",
        "breach_count": len(breaches),
        "breaches": breaches
    }


def check_referential_integrity(source, lookup, foreign_key, primary_key=None, **kwargs):
    """
    Ensure foreign key values in source dataset exist in parent lookup dataset.

    Returns:
        {
            "status": "PASS" | "BREACH",
            "breach_count": int,
            "breaches": list
        }
    """
    if primary_key is None:
        primary_key = foreign_key

    # Support single string or list of composite keys
    if isinstance(primary_key, str):
        pk_keys = [primary_key]
        fk_keys = [foreign_key]
    else:
        pk_keys = list(primary_key)
        fk_keys = list(foreign_key)

    # Build set of valid parent keys
    lookup_keys = set()
    for row in lookup:
        key_tuple = tuple(row.get(k) for k in pk_keys)
        if None not in key_tuple:
            lookup_keys.add(key_tuple if len(key_tuple) > 1 else key_tuple[0])

    breaches = []
    for index, row in enumerate(source):
        key_tuple = tuple(row.get(k) for k in fk_keys)
        actual_key = key_tuple if len(key_tuple) > 1 else key_tuple[0]

        if actual_key not in lookup_keys:
            breaches.append({
                "row_index": index,
                "type": "ORPHAN_RECORD",
                "foreign_key_fields": fk_keys,
                "foreign_key_value": actual_key,
                "message": f"Foreign key {actual_key} does not exist in target reference dataset",
                "record": row
            })

    return {
        "status": "PASS" if not breaches else "BREACH",
        "breach_count": len(breaches),
        "breaches": breaches
    }


def check_staleness(data, timestamp_field, as_of_date, max_age_days=1, date_format="%Y-%m-%d", **kwargs):
    """
    Ensure timestamps in data are within allowed max_age_days threshold relative to as_of_date.

    Returns:
        {
            "status": "PASS" | "BREACH",
            "breach_count": int,
            "breaches": list
        }
    """
    if isinstance(as_of_date, str):
        ref_dt = datetime.strptime(as_of_date, date_format).date()
    elif isinstance(as_of_date, datetime):
        ref_dt = as_of_date.date()
    elif isinstance(as_of_date, date):
        ref_dt = as_of_date
    else:
        raise ValueError("as_of_date must be a date, datetime, or formatted string")

    breaches = []
    for index, row in enumerate(data):
        raw_val = row.get(timestamp_field)
        if raw_val is None:
            breaches.append({
                "row_index": index,
                "type": "MISSING_TIMESTAMP",
                "field": timestamp_field,
                "message": f"Timestamp field '{timestamp_field}' is missing or null",
                "record": row
            })
            continue

        if isinstance(raw_val, str):
            try:
                rec_dt = datetime.strptime(raw_val, date_format).date()
            except ValueError:
                # Try ISO format
                rec_dt = datetime.fromisoformat(raw_val.replace("Z", "+00:00")).date()
        elif isinstance(raw_val, datetime):
            rec_dt = raw_val.date()
        elif isinstance(raw_val, date):
            rec_dt = raw_val
        else:
            raise ValueError(f"Unrecognized date type for {raw_val}")

        age_days = (ref_dt - rec_dt).total_seconds() / 86400.0

        if age_days > max_age_days:
            breaches.append({
                "row_index": index,
                "type": "STALE_DATA",
                "field": timestamp_field,
                "record_date": str(rec_dt),
                "as_of_date": str(ref_dt),
                "age_days": round(age_days, 2),
                "max_age_days": max_age_days,
                "message": f"Data is {round(age_days, 2)} days old (max allowed: {max_age_days} days)",
                "record": row
            })

    return {
        "status": "PASS" if not breaches else "BREACH",
        "breach_count": len(breaches),
        "breaches": breaches
    }


class CompletenessControl(ControlComponent):
    def __init__(self, version="1.0"):
        super().__init__(name="quality.completeness", version=version)

    def execute(self, data):
        return check_completeness(**data)


class ReferentialIntegrityControl(ControlComponent):
    def __init__(self, version="1.0"):
        super().__init__(name="quality.referential_integrity", version=version)

    def execute(self, data):
        return check_referential_integrity(**data)


class StalenessControl(ControlComponent):
    def __init__(self, version="1.0"):
        super().__init__(name="quality.staleness", version=version)

    def execute(self, data):
        return check_staleness(**data)
