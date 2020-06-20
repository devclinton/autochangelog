import os
from logging import getLogger, DEBUG
import click
from click.utils import LazyFile
from autochangelog.utils import processor

logger = getLogger(__name__)
LOCAL_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_MARKDOWN = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_sphinx_template.md.tmpl")
DEFAULT_GIT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_sphinx_git_template.md.tmpl")
DEFAULT_GITHUB = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_sphinx_github_template.md.tmpl")


@click.command(help="Generate changelog as a sphinx file")
@click.argument('output', type=click.File(mode='w'), default=None)
@click.option('--template', type=click.File(mode='o'),
              help="Template. Items passed as items dictionary with version and list of issues")
@processor
def sphinx(stream, output: LazyFile, allow_duplicates: bool, template: LazyFile, **kwargs):
    result = dict()

    template_types = set()
    for input_src in stream:
        items = input_src.items
        template_types.add(input_src.src)
        rendered_items = dict()
        for ver, entries in items.items():
            rendered_items[ver] = []
            for entry, commits in entries.items():
                if allow_duplicates:
                    rendered_items[ver].extend(commits)
                else:
                    rendered_items[ver].append(commits[0])

        result.update(rendered_items)

    if template is None:
        template_types = list(template_types)
        if logger.isEnabledFor(DEBUG):
            logger.debug(f"Checking for template default for types: {template_types}")
        if len(template_types) == 1:
            if template_types[0] == 'git':
                logger.debug("Loading git template")
                template = open(DEFAULT_GIT, 'r')