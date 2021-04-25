def enum_value_to_enum(value, enum):
    d = {e.value: e for e in enum}
    return d[value]

