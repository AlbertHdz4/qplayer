class TextfileDatabase:

    def __init__(self, filepath):
        self.filepath=filepath

    def store_run_parameters(self, run_id, variables, iterators):
        with open(self.filepath, encoding='utf-8', mode="w") as f:
            f.write(str(run_id))

    # perform file operations

    def get_latest_run_id(self):
        with open(self.filepath, encoding='utf-8', mode="r") as f:
            try:
                run_id = int(f.readline())
            except ValueError:
                run_id=1
        return run_id
