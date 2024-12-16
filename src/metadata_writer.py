# File: ./src/metadata_writer.py
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

def write_xmp_sidecar(image_path, rating, tags, title):
    base_name = os.path.splitext(image_path)[0]
    xmp_path = base_name + ".xmp"

    # Register namespaces once, similar to Lightroom's structure
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
        "crs": "http://ns.adobe.com/camera-raw-settings/1.0/"
    }

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
        li = ET.Element("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li", {"xml:lang": "x-default"})
        li.text = title_text
        alt.append(li)
        title_elem.append(alt)
        return title_elem

    if os.path.exists(xmp_path):
        # Parse existing XMP file
        tree = ET.parse(xmp_path)
        root = tree.getroot()

        rdf = root.find(".//rdf:RDF", namespaces)
        if rdf is None:
            rdf = ET.SubElement(root, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")

        # Find or create the main rdf:Description
        descriptions = rdf.findall("rdf:Description", namespaces)
        if len(descriptions) == 0:
            rdf_desc = ET.SubElement(rdf, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description", {
                "rdf:about": ""
            })
        else:
            rdf_desc = descriptions[0]

        # Set rating
        rdf_desc.set("{http://ns.adobe.com/xap/1.0/}Rating", str(rating))

        # Remove existing title and subject if present
        for existing_title in rdf_desc.findall("dc:title", namespaces):
            rdf_desc.remove(existing_title)
        for existing_subject in rdf_desc.findall("dc:subject", namespaces):
            rdf_desc.remove(existing_subject)

        # Add updated title and tags
        rdf_desc.append(create_dc_title(title))
        rdf_desc.append(create_dc_subject(tags))

        # Write back to file
        tree.write(xmp_path, encoding="utf-8", xml_declaration=True)
    else:
        # Create a new XMP file in a structure similar to Lightroom
        # Note: We only set namespaces on the top element (x:xmpmeta).
        # Additional namespaces are already registered globally via ET.register_namespace.
        xmpmeta = ET.Element("{adobe:ns:meta/}xmpmeta", {
            "x:xmptk": "Adobe XMP Core 7.0-c000 1.000000, 0000/00/00-00:00:00        "
        })
        rdf = ET.SubElement(xmpmeta, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")
        # rdf:Description with about="" and the rating
        rdf_desc = ET.SubElement(rdf, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description", {
            "rdf:about": ""
        })
        rdf_desc.set("{http://ns.adobe.com/xap/1.0/}Rating", str(rating))

        # Add the title and subject
        rdf_desc.append(create_dc_title(title))
        rdf_desc.append(create_dc_subject(tags))

        tree = ET.ElementTree(xmpmeta)
        tree.write(xmp_path, encoding="utf-8", xml_declaration=True)

    # Pretty-print the XML for formatting compatibility
    with open(xmp_path, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Use minidom to pretty-print
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

    # Write formatted XML back to file
    with open(xmp_path, 'wb') as f:
        f.write(pretty_xml)
