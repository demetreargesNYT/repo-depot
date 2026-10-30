import re, copy
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

def parse(text):
    p = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    p.feed(text)
    return p.close()

def ser(e, depth=0):
    ind = '    ' * depth
    if e.tag is ET.Comment:
        return f'{ind}<!--{e.text}-->\n'
    attrs = ''.join(f' {k}={quoteattr(v)}' for k, v in e.attrib.items())
    kids = list(e)
    if not kids:
        return f'{ind}<{e.tag}{attrs}/>\n'
    out = f'{ind}<{e.tag}{attrs}>\n'
    for c in kids:
        out += ser(c, depth + 1)
    return out + f'{ind}</{e.tag}>\n'

def block_range(lines, start_pat, indent=8):
    """(first, last) line indexes of the element whose opening line matches start_pat, closing at the same indent."""
    for i, l in enumerate(lines):
        if re.search(start_pat, l):
            pre = ' ' * indent
            tag = re.match(r'\s*<(\w+)', l).group(1)
            if l.rstrip().endswith('/>') or l.rstrip().endswith(f'</{tag}>'):
                return i, i
            for j in range(i + 1, len(lines)):
                if lines[j].startswith(pre + '</'):
                    return i, j
    raise KeyError(start_pat)
