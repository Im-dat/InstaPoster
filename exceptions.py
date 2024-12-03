class UploadException(Exception):
    """Exceção base para erros de upload"""
    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)

class ConfigurationException(UploadException):
    """Exceção para erros de configuração"""
    pass

class MediaProcessingException(UploadException):
    """Exceção para erros no processamento de mídia"""
    def __init__(self, message: str, file_path: str, details: dict = None):
        super().__init__(message, details)
        self.file_path = file_path

class NotificationException(UploadException):
    """Exceção para erros de notificação"""
    def __init__(self, message: str, service: str, details: dict = None):
        super().__init__(message, details)
        self.service = service 