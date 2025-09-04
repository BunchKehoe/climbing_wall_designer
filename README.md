# Climbing Wall Designer

A Python application for designing home climbing walls based on available space constraints. This tool helps you plan your DIY climbing wall by calculating material requirements, cutting angles, and safety parameters.

## Features

- Calculate required materials based on your available space
- Generate a visual representation of the wall design
- Determine optimal placement for T-nuts and holds
- Calculate safe loading capacity for your wall
- Provide cut lists with precise measurements and angles

## Requirements

- Python 3.7+
- Matplotlib
- NumPy
- pytest (for testing)
- pytest-cov (for test coverage)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/BunchKehoe/climbing_wall_designer.git
   cd climbing_wall_designer
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing

The project includes a comprehensive test suite covering core functionality, edge cases, and visualization components.

### Running Tests

Run all tests using:
```bash
python -m unittest tests/test_wall_designer.py
```

Or for more detailed output:
```bash
pytest tests/test_wall_designer.py -v
```

### Test Coverage

To generate a test coverage report:
```bash
pytest --cov=wall_designer tests/
```

### What's Tested

The test suite includes verification of:
- Core calculations and geometry
- Material requirements calculation
- Safety factor calculations
- Visualization generation
- Edge cases and boundary conditions
- Input validation
- File output generation

### Adding New Tests

When contributing new features, please add corresponding tests in `tests/test_wall_designer.py`. Tests should cover:
- Normal usage cases
- Edge cases and boundary conditions
- Error conditions
- Any new calculations or visualizations

## Usage

Run the script with default parameters:

```bash
python wall_designer.py
```

### Customizing Your Wall

You can modify the script to customize your wall dimensions. Open `wall_designer.py` and adjust the parameters in the `__main__` section:

```python
wall = WallSpec(
    height=2.4,  # meters
    width=2.4,   # meters
    depth=3.0,   # meters
    angle_deg=25 # degrees of overhang
)
```

Parameters explained:
- `height`: The vertical height of your climbing wall in meters
- `width`: The horizontal width of your climbing wall in meters
- `depth`: The available depth/space in meters (from the wall to how far you can extend into the room)
- `angle_deg`: The overhang angle in degrees
- `tnut_spacing`: The spacing between T-nuts in meters (default is 0.20m or 20cm)

## Output

The script generates:

1. A material list including:
   - Number of plywood sheets needed
   - T-nuts required
   - Recommended number of holds
   - Bolts required
   - Timber cut list with measurements
   - Required cutting angles

2. A safety check showing the maximum safe climber weight

3. A visual diagram of your climbing wall design

## Safety Considerations

This tool provides estimates based on general engineering principles, but local building codes and standards may vary. The safety calculations include a safety factor, but:

- Always consult with a structural engineer for larger installations
- Use appropriate fasteners and hardware for your specific wall construction
- Follow local building codes and regulations
- Test the wall thoroughly before full-weight climbing
- Consider additional reinforcement for dynamic movements

## Example Output

```
=== DIY Spray Wall Plan ===
Plywood sheets needed: 2
T-nuts required: 121
Holds recommended: 60
Bolts required: 60

Timber cut list (meters):
  Base beam: 2.40 m
  Uprights (x2): 5.29 m
  Cross braces (x2): 2.40 m
  Kicker/struts: 1.12 m

Cut Angles (degrees):
  Upright to base: 25.0°
  Top plate join: 65.0°

=== Safety Check ===
Safe maximum climber weight: 76.8 kg
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgements

This tool was generated with the assistance of AI to help climbers design safe and effective home climbing walls.
