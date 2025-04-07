class EulerPublisherException(Exception):
    """异常基类"""
    def __init__(self, message: str, cause: Exception = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        if self.cause:
            return f"{self.message} (Cause: {type(self.cause).__name__}: {self.cause})"
        return self.message

# 文件相关异常
class NoSuchFile(EulerPublisherException):
    """文件不存在异常"""
    def __init__(self, file_path: str, cause=None):
        super().__init__(f"File not found: {file_path}", cause)
        self.file_path = file_path

# 配置相关异常
class InvalidConfig(EulerPublisherException):
    """无效配置异常"""
    def __init__(self, key: str, value: str, cause=None):
        super().__init__(f"Invalid config: {key}={value}", cause)
        self.key = key
        self.value = value

# 网络相关异常
class RequestFailed(EulerPublisherException):
    """网络请求失败"""
    def __init__(self, url: str, status_code: int = None, cause=None):
        msg = f"Request failed: {url}"
        if status_code:
            msg += f" (Status: {status_code})"
        super().__init__(msg, cause)
        self.url = url
        self.status_code = status_code
        
# 数据库相关异常
class DatabaseError(EulerPublisherException):
    """数据库异常"""
    def __init__(self, message: str, cause=None):
        super().__init__(f"Database error: {message}", cause)
        self.message = message

# 不支持的制品类型异常
class UnsupportedArtifactType(EulerPublisherException):
    """不支持的制品类型异常"""
    def __init__(self, artifact_type: str, cause=None):
        super().__init__(f"Unsupported artifact type: {artifact_type}", cause)
        self.artifact_type = artifact_type

class UnsupportedWorkflowType(EulerPublisherException):
    """不支持的工作流类型异常"""
    def __init__(self, workflow_type: str, cause=None):
        super().__init__(f"Unsupported workflow type: {workflow_type}", cause)
        self.workflow_type = workflow_type

class GitCloneFailed(EulerPublisherException):
    """Git 克隆失败异常"""
    def __init__(self, message: str, cause=None):
        super().__init__(f"Git clone faild: {message}", cause)
        self.message = message

class GitPullFailed(EulerPublisherException):
    """Git 拉取失败异常"""
    def __init__(self, message: str, cause=None):
        super().__init__(f"Git pull faild: {message}", cause)
        self.message = message

class GitPushFailed(EulerPublisherException):
    """Git 推送失败异常"""
    def __init__(self, message: str, cause=None):
        super().__init__(f"Git push faild: {message}", cause)
        self.message = message