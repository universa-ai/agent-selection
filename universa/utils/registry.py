import uuid


class ItemExists(Exception):
    __name__ = "ItemExists"
    __desc__ = "Item `{}` already exists in the registry with value `{}`."

    def __init__(self, key, value, **kwargs) -> None:
        desc = self.__desc__.format(key, value)
        super().__init__(*(desc, ), **kwargs)

class ItemNotFound(Exception):
    __name__ = "ItemNotFound"
    __desc__ = "Item `{}` does not exist in the registry."

    def __init__(self, key, **kwargs) -> None:
        desc = self.__desc__.format(key)
        super().__init__(*(desc, ), **kwargs)

class Registry:
    """
    Base class for registers, such as object registry.
    """
    def __init__(self):
        self.registry = {}

    def register(self, key, value):
        if key not in self:
            self[key] = value
        raise ItemExists(
            key, self[key]
        )
        
    def unregister(self, key):
        del self[key]
        
    def __getitem__(self, key):
        if key not in self.registry:
            raise ItemNotFound(key)
        return self.registry.get(key)
    
    def __setitem__(self, key, value):
        self.registry[key] = value
        
    def __len__(self):
        return len(self.registry)
    
    def __delitem__(self, key):
        del self.registry[key]
    
    def __iter__(self):
        return iter(self.registry)
    
    def __contains__(self, key):
        return key in self.registry
    
    def __str__(self):
        return str(self.registry)
    
    def __repr__(self):
        return repr(self.registry)
    
def generate_id(id_step: int = 1) -> str:
    """
    Generate a unique ID.
    """
    return str(uuid.uuid4())[::max(1, id_step)]
