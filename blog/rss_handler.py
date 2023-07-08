import xml.etree.ElementTree as ET

def get_descriptions_and_links(xml):
    return [ {
        'description':x.find('description').text,
        'link': x.find('link').text
        } for x in ET.fromstring(xml).iter('item')]
