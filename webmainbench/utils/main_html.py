
from lxml import html



SELECT_ATTR = 'cc-select'


class HTML2TextWrapper:
    def __init__(self):
        import html2text
        self.converter = html2text.HTML2Text(bodywidth=0)
        self.converter.ignore_links = True
        self.converter.ignore_images = True
    
    def __call__(self, html_str: str, url: str = '') -> str:
        self.converter.baseurl = url
        text = self.converter.handle(html_str)
        self.converter.baseurl = ''
        return text


def html_to_element(html_str: str) -> html.HtmlElement:
    parser = html.HTMLParser(
        collect_ids=False,
        encoding='utf-8',
        remove_blank_text=True,
        remove_comments=True,
        remove_pis=True,
    )
    # Convert string to bytes if it contains an encoding declaration
    if isinstance(html_str, str) and (
        '<?xml' in html_str or '<meta charset' in html_str or 'encoding=' in html_str
    ):
        html_str = html_str.encode('utf-8')

    root = html.fromstring(html_str, parser=parser)
    return root


def element_to_html(root: html.HtmlElement, pretty_print=False) -> str:
    html_str = html.tostring(root, pretty_print=pretty_print, encoding='utf-8').decode()
    return html_str



def extract_main_html(labeled_html: str) -> str:
    """Prune a html dom tree with the given labeled html
    only keep the elements that are selected in the labeled html and their ancestors

    Args:
        labeled_html (str): the labeled html

    Returns:
        str: the pruned html
    """

    root = html_to_element(labeled_html)

    elements_to_remained: set[html.HtmlElement] = set()

    def walk_tree_to_add_elements(element: html.HtmlElement):
        style_attr = element.get('style', '')
        if 'display: none' in style_attr or 'display:none' in style_attr:
            return
        if element.get(SELECT_ATTR) == 'true':
            # When the element itself is selected, keep all elements in the subtree rooted at it
            for item in element.iter():
                elements_to_remained.add(item)
        else:
            # Check if child elements of this element are selected
            for item in element.iterchildren():
                walk_tree_to_add_elements(item)

    walk_tree_to_add_elements(root)

    all_elements_to_remained = elements_to_remained.copy()
    for element in elements_to_remained:
        # record all ancestor
        for ancestor in element.iterancestors():
            if ancestor not in all_elements_to_remained:
                all_elements_to_remained.add(ancestor)
            else:
                # if an ancestor is already in all_elements_to_remained, break
                break

    # recall not selected br tags
    last_element: html.HtmlElement = None
    for element in root.iter():
        if last_element is not None:
            if element.tag == 'br' and (last_element in all_elements_to_remained and not last_element.tag == 'br'):
                all_elements_to_remained.add(element)
            if last_element.tag == 'br' and (element in all_elements_to_remained and not element.tag == 'br'):
                all_elements_to_remained.add(last_element)
        last_element = element

    all_element_to_drop: list[html.HtmlElement] = []
    for element in root.iter():
        if element not in all_elements_to_remained:
            all_element_to_drop.append(element)
    for element in all_element_to_drop:
        if element.getparent() is not None:
            element.drop_tree()
    return element_to_html(root)
