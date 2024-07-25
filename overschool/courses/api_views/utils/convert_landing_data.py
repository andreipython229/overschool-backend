def change_keys(dicts):
    # удаление всех ключей, начинающихся на "photo"
    for dictionary in dicts:
        keys_to_remove = [key for key in dictionary if key.startswith("photo")]
        for key in keys_to_remove:
            del dictionary[key]
    return dicts

def convert_landing_data(data):
    return {
        "header": {
            "position": data["header"]["id"],
            "is_visible": data["header"]["visible"],
            "can_up": data["header"]["canUp"],
            "can_down": data["header"]["canDown"],
        },
        "course": {
            "name": data["header"]["name"],
            "description": data["header"]["description"],
        },
        "stats": {
            "position": data["stats"]["id"],
            "is_visible": data["stats"]["visible"],
            "can_up": data["stats"]["canUp"],
            "can_down": data["stats"]["canDown"],
        },
        "audience": {
            "position": data["audience"]["id"],
            "is_visible": data["audience"]["visible"],
            "can_up": data["audience"]["canUp"],
            "can_down": data["audience"]["canDown"],
            "description": data["audience"]["description"],
            "chips": change_keys(data["audience"]["chips"]),
        },
        "training_program": {
            "position": data["trainingProgram"]["id"],
            "is_visible": data["trainingProgram"]["visible"],
            "can_up": data["trainingProgram"]["canUp"],
            "can_down": data["trainingProgram"]["canDown"],
        },
        "training_purpose": {
            "position": data["trainingPurpose"]["id"],
            "is_visible": data["trainingPurpose"]["visible"],
            "can_up": data["trainingPurpose"]["canUp"],
            "can_down": data["trainingPurpose"]["canDown"],
            "description": data["trainingPurpose"]["description"],
            "chips": change_keys(data["trainingPurpose"]["chips"]),
        },
    }
