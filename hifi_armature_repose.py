
import bpy
from mathutils import Quaternion, Matrix, Vector, Euler

from math import pi
from .hifi_armature_data import structure as base_armature

# This is unit tested to be correct.


def correct_scale_rotation(obj, rotation):
    current_context = bpy.context.area.type
    bpy.context.area.type = 'VIEW_3D'
    # set context to 3D View and set Cursor
    bpy.context.space_data.cursor_location[0] = 0.0
    bpy.context.space_data.cursor_location[1] = 0.0
    bpy.context.space_data.cursor_location[2] = 0.0
    bpy.context.area.type = current_context
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.scale = Vector((100, 100, 100))
    str_angle = -90 * pi/180
    if rotation:
        obj.rotation_euler = Euler((str_angle, 0, 0), 'XYZ')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.scale = Vector((0.01, 0.01, 0.01))
    if rotation:
        obj.rotation_euler = Euler((-str_angle, 0, 0), 'XYZ')


def navigate_armature(data, current_rest_node, world_matrix, parent, parent_node):
    name = current_rest_node["name"]
    bone = data.get(name)
    if(bone):
        bone.rotation_mode = "QUATERNION"
        destination_matrix = current_rest_node["matrix_local"].copy()
        inv_destination_matrix = destination_matrix.inverted()
        matrix = bone.matrix
        if parent:
            parent_matrix = parent.matrix.copy()
            parent_inverted = parent_matrix.inverted()
            parent_destination = parent_node["matrix_local"].copy()
        else:
            parent_matrix = Matrix()
            parent_inverted = Matrix()
            parent_destination = Matrix()
        smat = inv_destination_matrix * \
            (parent_destination * (parent_inverted * matrix))
        bone.rotation_quaternion = smat.to_quaternion().inverted()
        for child in current_rest_node["children"]:
            navigate_armature(data, child, world_matrix,
                              bone, current_rest_node)
    else:
        bone = parent
        for child in current_rest_node["children"]:
            navigate_armature(data, child, world_matrix, bone, parent_node)


def retarget_armature(options):

    armature = bpy.context.object
    if armature.type == "ARMATURE":
        # Center Children First
        bpy.ops.object.mode_set(mode='OBJECT')

        # Make sure to reset the bones first.
        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=True)
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        bpy.ops.pose.select_all(action='DESELECT')

        print("---")

        # Now lets do the repose to rest
        world_matrix = armature.matrix_world
        bones = armature.pose.bones
        for bone in base_armature:
            navigate_armature(bones, bone, world_matrix, None, None)
            print("Iterating Bones")

        # Then apply everything
        if options['apply']:
            bpy.ops.object.mode_set(mode='OBJECT')
            correct_scale_rotation(armature, True)
            print("Scale")
            bpy.ops.object.mode_set(mode='POSE')

            print("Now Fix Armature for all")
            for child in armature.children:
                armature_modifier = False
            
                for modifier in child.modifiers:
                    if modifier.type == "ARMATURE" and modifier.object == armature:
                        name = modifier.name
                        # COPY OTHER SETTINGs
                        print("Apply", name, " to ", child.name)

                        bpy.context.scene.objects.active = child
                        armature_modifier = True
                        print(armature_modifier)
                        bpy.ops.object.modifier_apply(
                            apply_as='DATA', modifier=modifier.name)
                                
                print("READY FOR NEXT ")

                if armature_modifier:
                    print("Creating new modifier",
                          name, "_fix for ", child.name)
                    new_modifier = child.modifiers.new(
                        name + "_fix", "ARMATURE")
                    new_modifier.object = armature

                correct_scale_rotation(child, False)

            print("Set", armature, " active")
            bpy.context.scene.objects.active = armature

            bpy.ops.object.mode_set(mode='POSE')
            print("Apply Armature")
            bpy.ops.pose.armature_apply()

           

        bpy.ops.object.mode_set(mode='OBJECT')
