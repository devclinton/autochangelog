import re
from collections import defaultdict
from logging import getLogger
import click
from dataclasses import dataclass, field
from typing import List
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, GIT_SORT_TIME
from autochangelog.data import SrcData
from autochangelog.utils import generator

logger = getLogger(__name__)
user_logger = getLogger('user')


@click.command(help="Get changelog using a Git repo")
@click.argument('src', type=click.Path(exists=True))
@click.option("--version", default=None)
@click.option(
    '--exclude', '-e', multiple=True,
    default=['Merge branch', 'Merge pull request', 'Merge remote-tracking branch', 'Bump version', 'Fix linting']
)
@generator
@click.pass_context
def git(ctx, src, version, exclude):
    # load the git data from source specified
    repo = Repository(src)
    gcs = GitChangelogSource(repo=repo, excluded_messages=exclude)
    ctx.obj.src = gcs
    if version is None:
        versions = gcs.get_versions()
        for ver in versions:
            changes = gcs.get_changes_since(ver)
            yield SrcData(items=changes, src='git')
    else:
        changes = gcs.get_changes_since(version)
        yield SrcData(items=changes, src='git')


@dataclass()
class GitChangelogSource:
    repo: Repository
    issues: List = None
    excluded_messages: List = field(default_factory=list)
    __release_expr = re.compile('.*?([0-9.]+).*?')

    def get_versions(self):
        regex = re.compile('^refs/tags')
        tags = list(sorted(list(filter(lambda r: regex.match(r), self.repo.listall_references()))))
        tags.append('HEAD')
        tags.reverse()
        return tags

    def get_changes_since(self, tag):
        tags = self.get_versions()
        release_ranges = dict()
        release_notes = defaultdict(lambda: defaultdict(list))
        for index, other_tag in enumerate(tags):
            if other_tag == tag:
                ref = self.repo.lookup_reference(other_tag)
                next_release = self.repo.lookup_reference(tags[index + 1]) if index != len(tags) - 1 else 'Beginning'
                walker = self.repo.walk(
                    ref.target if ref.name != 'HEAD' else self.repo.head.target,
                    GIT_SORT_TOPOLOGICAL | GIT_SORT_TIME
                )
                rm = self.__release_expr.match(other_tag)
                release_name = rm.group(1) if rm else 'Development'
                if not isinstance(next_release, str):
                    walker.hide(next_release.target)
                for commit in walker:
                    if release_name not in release_ranges:
                        if next_release and not isinstance(next_release, str):
                            nc = self.repo.walk(next_release.target)
                            nc = next(nc)
                            nc = nc.commit_time
                        else:
                            nc = None
                        release_ranges[release_name] = (nc, commit.commit_time)
                    if next_release and (not isinstance(next_release, str) and commit.oid == next_release.target):
                        break
                    if not any([x in commit.message for x in self.excluded_messages]):
                        release_notes[release_name][commit.message.strip()].append(commit)

        return release_notes

