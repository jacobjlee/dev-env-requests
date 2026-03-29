import enum


class OSType(str, enum.Enum):
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    CENTOS = "centos"
    FEDORA = "fedora"
    WINDOWS = "windows"
    MACOS = "macos"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class EnvironmentType(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    RESEARCH = "research"
