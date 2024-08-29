import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QFormLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class Constants:
    WINDOW_TITLE = "LED Surface OBJ Generator"
    STYLE_SHEET = """
        QMainWindow { background-color: #1e1e1e; }
        QLabel { color: #ffffff; font-size: 14px; }
        QLineEdit { background-color: #2c2c2c; color: #ffffff; border: 1px solid #3a3a3a; padding: 5px; }
        QPushButton { background-color: #007acc; color: #ffffff; border: none; padding: 10px; font-weight: bold; }
        QPushButton:hover { background-color: #005999; }
        QTextEdit { background-color: #2c2c2c; color: #ffffff; border: 1px solid #3a3a3a; }
    """
    TITLE_STYLE = "font-size: 18px; font-weight: bold; margin-bottom: 20px;"
    INPUT_FIELDS = [
        ("Cabinets Wide", "36", "Number of cabinets in the horizontal direction"),
        ("Cabinets High", "8", "Number of cabinets in the vertical direction"),
        ("Tilt Angle", "5", "Tilt angle between columns in degrees"),
        ("Cabinet Width", "500", "Width of each cabinet in millimeters"),
        ("Cabinet Height", "500", "Height of each cabinet in millimeters"),
        ("Tile Width", "64", "Width resolution of each tile in pixels"),
        ("Tile Height", "64", "Height resolution of each tile in pixels")
    ]
    SCALE_FACTOR = 0.001  # Convert millimeters to meters


class MatplotlibCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111, projection='3d')
        super(MatplotlibCanvas, self).__init__(fig)


class LEDSurfaceGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Constants.WINDOW_TITLE)
        self.setStyleSheet(Constants.STYLE_SHEET)
        self.inputs = {}
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 1)

        title = QLabel("LED Surface Configuration")
        title.setStyleSheet(Constants.TITLE_STYLE)
        left_layout.addWidget(title)

        form_layout = QFormLayout()
        self.create_input_fields(form_layout)
        left_layout.addLayout(form_layout)

        generate_button = QPushButton("Generate OBJ")
        generate_button.clicked.connect(self.generate_obj)
        left_layout.addWidget(generate_button)

        generate_image_button = QPushButton("Generate Test Image")
        generate_image_button.clicked.connect(self.generate_test_image)
        left_layout.addWidget(generate_image_button)

        self.data_window = QTextEdit()
        self.data_window.setReadOnly(True)
        left_layout.addWidget(self.data_window)

        self.status_bar = self.statusBar()

        # Add 3D preview
        self.canvas = MatplotlibCanvas(self, width=5, height=4, dpi=100)
        main_layout.addWidget(self.canvas, 2)

        # Initial 3D preview update
        self.update_preview()

    def create_input_fields(self, form_layout):
        for label, default, tooltip in Constants.INPUT_FIELDS:
            self.inputs[label] = QLineEdit(default)
            self.inputs[label].setToolTip(tooltip)
            self.inputs[label].textChanged.connect(self.update_preview)
            form_layout.addRow(QLabel(f"{label}:"), self.inputs[label])

    def update_preview(self):
        try:
            params = self.get_input_params()
            vertices, _, _, _ = self.calculate_geometry(**params)
            self.plot_3d_preview(vertices)
            self.update_data_window(params)
        except ValueError:
            # Ignore invalid input while typing
            pass

    def plot_3d_preview(self, vertices):
        # Clear the entire figure
        self.canvas.figure.clear()

        vertices = np.array(vertices)

        # Reshape the vertices into a 2D grid
        cabinets_wide = int(self.inputs["Cabinets Wide"].text())
        cabinets_high = int(self.inputs["Cabinets High"].text())

        X = vertices[:, 0].reshape(cabinets_wide + 1, cabinets_high + 1)
        Y = vertices[:, 1].reshape(cabinets_wide + 1, cabinets_high + 1)
        Z = vertices[:, 2].reshape(cabinets_wide + 1, cabinets_high + 1)

        # Check if the wall is flat (all Z values are the same)
        is_flat = np.allclose(Z, Z[0, 0])

        # Always use 3D plot
        self.canvas.axes = self.canvas.figure.add_subplot(111, projection='3d')

        # Plot the surface with a single color
        self.canvas.axes.plot_surface(X, Z, Y, color='lightblue', edgecolor='none', alpha=0.8)

        # Plot wireframe for better visibility of the curvature
        self.canvas.axes.plot_wireframe(X, Z, Y, color='gray', alpha=0.3, linewidth=0.5)

        # Highlight the edges of the LED wall
        self.canvas.axes.plot(X[:, 0], Z[:, 0], Y[:, 0], color='r', linewidth=2)  # Bottom edge
        self.canvas.axes.plot(X[:, -1], Z[:, -1], Y[:, -1], color='r', linewidth=2)  # Top edge
        self.canvas.axes.plot(X[0, :], Z[0, :], Y[0, :], color='r', linewidth=2)  # Left edge
        self.canvas.axes.plot(X[-1, :], Z[-1, :], Y[-1, :], color='r', linewidth=2)  # Right edge

        self.canvas.axes.set_xlabel('X (Width)')
        self.canvas.axes.set_ylabel('Z (Depth)')
        self.canvas.axes.set_zlabel('Y (Height)')
        self.canvas.axes.set_title('LED Surface Preview')

        # Add disclaimer text
        disclaimer = "This preview is for general shape visualization only.\nThe actual OBJ file will more accurately represent the input data.\nClick+drag to rotate around model."
        self.canvas.axes.text2D(0.05, 0.95, disclaimer, transform=self.canvas.axes.transAxes, fontsize=9,
                                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Set the aspect ratio to be equal, handling flat walls
        x_range = np.ptp(X)
        y_range = np.ptp(Y)
        z_range = np.ptp(Z)

        # Add a small value to prevent division by zero
        max_range = max(x_range, y_range, z_range, 1e-6)
        self.canvas.axes.set_box_aspect((x_range / max_range, z_range / max_range, y_range / max_range))

        # Adjust view for flat walls
        if is_flat:
            self.canvas.axes.view_init(elev=90, azim=-90)

        # Adjust the layout and update the canvas
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def generate_obj(self):
        try:
            params = self.get_input_params()
            vertices, faces, normals, uvs = self.calculate_geometry(**params)
            self.save_obj_file(vertices, faces, normals, uvs)
        except ValueError:
            self.show_error_message("Input Error", "Please enter valid numeric values for all fields.")
        except IOError:
            self.show_error_message("File Error", "An error occurred while saving the file.")

    def get_input_params(self):
        return {
            'cabinets_wide': int(self.inputs["Cabinets Wide"].text()),
            'cabinets_high': int(self.inputs["Cabinets High"].text()),
            'tilt_angle': float(self.inputs["Tilt Angle"].text()),
            'cabinet_width': int(self.inputs["Cabinet Width"].text()),
            'cabinet_height': int(self.inputs["Cabinet Height"].text()),
            'tile_width': int(self.inputs["Tile Width"].text()),
            'tile_height': int(self.inputs["Tile Height"].text())
        }

    def calculate_geometry(self, cabinets_wide, cabinets_high, tilt_angle, cabinet_width, cabinet_height, tile_width,
                           tile_height):
        cabinet_width_m = cabinet_width * Constants.SCALE_FACTOR
        cabinet_height_m = cabinet_height * Constants.SCALE_FACTOR

        arc_length = cabinets_wide * cabinet_width_m

        if tilt_angle == 0:
            radius = float('inf')
            start_angle = 0
            central_angle = 0
            chord_length = arc_length
        else:
            central_angle = math.radians(tilt_angle * (cabinets_wide - 1))
            radius = arc_length / central_angle
            start_angle = -central_angle / 2
            chord_length = 2 * radius * math.sin(central_angle / 2)

        vertices, normals, uvs = self.generate_vertex_data(cabinets_wide, cabinets_high, cabinet_width_m,
                                                           cabinet_height_m, radius, start_angle, central_angle,
                                                           tilt_angle)
        faces = self.generate_faces(cabinets_wide, cabinets_high)

        self.print_debug_info(radius, arc_length, chord_length, central_angle)

        return vertices, faces, normals, uvs

    def generate_vertex_data(self, cabinets_wide, cabinets_high, cabinet_width_m, cabinet_height_m, radius, start_angle,
                             central_angle, tilt_angle):
        vertices, normals, uvs = [], [], []
        for x in range(cabinets_wide + 1):
            if tilt_angle == 0:
                vert_x = x * cabinet_width_m
                vert_z = 0
                normal_x, normal_z = 0, -1
            else:
                angle = start_angle + (x / cabinets_wide) * central_angle
                vert_x = radius * math.sin(angle)
                vert_z = radius * (1 - math.cos(angle))
                normal_x, normal_z = math.sin(angle), -math.cos(angle)

            for y in range(cabinets_high + 1):
                vert_y = y * cabinet_height_m
                vertices.append((vert_x, vert_y, vert_z))
                normals.append((normal_x, 0, normal_z))
                uvs.append((x / cabinets_wide, y / cabinets_high))  # Corrected UV mapping

        return vertices, normals, uvs

    def generate_faces(self, cabinets_wide, cabinets_high):
        faces = []
        for x in range(1, cabinets_wide + 1):
            for y in range(cabinets_high):
                v1 = (x - 1) * (cabinets_high + 1) + y
                v2 = x * (cabinets_high + 1) + y
                v3 = x * (cabinets_high + 1) + y + 1
                v4 = (x - 1) * (cabinets_high + 1) + y + 1
                faces.append((v1, v2, v3, v4))
        return faces

    def print_debug_info(self, radius, arc_length, chord_length, central_angle):
        print(f"Radius: {radius:.2f} m")
        print(f"Arc Length (Total Cabinet Width): {arc_length:.2f} m")
        print(f"Chord Length (Straight-line Distance): {chord_length:.2f} m")
        print(f"Central Angle: {math.degrees(central_angle):.2f} degrees")

    def update_data_window(self, params):
        cabinets_wide = params['cabinets_wide']
        cabinets_high = params['cabinets_high']
        cabinet_width = params['cabinet_width']
        cabinet_height = params['cabinet_height']
        tile_width = params['tile_width']
        tile_height = params['tile_height']
        tilt_angle = params['tilt_angle']

        total_width_mm = cabinets_wide * cabinet_width
        total_height_mm = cabinets_high * cabinet_height
        total_pixels_width = cabinets_wide * tile_width
        total_pixels_height = cabinets_high * tile_height
        total_cabinets = cabinets_wide * cabinets_high
        total_pixels = total_pixels_width * total_pixels_height

        arc_length_m = total_width_mm / 1000
        if tilt_angle == 0:
            chord_length_m = arc_length_m
        else:
            central_angle = math.radians(tilt_angle * (cabinets_wide - 1))
            radius = arc_length_m / central_angle
            chord_length_m = 2 * radius * math.sin(central_angle / 2)

        info = f"Wall Dimensions:\n"
        info += f"  Arc Length: {arc_length_m:.2f}m\n"
        info += f"  Chord Length: {chord_length_m:.2f}m\n"
        info += f"  Height: {total_height_mm / 1000:.2f}m\n"
        info += f"Total Resolution: {total_pixels_width}px x {total_pixels_height}px\n"
        info += f"Total Cabinets: {total_cabinets}\n"
        info += f"Total Pixels: {total_pixels:,}\n"
        info += f"Aspect Ratio: {total_width_mm / total_height_mm:.2f}\n"

        self.data_window.setText(info)

    def save_obj_file(self, vertices, faces, normals, uvs):
        filename, _ = QFileDialog.getSaveFileName(self, "Save OBJ File", "", "OBJ files (*.obj)")
        if filename:
            try:
                self.save_obj(filename, vertices, faces, normals, uvs)
                self.status_bar.showMessage("OBJ file generated successfully!")
            except IOError:
                raise
        else:
            self.status_bar.showMessage("OBJ file generation cancelled.")

    def save_obj(self, filename, vertices, faces, normals, uvs):
        with open(filename, 'w') as f:
            f.write("# OBJ file\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for vt in uvs:
                f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
            for vn in normals:
                f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
            for face in faces:
                f.write(f"f {face[0] + 1}/{face[0] + 1}/{face[0] + 1} {face[1] + 1}/{face[1] + 1}/{face[1] + 1} "
                        f"{face[2] + 1}/{face[2] + 1}/{face[2] + 1} {face[3] + 1}/{face[3] + 1}/{face[3] + 1}\n")

    def generate_test_image(self):
        try:
            params = self.get_input_params()
            image = self.create_test_image(**params)
            filename, _ = QFileDialog.getSaveFileName(self, "Save Test Image", "", "PNG files (*.png)")
            if filename:
                image.save(filename)
                self.status_bar.showMessage("Test image generated successfully!")
            else:
                self.status_bar.showMessage("Test image generation cancelled.")
        except ValueError:
            self.show_error_message("Input Error", "Please enter valid numeric values for all fields.")
        except IOError:
            self.show_error_message("File Error", "An error occurred while saving the file.")

    def create_test_image(self, cabinets_wide, cabinets_high, tile_width, tile_height, **kwargs):
        total_width = cabinets_wide * tile_width
        total_height = cabinets_high * tile_height

        image = Image.new('RGB', (total_width, total_height), color='white')
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        for x in range(cabinets_wide):
            for y in range(cabinets_high):
                left = x * tile_width
                top = y * tile_height
                right = left + tile_width
                bottom = top + tile_height

                # Draw checkerboard pattern
                if (x + y) % 2 == 0:
                    draw.rectangle([left, top, right, bottom], fill='lightgray')

                # Draw cabinet border
                draw.rectangle([left, top, right, bottom], outline='black')

                # Generate a unique color for each cabinet
                color = f"#{hash((x, y)) % 0xFFFFFF:06x}"

                # Draw cabinet ID and color
                cabinet_id = f"{x},{y}"
                text_bbox = draw.textbbox((left, top), cabinet_id, font=font)
                text_position = (left + (tile_width - text_bbox[2] + text_bbox[0]) // 2,
                                 top + (tile_height - text_bbox[3] + text_bbox[1]) // 2)
                draw.text(text_position, cabinet_id, fill=color, font=font)

        return image

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)
        self.status_bar.showMessage(f"Error: {message}")


def main():
    app = QApplication(sys.argv)
    window = LEDSurfaceGenerator()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()