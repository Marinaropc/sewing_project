import xml.etree.ElementTree as ET
from PIL import Image
from pdf2image import convert_from_path
import os

def convert_pdf_to_images(pdf_path, output_folder):
    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []
    for idx, img in enumerate(images):
        image_filename = f"page_{idx+1}.png"
        image_path = os.path.join(output_folder, image_filename)
        img.save(image_path, "PNG")
        image_paths.append(image_path)
    return image_paths

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def scale_svg(svg_content, scale_x=1.0, scale_y=1.0):
    from app.pattern_generator import strip_svg_namespace  # careful import
    tree = ET.fromstring(svg_content)
    g = ET.Element('g')
    g.attrib['transform'] = f'scale({scale_x},{scale_y})'

    for elem in list(tree):
        g.append(elem)
        tree.remove(elem)

    tree.append(g)
    strip_svg_namespace(tree)
    return ET.tostring(tree, encoding='unicode')

def resize_image(image_path, scale_x=1.0, scale_y=1.0):
    img = Image.open(image_path)
    new_width = int(img.width * scale_x)
    new_height = int(img.height * scale_y)
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img_resized.save(image_path)

def images_to_pdf(image_paths, output_pdf_path):
    images = [Image.open(p).convert("RGB") for p in image_paths]
    images[0].save(output_pdf_path, save_all=True, append_images=images[1:])

