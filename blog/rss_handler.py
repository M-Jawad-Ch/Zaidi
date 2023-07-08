import xml.etree.ElementTree as ET

def get_descriptions(xml):
    return [ x.find('description').text for x in ET.fromstring(xml).iter('item')]
