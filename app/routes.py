from flask import Flask, render_template, request, send_from_directory
from app.ai_calls import get_pattern_parameters
from app.pattern_generator import generate_bikini_top, generate_corset, generate_bikini_bottom
import os
from app.gemini_calls import get_sewing_instructions
from werkzeug.utils import secure_filename
from app.svg_extract import extract_paths_and_labels, summarize_svg_pattern
from app.resize import safe_float, scale_svg, resize_image, images_to_pdf, convert_pdf_to_images

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Get pattern type and measurements
        pattern_type = request.form.get("pattern")
        bust = safe_float(request.form.get("bust"))
        waist = safe_float(request.form.get("waist"))
        hips = safe_float(request.form.get("hips"))

        # Validate upload
        file = request.files.get("svg_file")
        if not file:
            return "Please upload a file.", 400

        filename = secure_filename(file.filename)
        upload_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        if filename.lower().endswith(".svg"):
            svg_content = file.read().decode("utf-8")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_content)
        elif filename.lower().endswith(".pdf"):
            file.save(filepath)
        else:
            return "Unsupported file type", 400

        if filename.lower().endswith(".pdf"):

            image_paths = convert_pdf_to_images(filepath, upload_dir)

            base_bust = 90
            base_waist = 70
            base_hips = 95
            user_meas_str = f"bust = {bust}, waist = {waist}, hips = {hips}"

            resize_response = get_pattern_parameters(pattern_type, "pdf file", user_meas_str)

            scale_x = scale_y = 1.0
            for line in resize_response.splitlines():
                if "scale_x" in line:
                    scale_x = float(line.split("=", 1)[1].strip())
                if "scale_y" in line:
                    scale_y = float(line.split("=", 1)[1].strip())

            if scale_y == 1.0:
                vertical = safe_float(request.form.get("torso_height"))
                base_vertical = 30
                if vertical and base_vertical:
                    scale_y = vertical / base_vertical

            resized_images = []
            for img_path in image_paths:
                output_img = img_path.replace(".png", "_resized.png")
                resize_image(img_path, scale_x, scale_y, output_img)
                resized_images.append(output_img)

            resized_pdf_path = os.path.join(upload_dir, f"resized_{filename}")
            images_to_pdf(resized_images, resized_pdf_path)

            return render_template(
                "pdf_result.html",
                images=resized_images,
                filename=os.path.basename(resized_pdf_path)
            )
        # Summarize and trim for GPT
        summary = summarize_svg_pattern(filepath)
        trimmed_summary = "\n".join(summary.splitlines()[:10])

        measurements = []
        if bust:
            measurements.append(f"bust = {bust}")
        if waist:
            measurements.append(f"waist = {waist}")
        if hips:
            measurements.append(f"hips = {hips}")

        user_meas_str = ", ".join(measurements)
        # Get GPT resize instructions
        resize_response = get_pattern_parameters(
            pattern_type, trimmed_summary, user_meas_str
        )


        # Parse scale factors
        scale_x = scale_y = 1.0
        for line in resize_response.splitlines():
            if "scale_x" in line:
                scale_x = float(line.split("=", 1)[1].strip())
            if "scale_y" in line:
                scale_y = float(line.split("=", 1)[1].strip())


        if scale_y == 1.0:
            vertical = safe_float(request.form.get("torso_height"))
            base_vertical = 30
            if vertical and base_vertical:
                scale_y = vertical / base_vertical

        # Apply scaling
        scaled_svg = scale_svg(svg_content, scale_x, scale_y)
        output_path = os.path.join("scaled", f"scaled_{filename}")
        os.makedirs("scaled", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(scaled_svg)

        # For gemini
        instructions = get_sewing_instructions(pattern_type, user_meas_str)
        print(f"Received pattern_type: {pattern_type}")

        print("Download filename:", filename)
        return render_template(
            "upload_result.html",
            bust=bust,
            waist=waist,
            hips=hips,
            scaled_svg=scaled_svg,
            filename=filename,
            instructions=instructions
        )

    return render_template("upload.html")


@app.route("/download/<filename>")
def download_scaled(filename):
    scaled_dir = os.path.join(os.path.dirname(app.root_path), "scaled")
    return send_from_directory(scaled_dir, filename, as_attachment=True)


@app.route("/generate", methods = ["POST"])
def generate():
    pattern_type = request.form["pattern"]

    if pattern_type == "bikini_top":
        bust_str = request.form.get("bust", "").strip()
        if not bust_str:
            return "Error: Bust measurement is required for bikini top.", 400
        bust = float(bust_str)

        user_meas_str = f"bust = {bust}"
        ai_response = get_pattern_parameters("bikini_top", "simple shape", user_meas_str)

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