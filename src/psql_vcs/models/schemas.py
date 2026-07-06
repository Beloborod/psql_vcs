class CurrentSchema:
    def __init__(self, name: str, current_version: int, max_version: int):
        self.name = name
        self.current_version = current_version
        self.max_version = max_version
