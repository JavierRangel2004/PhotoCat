# File: ./src/metadata_writer.py
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


def write_xmp_sidecar(image_path, rating, tags, title, genre_result=None):
    """
    Write an XMP sidecar file for image_path.

    genre_result (optional): dict from genre_decision.make_genre_decision()
        {genre, confidence, review_status: "auto"|"review"|"skip", ...}

    Genre is written only when review_status is "auto" or "review".
    When review_status is "review", the tag "genre-needs-review" is appended.
    When review_status is "skip" (or genre_result is None), no genre tag is written.
    """
    base_name = os.path.splitext(image_path)[0]
    xmp_path = base_name + ".xmp"

    ET.register_namespace("x", "adobe:ns:meta/")
    ET.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    ET.register_namespace("xmp", "http://ns.adobe.com/xap/1.0/")
    ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    ET.register_namespace("crs", "http://ns.adobe.com/camera-raw-settings/1.0/")

    namespaces = {
        "x": "adobe:ns:meta/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xmp": "http://ns.adobe.com/xap/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "crs": "http://ns.adobe.com/camera-raw-settings/1.0/",
    }

    # Build final tags list, optionally including genre
    final_tags = list(tags)
    if genre_result is not None:
        review_status = genre_result.get("review_status", "skip")
        if review_status != "skip":
            genre_tag = genre_result["genre"]
            if genre_tag not in final_tags:
                final_tags.append(genre_tag)
            if review_status == "review" and "genre-needs-review" not in final_tags:
                final_tags.append("genre-needs-review")

    def create_dc_subject(tags_list):
        subject_elem = ET.Element("{http://purl.org/dc/elements/1.1/}subject")
        bag = ET.Element("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag")
        for tag in tags_list:
            li = ET.Element("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li")
            li.text = tag
            bag.append(li)
        subject_elem.append(bag)
        return subject_elem

    def create_dc_title(title_text):
        title_elem = ET.Element("{http://purl.org/dc/elements/1.1/}title")
        alt = ET.Element("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Alt")
        li = ET.Element(
            "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li", {"xml:lang": "x-default"}
        )
        li.text = title_text
        alt.append(li)
        title_elem.append(alt)
        return title_elem

    if os.path.exists(xmp_path):
        tree = ET.parse(xmp_path)
        root = tree.getroot()

        rdf = root.find(".//rdf:RDF", namespaces)
        if rdf is None:
            rdf = ET.SubElement(root, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")

        descriptions = rdf.findall("rdf:Description", namespaces)
        if len(descriptions) == 0:
            rdf_desc = ET.SubElement(
                rdf,
                "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description",
                {"rdf:about": ""},
            )
        else:
            rdf_desc = descriptions[0]

        rdf_desc.set("{http://ns.adobe.com/xap/1.0/}Rating", str(rating))

        for existing_title in rdf_desc.findall("dc:title", namespaces):
            rdf_desc.remove(existing_title)
        for existing_subject in rdf_desc.findall("dc:subject", namespaces):
            rdf_desc.remove(existing_subject)

        rdf_desc.append(create_dc_title(title))
        rdf_desc.append(create_dc_subject(final_tags))

        tree.write(xmp_path, encoding="utf-8", xml_declaration=True)
    else:
        xmpmeta = ET.Element(
            "{adobe:ns:meta/}xmpmeta",
            {"x:xmptk": "Adobe XMP Core 7.0-c000 1.000000, 0000/00/00-00:00:00        "},
        )
        rdf = ET.SubElement(xmpmeta, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")
        rdf_desc = ET.SubElement(
            rdf,
            "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description",
            {"rdf:about": ""},
        )
        rdf_desc.set("{http://ns.adobe.com/xap/1.0/}Rating", str(rating))
        rdf_desc.append(create_dc_title(title))
        rdf_desc.append(create_dc_subject(final_tags))

        tree = ET.ElementTree(xmpmeta)
        tree.write(xmp_path, encoding="utf-8", xml_declaration=True)

    with open(xmp_path, "r", encoding="utf-8") as f:
        xml_string = f.read()

    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

    with open(xmp_path, "wb") as f:
        f.write(pretty_xml)
