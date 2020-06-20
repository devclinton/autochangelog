import pluggy
PLUGIN_REFERENCE_NAME = 'autochangelog'
get_description_spec = pluggy.HookspecMarker(PLUGIN_REFERENCE_NAME)
get_description_impl = pluggy.HookimplMarker(PLUGIN_REFERENCE_NAME)


class PluginSpecification:
    """
    Base class for all plugins.
    """

    @classmethod
    def get_name(cls, strip_all: bool = True) -> str:
        """
        Get the name of the plugin. Although it can be overridden, the best practice is to use the class
        name as the plugin name.

        Returns:
            The name of the plugin as a string.
        """
        if strip_all:
            return cls.__name__.replace("Specification", "")
        else:
            return cls.__name__

    @get_description_spec
    def get_description(self) -> str:
        """
        Get a brief description of the plugin and its functionality.

        Returns:
            The plugin description.
        """
        raise NotImplementedError("The plugin did not implement a description!")
