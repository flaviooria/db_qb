class ModeOperatorError(Exception):
    """
    Exception raised when mode to execute raw sql is incorrect
    """

    def __init__(self, msg: str):
        super().__init__(msg)
        self.add_note("Valid operators are  sql or as_pd")
