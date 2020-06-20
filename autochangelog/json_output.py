from collections import defaultdict
from logging import getLogger, DEBUG

import click
import json as js

from click.utils import LazyFile
from github.Issue import Issue
from pygit2._pygit2 import Commit

from autochangelog.utils import processor
from jinja2 import Template
logger = getLogger(__name__)


def get_object_base_level(item, level=0):
    if isinstance(item, dict):
        return get_object_base_level(item[list(item.keys())[0]], level+1)
    elif isinstance(item, list):
        return get_object_base_level(item[0], level+1)
    elif isinstance(item, (Issue, Commit)):
        return level+1
    else:
        return level+1


def get_default_template(item) -> str:
    """
    Get the default json template for each item
    Args:
        item: Item

    Returns:
        Default template string
    """
    if isinstance(item, dict):
        return get_default_template(item[list(item.keys())[0]])
    elif isinstance(item, list):
        return get_default_template(item[0])
    elif isinstance(item, Issue):
        template = "{{ item.title }}"
    elif isinstance(item, Commit):
        template = "{{ item.message }}"
    else:
        template = "{{ item|string }}"
    if logger.isEnabledFor(DEBUG):
        logger.debug(f"Default Template is {template}")
    return template


@click.command(help="Generate changelog as a JSON")
@click.option('--output', type=click.File(mode='w'), default=None)
@click.option('--sort-keys/--no-store-keys', default=False, help="Sort keys")
@click.option('--indent', type=click.IntRange(min=0), default=None, help="About of spaces to ident")
@click.option('--template', type=str, default=None, help="Template")
@processor
@click.pass_context
def json(ctx, stream, output: LazyFile, sort_keys: bool, indent: int, template: str, **kwargs):
    result = dict()
    for input_src in stream:
        items = input_src.items
        dl = get_object_base_level(items)
        # labeled changelog
        if template is None:
            template = get_default_template(items)
        rendered_items = dict() if dl == 2 else defaultdict(lambda: defaultdict(list))
        template_src = Template(template)
        for ver, entry in items.items():
            if dl <= 2:
                rendered_items[ver] = []
            for item in entry:
                if dl > 2:
                    for sub_item in entry[item]:
                        rendered_items[ver][item].append(template_src.render(item=sub_item))
                else:
                    rendered_items[ver].append(template_src.render(item=item))

        result.update(rendered_items)
    if output:
        js.dump(result, output, sort_keys=sort_keys, indent=indent)
    else:
        print(js.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))
    yield True
