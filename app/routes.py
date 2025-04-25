from flask import Flask, render_template, request
from app.ai_calls import get_pattern_parameters
from app.pattern_generator import generate_bikini_top, generate_corset, generate_bikini_bottom
import os
from werkzeug.utils import secure_filename
from app.svg_extract import extract_paths_and_labels, summarize_svg_pattern


app = Flask(__name__)

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def scale_svg(svg_content, scale_x=1.0, scale_y=1.0):
    import xml.etree.ElementTree as ET
    tree = ET.fromstring(svg_content)
    g = ET.Element('g')
    g.attrib['transform'] = f'scale({scale_x},{scale_y})'

    for elem in list(tree):
        g.append(elem)
        tree.remove(elem)

    tree.append(g)
    return ET.tostring(tree, encoding='unicode')

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_svg():
    if request.method == "POST":
        # Get pattern type and measurements
        pattern_type = request.form.get("pattern")
        bust = safe_float(request.form.get("bust"))
        waist = safe_float(request.form.get("waist"))
        hips = safe_float(request.form.get("hips"))

        # Validate upload
        file = request.files.get("svg_file")
        if not file or not file.filename.lower().endswith(".svg"):
            return "Please upload a valid SVG file.", 400

        svg_content = file.read().decode("utf-8")
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Summarize and trim for GPT
        summary = summarize_svg_pattern(filepath)
        trimmed_summary = "\n".join(summary.splitlines()[:10])
        user_meas_str = f"bust = {bust}, waist = {waist}, hips = {hips}"

        # Get GPT resize instructions
        resize_response = get_pattern_parameters(
            pattern_type, trimmed_summary, user_meas_str
        )
        print("GPT RESIZE INSTRUCTIONS:\n", resize_response)

        # Parse scale factors
        scale_x = scale_y = 1.0
        for line in resize_response.splitlines():
            if "scale_x" in line:
                scale_x = float(line.split("=", 1)[1].strip())
            if "scale_y" in line:
                scale_y = float(line.split("=", 1)[1].strip())

        # Apply scaling
        scaled_svg = scale_svg(svg_content, scale_x, scale_y)

        # Extract elements for UI
        elements = extract_paths_and_labels(filepath)
        return render_template(
            "upload_result.html",
            elements=elements,
            bust=bust,
            waist=waist,
            hips=hips,
            scaled_svg=scaled_svg,
        )

    return render_template("upload.html")


@app.route("/generate", methods = ["POST"])
def generate():
    pattern_type = request.form["pattern"]

    if pattern_type == "bikini_top":
        bust_str = request.form.get("bust", "").strip()
        if not bust_str:
            return "Error: Bust measurement is required for bikini top.", 400
        bust = float(bust_str)

        ai_response = get_pattern_parameters("bikini top", f"bust = {bust}")
        print(ai_response)

        try:
            for line in ai_response.splitlines():
                if "width" in line and "height" in line:
                    parts = line.replace("**", "").replace("Output:", "").split(",")
                    width = float(parts[0].split("=")[1].strip())
                    height = float(parts[1].split("=")[1].strip())
                    break
            else:
                raise ValueError("No valid line found with width and height")

            svg = generate_bikini_top(width)

        except Exception as e:
            return f"Error parsing AI response: {e}", 500

    elif pattern_type == "bikini_bottom":
        waist_str = request.form.get("waist","").strip()
        if not waist_str:
            return "Error: Waist measurement is required for bikini bottom.", 400
        waist = float(waist_str)
        ai_response = get_pattern_parameters("bikini_bottom", f"waist = {waist}")
        try:
            for line in ai_response.splitlines():
                if "width" in line and "height" in line:
                    parts = line.replace("**", "").replace("Output:", "").split(",")
                    width = float(parts[0].split("=")[1].strip())
                    height = float(parts[1].split("=")[1].strip())
                    break
            else:
                raise ValueError("No valid line found with width and height")

            svg = generate_bikini_bottom(waist)

        except Exception as e:
            return f"Error parsing AI response: {e}", 500

    elif pattern_type == 'corset':
        waist_str = request.form.get('waist', '').strip()
        bust_str = request.form.get('bust', '').strip()
        if not waist_str or not bust_str:
            return "Error: Both waist and bust measurements are required for corset.", 400
        waist = float(waist_str)
        bust = float(bust_str)
        ai_response = get_pattern_parameters("corset", f"waist = {waist}, bust = {bust}")
        print("AI RESPONSE:", ai_response)
        try:
            for line in ai_response.splitlines():
                if "top_width" in line and "bottom_width" in line and "height" in line:
                    parts = line.replace("**", "").replace("Output:", "").split(",")
                    top_width = float(parts[0].split("=")[1].strip())
                    bottom_width = float(parts[1].split("=")[1].strip())
                    height = float(parts[2].split("=")[1].strip())
                    break
            else:
                raise ValueError("No valid line found with top_width, bottom_width, and height")

            svg = generate_corset(top_width, bottom_width)

        except Exception as e:
            return f"Error parsing AI response: {e}", 500

    else:
        svg = "<p>Invalid pattern</p>"
    return render_template("result.html", svg = svg)