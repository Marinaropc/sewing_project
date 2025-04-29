import svgwrite

def generate_bikini_top(bust):
    width = bust / 5
    height = bust / 4

    svg = svgwrite.Drawing(size=("400mm","400mm"), viewBox = "0 0 200 200")
    triangle = [(10,10),(10+width, 10),(10 + width/2, 10 +height)]
    svg.add(svg.polygon(triangle, fill = "none", stroke = "black"))

    return svg.tostring()


def generate_bikini_bottom(waist):
    width = waist/4
    height = waist /6

    svg = svgwrite.Drawing(size=("200mm", "200mm"))

    path = svg.path(d="M 10 10 C 30 30, 50 30, 70 10 "
                      "C 90 30, 110 30, 130 10 "
                      "C 140 40, 110 70, 70 60 "
                      "C 50 70, 30 50, 10 40 Z",
                    fill="none", stroke="blue", stroke_width=1)
    svg.add(path)
    return svg.tostring()


def generate_corset(waist, bust):

    width = waist / 3
    height = bust / 2

    svg = svgwrite.Drawing(size=("200mm", "200mm"))
    #simple corset
    corset_path = svg.path(d=f"M 10 10 L {10 + width} 10 "
                             f"L {10 + width} {10 + height} "
                             f"L 10 {10 + height} Z",
                           fill="none", stroke="black", stroke_width=1)
    svg.add(corset_path)


    for i in range(3, 8):
        svg.add(svg.circle(center=(10 + width + 5, 10 + i * 5), r=1, fill="black"))

    return svg.tostring()


def strip_svg_namespace(elem):
    for el in elem.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]