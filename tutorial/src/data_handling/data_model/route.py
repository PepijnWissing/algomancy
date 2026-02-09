class Route:
    def __init__(
        self,
        from_id: str,
        to_id: str,
        cost: float,
    ):
        self.route_id = from_id + "_" + to_id
        self._from_id = from_id
        self._to_id = to_id
        self._cost = cost

    @property
    def cost(self):
        return self._cost

    @property
    def from_id(self):
        return self._from_id

    @property
    def to_id(self):
        return self._to_id
