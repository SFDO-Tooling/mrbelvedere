class DefaultBranchSyncFailed(Exception):
    """ Failed to sync the HEAD commit on the default branch in the main repository to the default branch in the fork repository """

    def __init__(self, message, response):

        # Call the base class constructor with the parameters it needs
        super(ValidationError, self).__init__(message)

        # Now for your custom code...
        self.response = response
