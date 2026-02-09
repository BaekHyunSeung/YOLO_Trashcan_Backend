def class_id_to_type_name(class_id: int) -> str | None:
    mapping = {
        0: "MetalCan",
        1: "PetBottle",
        2: "Plastic",
        3: "Styrofoam",
    }
    return mapping.get(class_id)