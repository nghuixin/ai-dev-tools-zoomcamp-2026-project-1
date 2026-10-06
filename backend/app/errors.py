class StoreError(Exception):
    def __init__(self, error: str, status: int = 400) -> None:
        super().__init__(error)
        self.error = error
        self.status = status
