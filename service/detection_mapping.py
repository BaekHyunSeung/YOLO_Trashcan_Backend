def camera_to_trashcan_id(camera_id: str) -> int:
    mapping = {"CAM_0": 1, "CAM_1": 2, "CAM_2": 3, "CAM_3": 4}
    return mapping.get(camera_id, 1)

def class_id_to_type_name(class_id: int) -> str | None:
    mapping = {
        0: "MetalCan",
        1: "PetBottle",
        2: "Plastic",
        3: "Styrofoam",
    }
    return mapping.get(class_id)