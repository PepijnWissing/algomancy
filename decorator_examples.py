from typing import Dict


class myClass:
    def __init__(self, id, value):
        self.id = id
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @staticmethod
    def staticmethod():
        return 1

    def to_dict(self):
        return {"id": self.id, "value": self._value}

    @classmethod
    def from_dct(cls, dct: Dict):
        return cls(dct["id"], dct["value"])

    # myclass_instance = myClass.from_dct(dct)

