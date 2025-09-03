import math
import matplotlib.pyplot as plt
from dataclasses import dataclass

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

def draw_wall(spec: WallSpec, materials: MaterialList):
    angle = math.radians(spec.angle_deg)
    panel_height = spec.height / math.cos(angle)
    panel_depth = spec.height * math.tan(angle)

    fig, ax = plt.subplots(figsize=(8,6))

    # Draw wall panel
    ax.plot([0, spec.width], [0, spec.height], color="blue", linewidth=2)
    ax.plot([0, spec.width], [0, spec.height], color="blue")
    ax.add_patch(plt.Polygon(
        [[0,0], [spec.width,0], 
         [spec.width - panel_depth, spec.height], 
         [-panel_depth, spec.height]], 
        closed=True, fill=False, edgecolor="blue", linewidth=2, label="Climbing Wall"
    ))

    # T-nut grid
    spacing = spec.tnut_spacing
    for x in frange(spacing, spec.width-spacing, spacing):
        for y in frange(spacing, spec.height-spacing, spacing):
            ax.plot(x, y, "ro", markersize=2)

    # Uprights
    ax.plot([0, -panel_depth], [0, spec.height], color="green", linestyle="--", label="Upright/Strut")
    ax.plot([spec.width, spec.width - panel_depth], [0, spec.height], color="green", linestyle="--")

    # Labels
    ax.set_aspect("equal")
    ax.set_xlim(-panel_depth-0.5, spec.width+0.5)
    ax.set_ylim(0, spec.height+0.5)
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title(f"DIY Climbing Wall Layout ({spec.angle_deg}°)")
    ax.legend()
    plt.show()

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

    # Draw the wall
    draw_wall(wall, materials)
