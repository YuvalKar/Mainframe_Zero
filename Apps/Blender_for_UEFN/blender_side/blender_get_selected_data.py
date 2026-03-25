import bpy

def get_selected_data():

    selected_objs = [o for o in bpy.data.objects if o.select_get()]
    
    if not selected_objs:
        return {"success": False, "message": "No object selected", "data": []}
        
    data_list = []
    for obj in selected_objs:
        data_list.append({
            "name": obj.name,
            "type": obj.type,
            "location": {"x": round(obj.location.x, 3), "y": round(obj.location.y, 3), "z": round(obj.location.z, 3)},
            "rotation": {"x": round(obj.rotation_euler.x, 3), "y": round(obj.rotation_euler.y, 3), "z": round(obj.rotation_euler.z, 3)},
            "scale": {"x": round(obj.scale.x, 3), "y": round(obj.scale.y, 3), "z": round(obj.scale.z, 3)},
            "dimensions": {"x": round(obj.dimensions.x, 3), "y": round(obj.dimensions.y, 3), "z": round(obj.dimensions.z, 3)}
        })
        
    return {"success": True, "message": f"Found {len(selected_objs)} objects.", "data": data_list}