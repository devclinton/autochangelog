import json
import os
import pathlib
from collections import defaultdict
from dataclasses import dataclass, field
from logging import DEBUG, getLogger
from typing import List, Dict
import click
import diskcache
from dateutil.parser import parse
from github import Github, UnknownObjectException, Tag
from github.Issue import Issue
from github.Label import Label
from github.Repository import Repository
from autochangelog.data import SrcData
from autochangelog.utils import generator


logger = getLogger(__name__)
UNCATEGORIZED = 'Uncategorized'
CACHE_DIRECTORY = os.path.join(str(pathlib.Path.home()), '.autochangelog', 'github')


@click.command(help="Get changelog using a Git repo")
@click.argument('src')
@click.option("--filter-pull-requests/--no-filter-pull-requests", default=True, help="Filter pull requests")
@click.option("--topics-from-labels/--no-topics-from-labels", default=True, help="Load Changelog topics from labels")
@click.option("--filter-unlabeled/--no-unlabeled", default=True, help="Filter unlabeled issues")
@click.option("--unlabeled-label", default=UNCATEGORIZED, help="Label for unlabeled issues")
@click.option("--split-issues-between-topics/-split-issues-between-topics", default=False,
              help="Split issues with multiple labels across labels")
@click.option("--ignore-labels-file", default=None, help="Path to json file that contains a list of labels to ignore")
@click.option("--label-map-file", default=None, help="Path to json file that contains a map of label to topic")
@click.option("--version", default=None, help="Load specific version")
@click.option("--token", default=None, help="Github Token. You can also use the GITHUB_TOKEN environment variable")
@generator
@click.pass_context
def github(ctx, src: str, filter_pull_requests: bool, topics_from_labels: bool, filter_unlabeled: bool,
           unlabeled_label: str, split_issues_between_topics: bool, ignore_labels_file: str, label_map_file: str,
           version: str, token: str = None):
    gh = Github(os.getenv('GITHUB_TOKEN', token if token else ''))
    # load the git data from source specified
    repo = gh.get_repo(src)
    label_map = None
    ignore_labels = []
    if label_map_file:
        label_map = load_label_map_file(label_map_file)
    if ignore_labels_file:
        ignore_labels = load_ignore_labels_file(ignore_labels_file)
    gcs = GithubChangelogSource(repo=repo, label_map=label_map, ignore_labels=ignore_labels)
    ctx.obj.src = gcs
    if version is None:
        versions = gcs.get_versions()
        prev_version = None
        for ver in versions:
            changes = gcs.get_changes_since(ver, filter_pull_requests, topics_from_labels, filter_unlabeled,
                                            unlabeled_label, split_issues_between_topics, prev_version)
            yield SrcData(items=changes, src='github')
            prev_version = ver
    else:
        # get previous version
        versions = gcs.get_versions()
        prev_version = None
        if version in [v.name for v in versions]:
            for idx, ver in enumerate(versions):
                break
            if idx < len(versions):
                prev_version = versions[idx+1]
            version = [v for v in versions if v.name == version][0]
        else:
            raise ValueError(f"Cannot find version {version}")
        changes = gcs.get_changes_since(version, filter_pull_requests, topics_from_labels, filter_unlabeled,
                                        unlabeled_label, split_issues_between_topics, prev_version)
        yield SrcData(items=changes, src='github')


def load_label_map_file(label_map_file: str) -> Dict[str, str]:
    """
    Load the label map file

    Args:
        label_map_file: Path to label map file

    Returns:
        Dictionary of label to new label
    """
    with open(label_map_file, 'r') as lmap_in:
        label_map = json.load(lmap_in)
        new_label_map = dict()
        for label, items in label_map.items():
            for item in items:
                new_label_map[item] = label
        label_map = new_label_map
    return label_map


def load_ignore_labels_file(ignore_labels_file: str) -> List[str]:
    """
    Load Ignore labels file

    Args:
        ignore_labels_file: File to load

    Returns:
        List of labels to ignore
    """
    with open(ignore_labels_file, 'r') as ignore_in:
        ignore_labels = json.load(ignore_in)
    ignore_labels = set(ignore_labels)
    return ignore_labels


@dataclass()
class GithubChangelogSource:
    repo: Repository
    cache: diskcache.Cache = field(default=None)
    label_map: Dict[str, List[str]] = field(default=None)
    labels: List[Label] = None
    ignore_labels: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.labels = list(self.repo.get_labels())
        cache_dir = os.path.join(CACHE_DIRECTORY, self.repo.name)
        if logger.isEnabledFor(DEBUG):
            logger.debug(f'Caching issues to from {cache_dir}')
        self.cache = diskcache.Cache(cache_dir)

    @staticmethod
    def sort_item(x):
        m = parse(x.commit.commit.last_modified)
        return m

    def get_versions(self):
        """

        Returns:

        """
        if logger.isEnabledFor(DEBUG):
            logger.debug(f'Loading tags from {self.repo.name}')
        tags = list(self.repo.get_tags())
        tags.sort(key=self.sort_item)
        return tags

    @staticmethod
    def filter(issue, filter_pull_requests, tag_date, prev_ver_date) -> bool:
        """
        Filter issue. Test if issue should be filtered because it is a PR or if the PR is outside of the tag's date range
        Args:
            issue: Issue to filter
            filter_pull_requests: Should PRs be filtered out
            tag_date: What date was the tag created
            prev_ver_date: When was the previous tag created

        Returns:

        """
        return (not filter_pull_requests or
                (issue.pull_request is None or issue.pull_request.html_url != issue.html_url)
                ) and issue.closed_at and tag_date.replace(tzinfo=None) > issue.closed_at and \
               (not prev_ver_date or prev_ver_date < issue.closed_at)

    def get_changes_since(self, tag: Tag, filter_pull_requests=True, topics_from_issues: bool = True,
                          filter_unlabeled: bool = True, unlabeled_label: str = UNCATEGORIZED,
                          split_issues_between_topics: bool = True, prev_tag: Tag = None):
        """

        Args:
            tag:
            filter_pull_requests:
            topics_from_issues:
            filter_unlabeled:
            unlabeled_label:
            split_issues_between_topics:
            prev_tag:

        Returns:

        """
        # try to get the previous version first
        prev_tag_date = prev_tag.commit.commit.last_modified if prev_tag else None
        # and parse its date
        prev_tag_date = parse(prev_tag_date).replace(tzinfo=None) if prev_tag_date else None
        # do the same current version
        tag_date = tag.commit.commit.last_modified
        tag_date = parse(tag_date)
        # now what kind of results. If we include topics, it is a dictionary of list
        results = defaultdict(list) if topics_from_issues else list
        # loop over issue numbers
        for issue_number in range(1, 50000):
            # try to get issue. If it fails, we are end of our issue list
            try:
                issue = self.get_issue(issue_number)
            except UnknownObjectException:
                break
            # are we filtering issues and if so does the item meet the filter
            if self.filter(issue, filter_pull_requests, tag_date, prev_tag_date):
                # are we getting topic
                if topics_from_issues:
                    # does the issue have labels
                    if issue.labels:
                        # do we have a label map
                        if self.label_map:
                            # should we split the issues across the map
                            if split_issues_between_topics:
                                for label in issue.labels:
                                    if label.name in self.label_map and label.name not in self.ignore_labels:
                                        results[self.label_map[label.name]].append(issue)
                            # if the issues is not ignore
                            elif all([x.name not in self.ignore_labels for x in issue.labels]):
                                # execute in order of label map
                                for label in self.label_map.keys():
                                    llist = [x.name for x in issue.labels]
                                    if label in llist:
                                        results[self.label_map[label]].append(issue)
                                        break
                        else:
                            # should we split the issue?
                            if split_issues_between_topics:
                                # loop through each label and add issue there
                                for label in issue.labels:
                                    if label.name not in self.ignore_labels:
                                        results[label.name].append(issue)
                            else:
                                # use the first label
                                results[issue.labels[0].name].append(issue)
                    elif not filter_unlabeled:
                        results[unlabeled_label].append(issue)

                else:
                    results.append(issue)

        return {tag.name: results}

    def get_issue(self, issue_number) -> Issue:
        """
        Gets an issues from github or cache

        Args:
            issue_number: Issue number

        Returns:
            Github issue
        """
        issue = self.cache.get(issue_number)
        if issue is None:
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Caching issue {issue_number}')
            issue = self.repo.get_issue(issue_number)
            if issue.closed_at:
                self.cache.set(issue_number, issue, expire=60*60*24)
            else:
                self.cache.set(issue_number, issue, expire=60 * 60 * 1)
        return issue
