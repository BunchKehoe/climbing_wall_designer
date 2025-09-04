import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

@dataclass
class WallSpec:
    height: float  # meters
    width: float   # meters
    depth: float   # meters
    angle_deg: float = 25.0
    tnut_spacing: float = 0.20  # meters

@dataclass
class MaterialList:
    plywood_sheets: int
    tnuts: int
    holds: int
    bolts: int
    timber_lengths: list
    cut_angles: dict
    safe_climber_weight: float

def calculate_wall(spec: WallSpec) -> MaterialList:
    h = spec.height * 1000
    w = spec.width * 1000
    d = spec.depth * 1000
    angle = math.radians(spec.angle_deg)

    panel_height = h / math.cos(angle)
    panel_depth = h * math.tan(angle)
    if panel_depth > d:
        raise ValueError("Not enough depth for this angle. Reduce angle or increase depth.")

    # Plywood sheet 2500x1250 mm
    sheet_h, sheet_w = 2500, 1250
    sheets_per_row = math.ceil(w / sheet_w)
    rows = math.ceil(panel_height / sheet_h)
    total_sheets = sheets_per_row * rows

    # T-nut grid
    grid_x = int(w // (spec.tnut_spacing * 1000))
    grid_y = int(h // (spec.tnut_spacing * 1000))
    tnuts = grid_x * grid_y
    holds = tnuts // 2
    bolts = holds

    # Frame timber lengths
    base_beam = w
    uprights = 2 * h / math.cos(angle)
    cross_braces = w
    kicker_depth = panel_depth
    timber_lengths = [
        ("Base beam", base_beam / 1000),
        ("Uprights (x2)", uprights / 1000),
        ("Cross braces (x2)", cross_braces / 1000),
        ("Kicker/struts", kicker_depth / 1000)
    ]

    cut_angles = {
        "Upright to base": spec.angle_deg,
        "Top plate join": 90 - spec.angle_deg
    }

    # Safety calculations
    panel_capacity = (w / 1000) * (h / 1000) * 200  # kg
    timber_capacity = 1200
    bolt_capacity = 6400
    raw_capacity = min(panel_capacity, timber_capacity, bolt_capacity)
    safe_capacity = raw_capacity / 3.0
    safe_climber_weight = safe_capacity / 2.5

    return MaterialList(
        plywood_sheets=total_sheets,
        tnuts=tnuts,
        holds=holds,
        bolts=bolts,
        timber_lengths=timber_lengths,
        cut_angles=cut_angles,
        safe_climber_weight=safe_climber_weight
    )

def create_3d_wall(spec: WallSpec):
    """Generate 3D coordinates for the wall structure"""
    angle = math.radians(spec.angle_deg)
    h, w = spec.height, spec.width
    d = h * math.tan(angle)

    # Main wall panel vertices
    panel = np.array([
        [0, 0, 0],           # bottom left
        [w, 0, 0],           # bottom right
        [w, h*math.cos(angle), h*math.sin(angle)],  # top right
        [0, h*math.cos(angle), h*math.sin(angle)]   # top left
    ])

    # Support structure vertices
    left_support = np.array([
        [0, 0, 0],           # bottom front
        [0, 0, d],           # bottom back
        [0, h*math.cos(angle), h*math.sin(angle)],  # top front
    ])

    right_support = np.array([
        [w, 0, 0],           # bottom front
        [w, 0, d],           # bottom back
        [w, h*math.cos(angle), h*math.sin(angle)]   # top front
    ])

    # Base frame vertices
    base = np.array([
        [0, 0, 0],           # front left
        [w, 0, 0],           # front right
        [w, 0, d],           # back right
        [0, 0, d]            # back left
    ])

    return panel, left_support, right_support, base

def draw_wall(spec: WallSpec, materials: MaterialList):
    fig = plt.figure(figsize=(15, 10))
    
    # Main 3D view (top left)
    ax1 = fig.add_subplot(121, projection='3d')
    panel, left_support, right_support, base = create_3d_wall(spec)
    
    # Plot main climbing surface
    ax1.add_collection3d(Poly3DCollection([panel], facecolors='lightgray', alpha=0.3, edgecolors='black'))
    
    # Plot support structures
    ax1.add_collection3d(Poly3DCollection([left_support], facecolors='green', alpha=0.3))
    ax1.add_collection3d(Poly3DCollection([right_support], facecolors='green', alpha=0.3))
    ax1.add_collection3d(Poly3DCollection([base], facecolors='brown', alpha=0.3))

    # Set axis limits and labels
    max_dim = max(spec.width, spec.height, spec.depth)
    ax1.set_box_aspect([spec.width, spec.height, spec.depth])
    ax1.set_xlabel('Width (m)')
    ax1.set_ylabel('Depth (m)')
    ax1.set_zlabel('Height (m)')
    
    # Add dimensions
    ax1.text(spec.width/2, -0.2, 0, f'{spec.width:.2f}m', ha='center')
    ax1.text(-0.2, spec.height/2, 0, f'{spec.height:.2f}m', ha='right')
    ax1.text(spec.width+0.2, 0, spec.depth/2, f'{spec.depth:.2f}m', ha='left')
    
    # Top view with T-nut grid (top right)
    ax2 = fig.add_subplot(222)
    spacing = spec.tnut_spacing
    angle = math.radians(spec.angle_deg)
    panel_width = spec.width
    panel_height = spec.height / math.cos(angle)
    
    # Draw panel outline
    ax2.add_patch(plt.Rectangle((0, 0), panel_width, panel_height, fill=False))
    
    # Draw T-nut grid
    for x in np.arange(spacing, panel_width-spacing/2, spacing):
        for y in np.arange(spacing, panel_height-spacing/2, spacing):
            ax2.plot(x, y, 'ko', markersize=3)
    
    ax2.set_title('T-nut Grid Layout (Top View)')
    ax2.set_aspect('equal')
    ax2.set_xlabel('Width (m)')
    ax2.set_ylabel('Length (m)')
    
    # Side view (bottom right)
    ax3 = fig.add_subplot(224)
    h = spec.height
    d = h * math.tan(angle)
    
    # Draw side profile
    ax3.plot([0, d], [0, h], 'k-', linewidth=2)
    ax3.plot([0, 0], [0, h], 'g--', label='Support')
    
    # Add angle label
    ax3.text(d/2, h/2, f'{spec.angle_deg}°', ha='center', va='bottom')
    
    ax3.set_title('Side Profile')
    ax3.set_aspect('equal')
    ax3.set_xlabel('Depth (m)')
    ax3.set_ylabel('Height (m)')
    ax3.legend()

    plt.suptitle('DIY Climbing Wall Design', fontsize=16)
    plt.tight_layout()
    
    # Save the figure

    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designs/wall_design.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nWall design saved to: {save_path}")
    
    # Uncomment to show interactive plot instead of saving
    # plt.show()

def create_materials_list(spec: WallSpec, materials: MaterialList):
    """Create a detailed materials list file with dimensions and quantities"""
    
    # Calculate additional measurements
    angle = math.radians(spec.angle_deg)
    panel_height = spec.height / math.cos(angle)
    panel_area = spec.width * panel_height
    
    content = f"""=== DIY Climbing Wall Materials List ===

WALL SPECIFICATIONS
------------------
Overall Height: {spec.height:.2f} m
Overall Width: {spec.width:.2f} m
Depth from Wall: {spec.depth:.2f} m
Wall Angle: {spec.angle_deg}°
Actual Panel Length: {panel_height:.2f} m
Total Panel Area: {panel_area:.2f} m²

PLYWOOD PANELS
-------------
Type: Structural Plywood (minimum 18mm thick)
Full Sheets Required: {materials.plywood_sheets}
Sheet Size: 2500mm x 1250mm
Coverage Area Required: {panel_area:.2f} m²

TIMBER FRAME
-----------"""

    for name, length in materials.timber_lengths:
        content += f"\n{name}: {length:.2f} m"
    
    content += f"""

CLIMBING HOLDS & HARDWARE
-----------------------
T-nuts Required: {materials.tnuts} (20mm countersunk)
Recommended Holds: {materials.holds}
Mounting Bolts: {materials.bolts} (M10 Allen head)
T-nut Spacing: {spec.tnut_spacing * 100:.1f} cm

CRITICAL ANGLES
--------------"""
    
    for joint, angle in materials.cut_angles.items():
        content += f"\n{joint}: {angle:.1f}°"

    content += f"""

SAFETY INFORMATION
-----------------
Maximum Safe Climber Weight: {materials.safe_climber_weight:.1f} kg
Safety Factor: 2.5
Recommended Anchor Points: 4 minimum

ADDITIONAL MATERIALS
-------------------
- Weather sealant for plywood
- Construction screws (minimum 4 per joint)
- Washers for all bolts
- Anti-slip matting for ground protection

INSTALLATION NOTES
-----------------
1. All timber should be structural grade
2. Use galvanized/weather-resistant hardware if outdoor installation
3. Pre-drill all screw holes to prevent splitting
4. Check all angles before final assembly
5. Ensure proper anchoring to ground/wall
6. Apply sealant before installing holds
7. Double-check all bolt tightness before use"""

    # Create materials list file
    materials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials_lists/materials_list.txt")
    with open(materials_path, 'w') as f:
        f.write(content)
    print(f"\nMaterials list saved to: {materials_path}")

def frange(start, stop, step):
    while start < stop:
        yield round(start,2)
        start += step

if __name__ == "__main__":
    wall = WallSpec(height=2.4, width=2.4, depth=3.0, angle_deg=25)
    materials = calculate_wall(wall)

    print("=== DIY Spray Wall Plan ===")
    print(f"Plywood sheets needed: {materials.plywood_sheets}")
    print(f"T-nuts required: {materials.tnuts}")
    print(f"Holds recommended: {materials.holds}")
    print(f"Bolts required: {materials.bolts}")
    print("\nTimber cut list (meters):")
    for name, length in materials.timber_lengths:
        print(f"  {name}: {length:.2f} m")
    print("\nCut Angles (degrees):")
    for joint, angle in materials.cut_angles.items():
        print(f"  {joint}: {angle:.1f}°")
    print("\n=== Safety Check ===")
    print(f"Safe maximum climber weight: {materials.safe_climber_weight:.1f} kg")

    # Generate the design and materials list
    draw_wall(wall, materials)
    create_materials_list(wall, materials)
