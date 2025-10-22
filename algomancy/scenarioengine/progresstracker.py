class ProgressTracker:
    def __init__(self):
        self.progress = 0

    def set_progress(self, progress):
        assert 0 <= progress <= 100, "progress must be between 0 and 100"
        self.progress = progress

    def get_progress(self):
        return self.progress

    def is_complete(self):
        return self.progress == 100