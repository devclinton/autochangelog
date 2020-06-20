import os
from collections import defaultdict
from logging import getLogger, DEBUG
import click
from click.utils import LazyFile
from jinja2 import Environment, BaseLoader
from autochangelog.json_output import get_object_base_level
from autochangelog.utils import processor

logger = getLogger(__name__)
LOCAL_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_MARKDOWN = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_markdown_template.md.tmpl")
DEFAULT_GIT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_markdown_git_template.md.tmpl")
DEFAULT_GITHUB = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_markdown_github_template.md.tmpl")
DEFAULT_GITHUB_VERSION = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "default_markdown_github_version_template.md.tmpl"
)
DEFAULT_GITHUB_INDEX_VERSION = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "default_markdown_github_version_index_template.md.tmpl"
)


def is_dict(value):
    return isinstance(value, dict)


@click.command(help="Generate changelog as a Markdown file")
@click.option('--output', default=None)
@click.option('--allow-duplicates/--no-allow-duplicates', default=False)
@click.option('--split-versions/--no-split-versions', default=False)
@click.option('--template', type=click.File(mode='o'),
              help="Template. Items passed as items dictionary with version and list of issues")
@processor
@click.pass_context
def markdown(ctx, stream, output: LazyFile, allow_duplicates: bool, split_versions: bool, template: LazyFile, **kwargs):
    result = dict()

    template_types = set()
    template, template_types = None, set()
    templates = dict()
    for input_src in stream:
        # get items from source
        items = input_src.items
        # get depth
        dl = get_object_base_level(items)
        # get template types
        template_types.add(input_src.src)
        # get template type
        template = get_template(
            template,
            [input_src.src] if split_versions else template_types,
            split_versions
        )
        rendered_items = defaultdict(list) if dl <= 2 else defaultdict(lambda: defaultdict(list))
        for ver, entries in items.items():
            for entry, commits in entries.items():
                # add the nested commits
                if isinstance(commits, list):
                    rendered_items[ver][entry].extend(commits)
                else:
                    # otherwise decide if we should allow duplicates
                    if allow_duplicates:
                        rendered_items[ver].extend(commits)
                    else:
                        rendered_items[ver].append(commits[0])

            # if we are splitting versions, render those now
            if split_versions:
                if output and (os.path.exists(output) and os.path.isdir(output)):
                    raise ValueError("Output must be a directory")
                elif output and not os.path.exists(output):
                    os.makedirs(output, exist_ok=True)
                render_template(
                    ctx, os.path.join(output, f'changelog_{ver}.md') if output else None,
                    rendered_items[ver],
                    template,
                    templates,
                    version=ver
                )

        result.update(rendered_items)
    # if we are splitting versions, we should render the index now
    if split_versions:
        # render index
        idx_template = get_index_template(template_types)
        render_template(ctx, os.path.join(output, f'changelog.md') if output else None, result, idx_template)
    else:
        render_template(ctx, output, result, template)
    yield True


def render_template(ctx, output: str, items, template, templates=None, **kwargs):
    if template is None:
        logger.debug("Loading default markdown")
        template = LazyFile(DEFAULT_MARKDOWN, 'r')
    elif isinstance(template, str):
        template = LazyFile(template, 'r')
    if templates is None:
        templates = dict()
    if template.name in templates:
        template_src = templates[template.name]
    else:
        env = Environment(loader=BaseLoader)
        env.filters['is_dict'] = is_dict
        template_src = env.from_string(template.read())
        templates[template.name] = template_src

    if logger.isEnabledFor(DEBUG):
        logger.debug(f"Sending template items value of {items}")
        if output:
            logger.debug(f"Writing to {output.name}")
    render_args = dict(items=items, context=ctx.obj, **kwargs)
    result = template_src.render(render_args)
    if output:
        with open(output, 'w') as out:
            out.write(result)
    else:
        print(result)


def get_template(template, template_types, split_versions):
    if template is None:
        template_types = list(template_types)
        if logger.isEnabledFor(DEBUG):
            logger.debug(f"Checking for template default for types: {template_types}")
        if len(template_types) == 1:
            if template_types[0] == 'git':
                logger.debug("Loading git template")
                template = LazyFile(DEFAULT_GIT_VERSION, 'r')
            elif template_types[0] == 'github':
                logger.debug("Loading github template")
                template = LazyFile(DEFAULT_GITHUB_VERSION if split_versions else DEFAULT_GITHUB, 'r')
    return template


def get_index_template(template_types):
    template = None
    template_types = list(template_types)
    if logger.isEnabledFor(DEBUG):
        logger.debug(f"Checking for template default for types: {template_types}")
    if len(template_types) == 1:
        if template_types[0] == 'git':
            logger.debug("Loading git template")
            template = LazyFile(DEFAULT_GIT_INDEX_VERSION)
        elif template_types[0] == 'github':
            logger.debug("Loading github template")
            template = LazyFile(DEFAULT_GITHUB_INDEX_VERSION)
    return template