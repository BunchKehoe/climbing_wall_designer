import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

HEIGHT = 1.77  # meters
WIDTH = 1.2   # meters
DEPTH = 1.94   # meters

@dataclass
class WallSpec:
    height: float  # meters
    width: float   # meters
    depth: float   # meters
    
    @property
    def angle_deg(self) -> float:
        """Calculate the wall angle in degrees based on height and depth"""
        return round(math.degrees(math.atan(self.depth / self.height)), 1)

@dataclass
class MaterialList:
    plywood_sheets: int
    timber_lengths: list
    cut_angles: dict
    safe_climber_weight: float

def calculate_wall(spec: WallSpec) -> MaterialList:
    # Validate dimensions
    if spec.height <= 0 or spec.width <= 0 or spec.depth <= 0:
        raise ValueError("All dimensions must be positive numbers")

    # Validate angle safety constraints
    angle_deg = spec.angle_deg
    if angle_deg < 15:
        raise ValueError(f"Wall angle {angle_deg:.1f}° is too shallow. Minimum angle is 15°")
    if angle_deg > 70:  # Maximum safe angle for home climbing walls
        raise ValueError(f"Wall angle {angle_deg:.1f}° is too steep. Maximum safe angle is 70°")
        
    # Validate height for home installation safety
    if spec.height > 4.0:  # 4 meters is maximum safe height for home installation
        raise ValueError(f"Height {spec.height:.1f}m exceeds safe limit of 4.0m for home installation")
        
    # Validate width and height-to-width ratio for stability
    if spec.width < 1.2:  # Minimum width for stability
        raise ValueError(f"Width {spec.width:.1f}m is too small for stability. Minimum width is 1.2m")
    
    # Check height-to-width ratio (maximum 2:1 for stability)
    if spec.height / spec.width > 2.0:
        raise ValueError(f"Height-to-width ratio {spec.height/spec.width:.1f} exceeds safe limit of 2.0")

    h = spec.height * 1000
    w = spec.width * 1000
    d = spec.depth * 1000
    angle = math.radians(angle_deg)

    # Calculate required depth based on angle
    panel_depth = spec.height * math.tan(angle)
    
    # Add a small tolerance (1cm) to account for rounding errors
    if panel_depth > spec.depth + 0.01:
        required_depth = panel_depth
        actual_angle = math.degrees(math.atan(spec.depth / spec.height))
        raise ValueError(f"Not enough depth. Maximum angle for given depth is {actual_angle:.1f}°")

    panel_height = h / math.cos(angle)
    panel_depth = h * math.tan(angle)
    if panel_depth > d:
        raise ValueError("Not enough depth for this angle. Reduce angle or increase depth.")

    # Plywood sheet 2500x1250 mm
    sheet_h, sheet_w = 2500, 1250
    sheets_per_row = math.ceil(w / sheet_w)
    rows = math.ceil(panel_height / sheet_h)
    total_sheets = sheets_per_row * rows

    # Hardware calculations removed - holds can be placed as needed

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

    # Safety calculations with strict validation
    panel_capacity = (w / 1000) * (h / 1000) * 200  # kg/m² for 18mm structural plywood
    timber_capacity = 1200  # kg for structural grade timber
    bolt_capacity = 6400   # kg for M10 bolts
    
    # Additional angle-based safety factors
    if angle > math.radians(45):
        # Reduce capacities for steep angles due to increased shear forces
        panel_capacity *= 0.8
        timber_capacity *= 0.8
        
    raw_capacity = min(panel_capacity, timber_capacity, bolt_capacity)
    
    # Strict safety factors:
    # - Factor of 3.0 for general safety
    # - Additional factor of 2.5 for dynamic loads
    # - Total safety factor of 7.5
    safe_capacity = raw_capacity / 3.0
    safe_climber_weight = safe_capacity / 2.5
    
    # Validate minimum safe capacity
    if safe_climber_weight < 80:  # Minimum safe capacity for adult climbers
        raise ValueError(f"Design cannot safely support minimum required weight of 80kg")

    return MaterialList(
        plywood_sheets=total_sheets,
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
    
    # Top view (top right)
    ax2 = fig.add_subplot(222)
    angle = math.radians(spec.angle_deg)
    panel_width = spec.width
    panel_height = spec.height / math.cos(angle)
    
    # Draw panel outline
    ax2.add_patch(plt.Rectangle((0, 0), panel_width, panel_height, fill=False))
    
    ax2.set_title('Panel Layout (Top View)')
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
    
    # Create designs directory if it doesn't exist
    designs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designs")
    os.makedirs(designs_dir, exist_ok=True)
    
    # Save the figure
    save_path = os.path.join(designs_dir, "wall_design.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nWall design saved to: {save_path}")
    
    # Uncomment to show interactive plot instead of saving
    # plt.show()

def create_materials_list(spec: WallSpec, materials: MaterialList) -> str:
    """Create a detailed materials list file with dimensions and quantities
    
    Returns:
        str: The formatted materials list content
    """
    
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

HARDWARE RECOMMENDATIONS
----------------------
- Pre-drill holes for climbing holds as needed
- Use 20mm countersunk T-nuts for hold mounting
- Use M10 Allen head bolts for holds
- Space holds according to route design
- Install holds after completing wall construction and sealing

CRITICAL ANGLES
--------------"""
    
    for joint, angle in materials.cut_angles.items():
        content += f"\n{joint}: {angle:.1f}°"

    content += f"""

SAFETY INFORMATION
-----------------
⚠️ CRITICAL SAFETY WARNINGS ⚠️
1. Maximum Safe Climber Weight: {materials.safe_climber_weight:.1f} kg
2. Overall Safety Factor: 7.5 (3.0 × 2.5 for dynamic loads)
3. Minimum Required Materials:
   - 18mm structural grade plywood
   - Grade 8.8 or higher M10 bolts
   - Structural grade timber
4. Required Anchor Points: Minimum 4
5. Load Testing:
   - Test with static loads before climbing
   - Start at 50% max weight and gradually increase
   - Check all joints and anchors after testing
6. Regular Inspection:
   - Check all bolts monthly
   - Inspect timber for damage/rot
   - Verify anchor points remain secure
7. Additional Safety Measures:
   - Use proper crash pads
   - Never climb alone
   - Stay within weight limits
   - Maintain proper clearance zones

CERTIFIED INSPECTION REQUIRED:
This design must be reviewed by a qualified person
before use. Climbing is inherently dangerous and
improper construction could result in serious
injury or death.

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

    # Create materials list directory if it doesn't exist
    materials_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials_lists")
    os.makedirs(materials_dir, exist_ok=True)
    
    return content

def frange(start, stop, step):
    while start < stop:
        yield round(start,2)
        start += step

if __name__ == "__main__":
    wall = WallSpec(height=2.4, width=2.4, depth=2.0)  # depth adjusted to accommodate calculated angle
    materials = calculate_wall(wall)

    print("=== DIY Climbing Wall Plan ===")
    print(f"\nWALL SPECIFICATIONS:")
    print(f"Height: {wall.height:.2f} m")
    print(f"Width: {wall.width:.2f} m")
    print(f"Depth from wall: {wall.depth:.2f} m")
    print(f"Wall angle: {wall.angle_deg}°")

    print("\nMATERIALS REQUIRED:")
    print(f"Plywood sheets needed (2500x1250mm): {materials.plywood_sheets}")
    
    print("\nTIMBER CUT LIST (meters):")
    for name, length in materials.timber_lengths:
        print(f"  {name}: {length:.2f} m")
    
    print("\nCUT ANGLES (degrees):")
    for joint, angle in materials.cut_angles.items():
        print(f"  {joint}: {angle:.1f}°")
    
    print("\nSAFETY INFORMATION:")
    print(f"Safe maximum climber weight: {materials.safe_climber_weight:.1f} kg")
    print("Remember to test thoroughly before full-weight climbing")

    # Generate the design and materials list
    draw_wall(wall, materials)
    content = create_materials_list(wall, materials)
    
    # Create materials list directory if it doesn't exist
    materials_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials_lists")
    os.makedirs(materials_dir, exist_ok=True)
    
    # Save the materials list
    materials_path = os.path.join(materials_dir, "materials_list.txt")
    with open(materials_path, 'w') as f:
        f.write(content)
    print(f"\nDetailed materials list saved to: {materials_path}")
