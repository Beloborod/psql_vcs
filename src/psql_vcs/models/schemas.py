"""Describe shema to proceed migration
"""


class CurrentSchema:
    def __init__(self, name: str, current_version: int,
                 max_version: int) -> None:
        """
        Describe shema to proceed migration

        :param name: Name of database / tag of schemas chain group
        :type name: str
        :param current_version: Current database schemas version
        :type current_version: int
        :param max_version: Needed database schemas version
        to migrate onto
        :type max_version: int
        :rtype: None
        """
        self.name = name
        self.current_version = current_version
        self.max_version = max_version
