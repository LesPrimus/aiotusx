class UploadException(Exception):
    pass


class LocationRetrieveException(UploadException):
    pass


class PatchDataException(UploadException):
    pass
