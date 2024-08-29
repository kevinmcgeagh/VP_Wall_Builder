# VP Wall Builder

## Overview

The VP Wall Builder / OBJ Generator is a Python-based application that allows users to create 3D models of LED walls. It generates OBJ files that can be used in various 3D modelling and rendering software.

![GUI_preview](https://github.com/user-attachments/assets/a42abb5c-695f-4ef3-9470-e95e6bb02614)

## Features

- Interactive GUI for easy configuration of LED wall parameters
- Real-time 3D preview of the LED wall
- Generation of OBJ files with correct geometry and UV mapping
- Support for curved LED walls with adjustable tilt angles
- Creation of test images for visualizing cabinet layouts
- Detailed information display about the LED wall configuration

## Requirements

- Python 3.8+
- PySide6
- Matplotlib
- NumPy
- Pillow (PIL)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/kevinmcgeagh/VP_Wall_Builder.git
   cd VP_Wall_Builder
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python VP_Wall_Builder.py
   ```

2. Use the input fields to configure your LED wall:
   - Cabinets Wide: Number of cabinets horizontally
   - Cabinets High: Number of cabinets vertically
   - Tilt Angle: Angle between columns (for curved walls)
   - Cabinet Width: Width of each cabinet in millimeters
   - Cabinet Height: Height of each cabinet in millimeters
   - Tile Width: Width resolution of each tile in pixels
   - Tile Height: Height resolution of each tile in pixels

3. The 3D preview will update in real-time as you adjust the parameters.

4. Click "Generate OBJ" to create and save the OBJ file of your LED wall.

5. Click "Generate Test Image" to create a visual representation of the cabinet layout.

## Contributing

Contributions to improve the LED Surface OBJ Generator are welcome. Please feel free to submit pull requests or open issues to discuss proposed changes or report bugs.

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the PySide6, Matplotlib, and Pillow development teams for their excellent libraries.
- Inspired by the need for accurate 3D models in LED wall design and visualization.
