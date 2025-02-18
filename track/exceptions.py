class REDCapError(Exception):
    """
    Exception raised for issues with REDCap.
    """

    def __init__(self, message="There was an issue with connecting to REDCap."):
        self.message = message
        super().__init__(self.message)