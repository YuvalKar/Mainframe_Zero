import unreal

def get_selected_data():
    # Fetch all currently selected actors in the UEFN viewport
    selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    
    if not selected_actors:
        return {"success": False, "message": "No object selected in UEFN", "data": []}
        
    data_list = []
    for actor in selected_actors:
        # Extract location, rotation, and scale using Unreal's syntax
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        
        data_list.append({
            "name": actor.get_actor_label(),
            "type": actor.get_class().get_name(),
            "location": {"x": round(loc.x, 3), "y": round(loc.y, 3), "z": round(loc.z, 3)},
            "rotation": {"x": round(rot.roll, 3), "y": round(rot.pitch, 3), "z": round(rot.yaw, 3)},
            "scale": {"x": round(scale.x, 3), "y": round(scale.y, 3), "z": round(scale.z, 3)}
        })
        
    return {"success": True, "message": f"Found {len(selected_actors)} objects.", "data": data_list}