#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from pathlib import Path

urdf_path = Path.home() / (
    "e5_ws/src/e5_arm_sim/urdf/mecharm_270_m5_sim.urdf"
)

masses = {
    "base": 1.0,
    "link1": 0.30,
    "link2": 0.30,
    "link3": 0.25,
    "link4": 0.20,
    "link5": 0.15,
    "link6": 0.12,
    "gripper_base": 0.10,
    "gripper_left1": 0.02,
    "gripper_left2": 0.02,
    "gripper_left3": 0.02,
    "gripper_right1": 0.02,
    "gripper_right2": 0.02,
    "gripper_right3": 0.02,
}

tree = ET.parse(urdf_path)
root = tree.getroot()

for link in root.findall("link"):
    if link.find("inertial") is not None:
        continue

    name = link.get("name")
    mass_value = masses.get(name, 0.05)

    inertial = ET.Element("inertial")
    ET.SubElement(
        inertial,
        "origin",
        {"xyz": "0 0 0", "rpy": "0 0 0"},
    )
    ET.SubElement(
        inertial,
        "mass",
        {"value": str(mass_value)},
    )
    ET.SubElement(
        inertial,
        "inertia",
        {
            "ixx": "0.0001",
            "ixy": "0.0",
            "ixz": "0.0",
            "iyy": "0.0001",
            "iyz": "0.0",
            "izz": "0.0001",
        },
    )

    link.insert(0, inertial)

ET.indent(tree, space="  ")
tree.write(urdf_path, encoding="utf-8", xml_declaration=True)

print(f"Updated: {urdf_path}")
print(f"Links processed: {len(root.findall('link'))}")

