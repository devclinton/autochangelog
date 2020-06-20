import functools
import inspect
import pluggy
from abc import ABC
from logging import getLogger, DEBUG
from typing import cast, Dict, Set, Type, Any, List
from autochangelog.plugin_specification import PluginSpecification, PLUGIN_REFERENCE_NAME

logger = getLogger(__name__)
user_logger = getLogger('user')


def is_a_plugin_of_type(value, plugin_specification: Type[PluginSpecification]) -> bool:
    """
    Determine if a value of a plugin specification is of type :class:`~autochangelog.plugin_specification.PluginSpecification`.

    Args:
        value: The value to inspect.
        plugin_specification: Plugin specification to check against.

    Returns:
        A Boolean indicating True if the plugin is of a subclass of :class:`~autochangelog.plugin_specification.PluginSpecification`,
        else False.
    """
    return inspect.isclass(value) and issubclass(value, plugin_specification) \
        and not inspect.isabstract(value) and value is not plugin_specification


def load_plugin_map(entrypoint: str, spec_type: Type[PluginSpecification], strip_all: bool = True) -> \
        Dict[str, Type[PluginSpecification]]:
    """
    Load plugins from entry point with the indicated type of specification into a map.

    .. warning::

        This could cause name collisions if plugins of the same name are installed.

    Args:
        entrypoint: The name of the entry point.
        spec_type: The type of plugin specification.
        strip_all: Pass through for get_name from Plugins. Changes names in plugin registries

    Returns:
        (Dict[str, Type[PluginSpecification]]): Returns a dictionary of name and :class:`~autochangelog.plugin_specification.PluginSpecification`.
    """
    plugins = plugins_loader(entrypoint, spec_type)
    # create instances of the plugins
    _plugin_map = dict()
    for plugin in plugins:
        if logger.isEnabledFor(DEBUG):
            logger.debug(f"Loading {str(plugin)} as {plugin.get_name()}")
        try:
            _plugin_map[plugin.get_name(strip_all)] = plugin()
        except Exception as e:
            logger.exception(e)
            user_logger.error(f'Problem loading plugin: {plugin.get_name()}')
    return _plugin_map


def plugins_loader(entry_points_name: str, plugin_specification: Type[PluginSpecification]) -> Set[PluginSpecification]:
    """
    Loads all the plugins of type :class: from entry point name. |IT_s| also supports loading plugins
    through a list of strings representing the paths to modules containing plugins.

    Args:
        entry_points_name: Entry point name for plugins.
        plugin_specification: Plugin specification to load.

    Returns:
        (Set[PluginSpecification]): All the plugins of the type indicated.
    """
    manager = pluggy.PluginManager(PLUGIN_REFERENCE_NAME)
    manager.add_hookspecs(plugin_specification)
    manager.load_setuptools_entrypoints(entry_points_name)

    manager.check_pending()
    return manager.get_plugins()


@functools.lru_cache(maxsize=32)
def discover_plugins_from(library: Any, plugin_specification: Type[PluginSpecification]) -> \
        List[Type[PluginSpecification]]:
    """
    Search a library object for plugins of type :class:`~autochangelog.plugin_specification.PluginSpecification`.

    Currently it detects module and classes. In the future support for strings will be added.

    Args:
        library: Library object to discover plugins from.
        plugin_specification: Specification to search for.

    Returns:
        List[Type[PluginSpecification]]: List of plugins.
    """

    plugins = []
    # check if the item is a module
    if inspect.ismodule(library):
        if logger.isEnabledFor(DEBUG):
            logger.debug('Attempting to load library as a module: %s', library.__name__)
        for k, v in library.__dict__.items():
            if k[:2] != '__' and is_a_plugin_of_type(v, plugin_specification):
                if logger.isEnabledFor(DEBUG):
                    logger.debug('Adding class %s from %s as a plugin', v.__name__, library.__name__)
                plugins.append(v)
    # or maybe a plugin object
    elif is_a_plugin_of_type(library, plugin_specification):
        if logger.isEnabledFor(DEBUG):
            logger.debug('Adding class %s as a plugin', library.__name__)
        plugins.append(library)
    else:
        logger.warn('Could not determine the the type of library specified by %s', str(library))
    return plugins


class PluginRegistry(ABC):
    def __init__(self, spec: Type[PluginSpecification], plugin_string: str, strip_all: bool = True) -> None:
        """
        Initialize the PluginRegistry. When strip all is false, the full plugin name will be used for names in map

        Args:
            strip_all: Whether to strip common parts of name from plugins in plugin map
        """
        self._plugins = cast(Dict[str, spec], load_plugin_map(plugin_string, spec, strip_all))

    def get_plugins(self) -> Set[PluginSpecification]:
        return set(self._plugins.values())

    def get_plugin_map(self) -> Dict[str, PluginSpecification]:
        return self._plugins
