from dataclasses import dataclass
import pluggy
from abc import ABC, abstractmethod
from typing import Type
from autochangelog.changelog_context import ChangelogContext
from autochangelog.plugin_registry import PluginRegistry
from autochangelog.plugin_specification import PluginSpecification, PLUGIN_REFERENCE_NAME

get_changelog_type_spec = pluggy.HookspecMarker(PLUGIN_REFERENCE_NAME)
get_changelog_spec = pluggy.HookspecMarker(PLUGIN_REFERENCE_NAME)
get_changelog_impl = pluggy.HookimplMarker(PLUGIN_REFERENCE_NAME)
get_changelog_type_impl = pluggy.HookimplMarker(PLUGIN_REFERENCE_NAME)


@dataclass()
class ChangelogSource:
    context: ChangelogContext

    @abstractmethod
    def get_changes(self, tag1: str, tag2: str):
        pass


class ChangelogSourceSpecification(PluginSpecification, ABC):

    @classmethod
    def get_name(cls, strip_all: bool = True) -> str:
        """
        Get name of plugin. By default we remove the ChangelogSourceSpecification portion.
        Args:
            strip_all: When true, ChangelogSourceSpecification is stripped from name. When false only Specification is
             stripped

        Returns:

        """
        if strip_all:
            ret = cls.__name__.replace("ChangelogSourceSpecification", '')
        else:
            ret = cls.__name__.replace('Specification', '')
        return ret

    @get_changelog_spec
    def get(self, configuration: dict) -> ChangelogSource:
        """
        Return a new ChangeLogSource using the passed in configuration.

        Args:
            configuration: The json configuration to use

        Returns:
            The new ChangelogSource.
        """
        raise NotImplementedError("Plugin did not implement get")

    @get_changelog_type_spec
    def get_type(self) -> Type[ChangelogSource]:
        pass


class ChangelogSourcePluginRegistry(PluginRegistry):
    def __init__(self, strip_all: bool = True):
        super().__init__(ChangelogSourceSpecification, 'changelog_src', strip_all)
