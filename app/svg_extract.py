from svgpathtools import svg2paths2

def extract_paths_and_labels(svg_path):
    paths, attributes, svg_attributes = svg2paths2(svg_path)

    elements = []
    for attr in attributes:
        if 'd' in attr:
            elements.append({"type": "path", "d": attr["d"], "id": attr.get("id", "")})
        elif 'text' in attr:
            elements.append({"type": "text", "text": attr["text"], "id": attr.get("id", "")})
    return elements

def summarize_svg_pattern(svg_path):
    paths, attributes, svg_attributes = svg2paths2(svg_path)

    summary_lines = []
    summary_lines.append(f"{len(paths)} paths found.")

    for i, attr in enumerate(attributes):
        label = attr.get("id") or attr.get("label") or attr.get("class") or ""
        if 'd' in attr:
            d = attr["d"]
            summary_lines.append(f"path{i+1}: label={label or 'none'}, d starts with: {d[:50]}...")
        if 'text' in attr:
            summary_lines.append(f"text: {attr['text']}")

    return "\n".join(summary_lines)