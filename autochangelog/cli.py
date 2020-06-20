import logging
from dataclasses import dataclass
from typing import List, Any, Dict

import click
import coloredlogs
from click_plugins import with_plugins
from pkg_resources import iter_entry_points
from tqdm import tqdm

from autochangelog.changelog_context import ChangelogContext

VERBOSE = 15
NOTICE = 25
SUCCESS = 35
CRITICAL = 50

logging.addLevelName(VERBOSE, 'VERBOSE')
logging.addLevelName(NOTICE, 'NOTICE')
logging.addLevelName(SUCCESS, 'SUCCESS')
logging.addLevelName(CRITICAL, 'CRITICAL')
logger = logging.getLogger(__name__)
user_logger = logging.getLogger('user')


@click.group()
@click.option('--debug/--no-debug',  default=False)
@click.option('--verbose/--no-verbose',  default=False)
@click.pass_context
def cli(ctx, debug: bool, verbose: bool,):
    default_level = logging.DEBUG if debug else logging.INFO
    if not debug:
        default_level = VERBOSE if verbose else default_level
    coloredlogs.install(level=default_level)
    # if urlparse(src).scheme not in ('http', 'https',):
    #     if not os.path.exists(src):
    #         user_logger.error(f"The file {src} cannot be found")
    #         sys.exit(-1)

    # create context
    ctx.obj = ChangelogContext(src=None, debug=debug, verbose=verbose)


@with_plugins(iter_entry_points('autochangelog.cli_src_plugins'))
@cli.group(chain=True)
def generate():
    pass


@cli.resultcallback()
def process_commands(processors, **kwargs):
    """
    This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in tqdm(stream, total=len(processors)):
        pass


@dataclass
class SrcData:
    items: Dict[str, List[Any]]
    src: str


if __name__ == "__main__":
    cli()
