class Location:
    def __init__(
        self,
        id: str,
        x: float,
        y: float,
    ):
        self._id = id
        self._x = x
        self._y = y

    @property
    def id(self):
        return self._id

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y
