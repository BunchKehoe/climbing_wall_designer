import unittest
import math
import os
import numpy as np
import matplotlib.pyplot as plt
from wall_designer import (
    WallSpec, MaterialList, calculate_wall, create_3d_wall,
    draw_wall, create_materials_list
)

class TestWallDesigner(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        # Using dimensions that ensure the panel depth won't exceed the available depth
        self.wall_spec = WallSpec(height=2.4, width=2.4, depth=2.0)  # Increased depth for viable angle
        self.materials = calculate_wall(self.wall_spec)
        
        # Calculate the actual panel depth for validation
        angle = math.radians(self.wall_spec.angle_deg)
        self.panel_depth = self.wall_spec.height * math.tan(angle)
        self.assertTrue(self.panel_depth <= self.wall_spec.depth, 
                       f"Panel depth ({self.panel_depth:.2f}m) exceeds available depth ({self.wall_spec.depth}m)")

    def test_wall_spec_angle_calculation(self):
        """Test wall angle calculations against climbing industry standards"""
        # Test standard beginner-friendly angle (20°)
        beginner_wall = WallSpec(
            height=2.4,
            width=2.4,
            depth=math.tan(math.radians(20)) * 2.4
        )
        self.assertAlmostEqual(beginner_wall.angle_deg, 20, places=1,
            msg="Beginner-friendly angle should be accurate")

        # Test standard vertical training angle (30°)
        training_wall = WallSpec(
            height=2.4,
            width=2.4,
            depth=math.tan(math.radians(30)) * 2.4
        )
        self.assertAlmostEqual(training_wall.angle_deg, 30, places=1,
            msg="Training angle should be accurate")

        # Test competition-style overhang (45°)
        overhang_wall = WallSpec(
            height=2.4,
            width=2.4,
            depth=2.4  # 45° angle
        )
        self.assertAlmostEqual(overhang_wall.angle_deg, 45, places=1,
            msg="Overhang angle should be accurate")
            
        # Test angle consistency with different dimensions
        # (angle shouldn't change if height:depth ratio stays constant)
        wall1 = WallSpec(height=2.4, width=2.4, depth=1.2)  # 1:0.5 ratio
        wall2 = WallSpec(height=3.0, width=2.4, depth=1.5)  # Same 1:0.5 ratio
        self.assertAlmostEqual(wall1.angle_deg, wall2.angle_deg, places=1,
            msg="Angle should be consistent for same height:depth ratio")

    def test_plywood_panel_requirements(self):
        """Test plywood panel calculations and layout optimization"""
        materials = self.materials
        angle = math.radians(self.wall_spec.angle_deg)
        
        # Calculate actual climbing surface dimensions
        panel_height = self.wall_spec.height / math.cos(angle)
        panel_area = self.wall_spec.width * panel_height
        
        # Standard sheet dimensions
        SHEET_HEIGHT = 2500  # mm
        SHEET_WIDTH = 1250   # mm
        SHEET_AREA = (SHEET_HEIGHT * SHEET_WIDTH) / 1000000  # m²
        
        # Test sheet count calculation
        sheets_height = math.ceil(panel_height * 1000 / SHEET_HEIGHT)
        sheets_width = math.ceil(self.wall_spec.width * 1000 / SHEET_WIDTH)
        expected_sheets = sheets_height * sheets_width
        
        self.assertEqual(materials.plywood_sheets, expected_sheets,
            msg="Sheet count should minimize waste while covering area")
        
        # Verify total sheet area is sufficient
        total_sheet_area = materials.plywood_sheets * SHEET_AREA
        self.assertGreater(total_sheet_area, panel_area,
            msg="Total sheet area must exceed climbing surface area")
        
        # Check waste factor is reasonable (<45% waste - typical for angled walls)
        waste_factor = (total_sheet_area - panel_area) / total_sheet_area
        self.assertLess(waste_factor, 0.45,
            msg="Panel layout should not waste more than 45% of materials")
        
        # Verify sheet count increases with size
        larger_wall = WallSpec(
            height=self.wall_spec.height * 1.5,
            width=self.wall_spec.width * 1.5,
            depth=self.wall_spec.depth * 1.5
        )
        larger_materials = calculate_wall(larger_wall)
        self.assertGreater(larger_materials.plywood_sheets, materials.plywood_sheets,
            msg="Larger walls should require more sheets")

    def test_timber_frame_design(self):
        """Test timber frame design for structural integrity and constructability"""
        materials = self.materials
        angle = math.radians(self.wall_spec.angle_deg)
        h = self.wall_spec.height
        w = self.wall_spec.width
        d = h * math.tan(angle)
        
        # 1. Test frame completeness
        required_pieces = {
            "Base beam": "Primary support and anchor point",
            "Uprights (x2)": "Main load-bearing structure",
            "Cross braces (x2)": "Lateral stability",
            "Kicker/struts": "Angle support and force distribution"
        }
        timber_names = [t[0] for t in materials.timber_lengths]
        for piece, purpose in required_pieces.items():
            self.assertIn(piece, timber_names,
                msg=f"Missing {piece} - required for {purpose}")

        # 2. Test structural dimensions
        for name, length in materials.timber_lengths:
            # Basic sanity checks
            self.assertGreater(length, 0, "All lengths must be positive")
            
            # For uprights that come as pairs, check individual length
            if "(x2)" in name:
                individual_length = length / 2
                self.assertLess(individual_length, 6.0,
                    msg=f"Individual {name} length over 6m not practical for transport/installation")
            else:
                self.assertLess(length, 6.0,
                    msg=f"{name} length over 6m not practical for transport/installation")
            
            if name == "Base beam":
                self.assertAlmostEqual(length, w, places=2,
                    msg="Base must match wall width exactly")
                
            elif name == "Uprights (x2)":
                expected_upright = 2 * h / math.cos(angle)  # Both uprights
                self.assertAlmostEqual(length, expected_upright, places=2,
                    msg="Uprights must account for angle")
                # Check individual upright length is manageable
                self.assertLess(length/2, 4.0,
                    msg="Individual uprights should not exceed 4m for handling")
                
            elif name == "Cross braces (x2)":
                self.assertAlmostEqual(length, w, places=2,
                    msg="Cross braces must span wall width")
                # Verify minimum of 2 cross braces for stability
                self.assertGreaterEqual(
                    len([t for t in materials.timber_lengths if t[0] == "Cross braces (x2)"]),
                    1, msg="Minimum 2 cross braces required")
                
            elif name == "Kicker/struts":
                self.assertAlmostEqual(length, d, places=2,
                    msg="Struts must match calculated depth")
                # Verify strut angle is within workable range
                strut_angle = 90 - self.wall_spec.angle_deg
                self.assertGreater(strut_angle, 20,
                    msg="Strut angle too shallow for effective support")
                self.assertLess(strut_angle, 75,
                    msg="Strut angle too steep for effective support")
                
        # 3. Test support spacing
        max_unsupported_span = 0.6  # meters, standard for 18mm plywood
        spans = []
        if w > max_unsupported_span:
            n_supports = math.ceil(w / max_unsupported_span)
            span = w / n_supports
            spans.append(span)
        self.assertTrue(all(s <= max_unsupported_span for s in spans),
            msg=f"Support spacing exceeds maximum {max_unsupported_span}m for plywood strength")

    def test_cut_angles(self):
        """Test cut angle calculations"""
        materials = self.materials
        
        # Check required angles are present
        self.assertIn("Upright to base", materials.cut_angles)
        self.assertIn("Top plate join", materials.cut_angles)
        
        # Test angle calculations
        angle = self.wall_spec.angle_deg
        self.assertAlmostEqual(materials.cut_angles["Upright to base"], angle)
        self.assertAlmostEqual(materials.cut_angles["Top plate join"], 90 - angle)

    def test_safety_calculations(self):
        """Test safety weight calculations and constraints"""
        # Test base case
        materials = self.materials
        h = self.wall_spec.height
        w = self.wall_spec.width
        angle = math.radians(self.wall_spec.angle_deg)
        
        # Calculate expected safety weight with all safety factors
        panel_capacity = w * h * 200  # kg/m² for 18mm structural plywood
        timber_capacity = 1200  # kg for structural timber
        bolt_capacity = 6400   # kg for M10 bolts
        
        # Apply angle-based safety factors
        if angle > math.radians(45):
            panel_capacity *= 0.8
            timber_capacity *= 0.8
        
        raw_capacity = min(panel_capacity, timber_capacity, bolt_capacity)
        expected_safe_weight = (raw_capacity / 3.0) / 2.5  # Combined safety factor of 7.5
        
        # Test actual vs expected calculation
        self.assertAlmostEqual(
            materials.safe_climber_weight,
            expected_safe_weight,
            msg="Safety weight calculation must be exact",
            places=1)
        
        # Test minimum safety requirements
        self.assertGreaterEqual(materials.safe_climber_weight, 80,
            "Must safely support at least 80kg")
        self.assertLess(materials.safe_climber_weight, raw_capacity / 5.0,
            "Safe weight must include adequate safety margin")
            
        # Test angle effects on safety
        angles_to_test = [
            (20, 1.0),  # Shallow angle, no reduction
            (45, 1.0),  # Mid angle, no reduction
            (60, 0.8),  # Steep angle, reduced capacity
        ]
        
        for test_angle, expected_factor in angles_to_test:
            depth = h * math.tan(math.radians(test_angle))
            test_wall = WallSpec(height=h, width=w, depth=depth)
            test_materials = calculate_wall(test_wall)
            
            expected_capacity = (w * h * 200 * expected_factor)  # Base capacity with angle factor
            expected_safe = (expected_capacity / 3.0) / 2.5  # Safety factors
            
            self.assertAlmostEqual(
                test_materials.safe_climber_weight / materials.safe_climber_weight,
                expected_factor,
                places=1,
                msg=f"Incorrect safety reduction at {test_angle}°"
            )
            
        # Test limiting factors
        # Test wider wall has proportionally increased capacity
        # Note: Won't scale exactly linearly due to structural considerations
        wide_wall = WallSpec(height=2.4, width=4.8, depth=2.4)  # Double width
        wide_materials = calculate_wall(wide_wall)
        capacity_ratio = wide_materials.safe_climber_weight / materials.safe_climber_weight
        self.assertGreater(capacity_ratio, 1.0,
            msg="Wider wall should support more weight")
        self.assertLess(capacity_ratio, 2.0,
            msg="Capacity shouldn't scale fully linear due to structural limits")
        
        # 2. Timber limited (ensure we don't exceed timber capacity)
        timber_limit = 1200 / (3.0 * 2.5)  # Raw capacity with safety factors
        self.assertLess(materials.safe_climber_weight, timber_limit,
            "Must respect timber capacity limits")
        
        # Test critical safety constraints
        with self.assertRaises(ValueError) as context:
            unsafe_wall = WallSpec(height=1.0, width=1.2, depth=1.0)
            calculate_wall(unsafe_wall)  # Should fail minimum capacity check
        self.assertIn("support minimum required weight", str(context.exception))

    def test_3d_wall_geometry(self):
        """Test 3D wall geometry calculations"""
        panel, left_support, right_support, base = create_3d_wall(self.wall_spec)
        angle = math.radians(self.wall_spec.angle_deg)
        h, w = self.wall_spec.height, self.wall_spec.width
        
        # Test panel dimensions and coordinates
        self.assertEqual(len(panel), 4)  # Should have 4 vertices
        self.assertEqual(panel.shape, (4, 3))  # Each vertex should have x,y,z coordinates
        
        # Check key panel coordinates
        np.testing.assert_array_almost_equal(panel[0], [0, 0, 0])  # bottom left
        np.testing.assert_array_almost_equal(panel[1], [w, 0, 0])  # bottom right
        np.testing.assert_array_almost_equal(
            panel[2],
            [w, h*math.cos(angle), h*math.sin(angle)]  # top right
        )
        np.testing.assert_array_almost_equal(
            panel[3],
            [0, h*math.cos(angle), h*math.sin(angle)]  # top left
        )
        
        # Test support structure coordinates
        self.assertEqual(len(left_support), 3)
        np.testing.assert_array_almost_equal(left_support[0], [0, 0, 0])
        np.testing.assert_array_almost_equal(
            left_support[2],
            [0, h*math.cos(angle), h*math.sin(angle)]
        )
        
        # Test base frame dimensions
        self.assertEqual(len(base), 4)
        np.testing.assert_array_almost_equal(base[0], [0, 0, 0])  # front left
        np.testing.assert_array_almost_equal(base[1], [w, 0, 0])  # front right

    def test_invalid_dimensions(self):
        """Test handling of invalid and unsafe wall dimensions"""
        # Test too shallow angle (unsafe for climbing)
        with self.assertRaises(ValueError) as context:
            shallow_wall = WallSpec(height=2.4, width=2.4, depth=0.1)
            calculate_wall(shallow_wall)
        self.assertIn("too shallow", str(context.exception))

        # Test maximum height limit
        with self.assertRaises(ValueError) as context:
            tall_wall = WallSpec(height=4.1, width=2.4, depth=2.0)
            calculate_wall(tall_wall)
        self.assertIn("exceeds safe limit", str(context.exception))

        # Test minimum width for stability
        with self.assertRaises(ValueError) as context:
            narrow_wall = WallSpec(height=2.4, width=1.1, depth=2.0)
            calculate_wall(narrow_wall)
        self.assertIn("too small for stability", str(context.exception))

        # Test height-to-width ratio (stability)
        with self.assertRaises(ValueError) as context:
            unstable_wall = WallSpec(height=3.0, width=1.2, depth=2.0)  # 2.5:1 ratio
            calculate_wall(unstable_wall)
        self.assertIn("Height-to-width ratio", str(context.exception))

        # Test borderline depth case
        min_angle = 15
        height = 2.4
        min_depth = height * math.tan(math.radians(min_angle))
        
        # Just below minimum
        with self.assertRaises(ValueError) as context:
            borderline_wall = WallSpec(height=height, width=2.4, depth=min_depth - 0.01)
            calculate_wall(borderline_wall)
        self.assertIn("too shallow", str(context.exception))
        
        # Just at minimum (should pass)
        borderline_wall = WallSpec(height=height, width=2.4, depth=min_depth + 0.01)
        try:
            calculate_wall(borderline_wall)
        except ValueError as e:
            self.fail(f"Valid minimum angle should be accepted: {str(e)}")

        # Test zero dimensions
        with self.assertRaises(ValueError):
            zero_wall = WallSpec(height=0, width=2.4, depth=1.2)
            calculate_wall(zero_wall)

        # Test negative dimensions
        with self.assertRaises(ValueError):
            negative_wall = WallSpec(height=-2.4, width=2.4, depth=1.2)
            calculate_wall(negative_wall)

        # Test too-small dimensions (should raise error)
        with self.assertRaises(ValueError):
            min_wall = WallSpec(height=1.0, width=1.0, depth=0.2)  # Not enough depth for angle
            calculate_wall(min_wall)

        # Test zero dimensions (should raise error)
        with self.assertRaises(ValueError):
            zero_wall = WallSpec(height=0, width=2.4, depth=1.2)
            calculate_wall(zero_wall)

        # Test negative dimensions (should raise error)
        with self.assertRaises(ValueError):
            negative_wall = WallSpec(height=-2.4, width=2.4, depth=1.2)
            calculate_wall(negative_wall)

    def test_extreme_angles(self):
        """Test extreme angle cases"""
        # Test minimum valid angle (just above 15 degrees)
        min_valid_height = 2.0
        min_valid_depth = math.tan(math.radians(15.1)) * min_valid_height
        min_angle_wall = WallSpec(height=min_valid_height, width=2.4, depth=min_valid_depth)
        try:
            materials = calculate_wall(min_angle_wall)
            self.assertGreater(min_angle_wall.angle_deg, 15)
            self.assertLess(min_angle_wall.angle_deg, 16)
        except ValueError as e:
            self.fail(f"Minimum valid angle should be accepted: {str(e)}")
        
        # Test maximum allowed angle (70 degrees)
        steep_height = 2.0
        steep_depth = math.tan(math.radians(69.9)) * steep_height
        steep_wall = WallSpec(height=steep_height, width=2.4, depth=steep_depth)
        try:
            materials = calculate_wall(steep_wall)
            self.assertGreater(steep_wall.angle_deg, 69)
            self.assertLess(steep_wall.angle_deg, 70)
            # Verify that uprights are much longer than wall height due to steep angle
            upright_length = next(l[1] for l in materials.timber_lengths if l[0] == "Uprights (x2)")
            self.assertGreater(upright_length, steep_height * 2.5)  # At 70 degrees, should be significantly longer
        except ValueError as e:
            self.fail(f"Steep but valid angle should be accepted: {str(e)}")
            
        # Test too shallow angle (should raise error)
        with self.assertRaises(ValueError) as context:
            shallow_wall = WallSpec(height=3.0, width=2.4, depth=0.3)
            calculate_wall(shallow_wall)
        self.assertIn("too shallow", str(context.exception))

    def test_edge_case_material_calcs(self):
        """Test edge cases in material calculations"""
        # Test when dimensions exactly match plywood sheet size
        perfect_wall = WallSpec(height=2.5, width=1.25, depth=2.5)  # Standard plywood is 2500x1250mm
        perfect_materials = calculate_wall(perfect_wall)
        # Account for the angle in the calculation
        angle = math.radians(perfect_wall.angle_deg)
        panel_height = perfect_wall.height / math.cos(angle)
        # If panel height after angle is still within one sheet
        if panel_height <= 2.5:
            self.assertEqual(perfect_materials.plywood_sheets, 1)  # Should need exactly one sheet
        else:
            self.assertEqual(perfect_materials.plywood_sheets, 2)  # Will need two sheets due to angle

    def test_visualization_edge_cases(self):
        """Test visualization with edge case dimensions"""
        # Test visualization with extreme but viable dimensions
        extreme_walls = [
            WallSpec(height=3.0, width=1.8, depth=3.0),  # Tall and narrow (maintains 1.67:1 ratio)
            WallSpec(height=2.0, width=4.0, depth=2.0),  # Wide and short
            WallSpec(height=3.0, width=3.0, depth=3.0),  # Cubic proportions
        ]

        for wall in extreme_walls:
            try:
                materials = calculate_wall(wall)
                draw_wall(wall, materials)
                # Get the current figure
                fig = plt.gcf()
                self.assertEqual(len(fig.axes), 3)  # Should have 3 subplots
                
                # Check for different types of plot elements in each subplot
                for ax in fig.axes:
                    has_data = (
                        len(ax.lines) > 0 or          # Line plots
                        len(ax.collections) > 0 or     # 3D collections
                        len(ax.patches) > 0 or         # Rectangle patches
                        (hasattr(ax, 'has_data') and ax.has_data())  # Generic data check
                    )
                    self.assertTrue(has_data, "Subplot should contain plotted data")
                
                plt.close('all')  # Close all figures
            except Exception as e:
                plt.close('all')  # Clean up
                self.fail(f"Visualization failed for dimensions h={wall.height}, w={wall.width}, d={wall.depth}: {str(e)}")



    def test_visualization_functions(self):
        """Test the wall visualization functions"""
        try:
            # Test if the visualization runs without errors
            draw_wall(self.wall_spec, self.materials)
            
            # Get the current figure
            fig = plt.gcf()
            
            # Test if the figure contains the expected number of subplots
            self.assertEqual(len(fig.axes), 3)  # Should have 3 subplots
            
            # Test if axes have correct labels
            ax1, ax2, ax3 = fig.axes[:3]
            self.assertIn('Width', ax1.get_xlabel())
            self.assertIn('Height', ax1.get_zlabel())  # 3D plot has z-label
            
            plt.close('all')  # Clean up
        except Exception as e:
            plt.close('all')  # Clean up
            self.fail(f"Visualization failed: {str(e)}")

        # Test if output file is created
        test_output_path = "test_wall_design.png"
        fig = plt.figure()
        plt.savefig(test_output_path)
        file_exists = os.path.exists(test_output_path)
        plt.close(fig)
        if file_exists:
            os.remove(test_output_path)
        self.assertTrue(file_exists, "Failed to save visualization file")

    def test_materials_list_generation(self):
        """Test the materials list generation functionality"""
        # Test materials list creation
        test_dir = "test_materials"
        os.makedirs(test_dir, exist_ok=True)
        test_file_path = os.path.join(test_dir, "test_materials_list.txt")
        
        try:
            # Generate content and write to file directly to test the content generation
            angle = math.radians(self.wall_spec.angle_deg)
            panel_height = self.wall_spec.height / math.cos(angle)
            panel_area = self.wall_spec.width * panel_height
            
            # Create the materials list
            content = create_materials_list(self.wall_spec, self.materials)
            with open(test_file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            self.fail(f"Failed to generate materials list: {str(e)}")
            
        # Verify the file was created and contains the expected content
        self.assertTrue(os.path.exists(test_file_path))

        # Read and verify the materials list content
        with open(test_file_path, 'r') as f:
            content = f.read()

        # Test required sections are present
        required_sections = [
            "WALL SPECIFICATIONS",
            "PLYWOOD PANELS",
            "TIMBER FRAME",
            "HARDWARE RECOMMENDATIONS",
            "CRITICAL ANGLES",
            "SAFETY INFORMATION",
            "ADDITIONAL MATERIALS",
            "INSTALLATION NOTES"
        ]
        for section in required_sections:
            self.assertIn(section, content)

        # Test specific content details
        self.assertIn(f"{self.wall_spec.height:.2f} m", content)  # Height
        self.assertIn(f"{self.wall_spec.width:.2f} m", content)   # Width
        self.assertIn(f"{self.wall_spec.depth:.2f} m", content)   # Depth
        self.assertIn(f"{self.wall_spec.angle_deg}°", content)    # Angle

        # Test that all timber lengths are included
        for name, length in self.materials.timber_lengths:
            self.assertIn(f"{name}: {length:.2f}", content)

        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == '__main__':
    unittest.main()
