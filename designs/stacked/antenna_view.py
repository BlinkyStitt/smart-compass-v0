"""Place compact rear-view annotations outside its crowded radio/display bay."""

import xml.etree.ElementTree as ET

import antenna


def export(route, obstacles, gaps, out):
    antenna.diagram(route, obstacles, gaps, out)
    tree = ET.parse(out)
    ns = '{http://www.w3.org/2000/svg}'
    group = tree.getroot().find(ns + 'g')
    children = list(group)
    feed = next(e for e in children if e.tag == ns+'circle' and e.get('fill') == '#111')
    for index, element in enumerate(children):
        if element.tag != ns+'text':
            continue
        if element.text in {'ANT', 'Tie 1', 'Tie 2'}:
            element.set('x', str(float(feed.get('cx')) - 14))
            element.set('text-anchor', 'end')
            if element.text == 'ANT':
                element.set('y', str(float(feed.get('cy')) + 10))
        elif element.text == 'Radio':
            # Component labels follow their projected rectangle in the shared
            # drawing. Use those bounds, rather than duplicating its transform.
            rectangle = children[index-1]
            assert rectangle.tag == ns+'rect'
            element.set('y', str(float(rectangle.get('y')) + float(rectangle.get('height')) - 4))
    tree.write(out, encoding='utf-8', xml_declaration=True)
