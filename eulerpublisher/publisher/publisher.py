# coding=utf-8

# global varibles
PUBLISH_FAILED = 1
PUBLISH_SUCCESS = 0
ARCHS = ["x86_64", "aarch64"]


# parent `publisher`
class Publisher:

    def __init__():
        pass

    # prepare stage
    def prepare():
        pass

    # `build` method that can be executed separately
    def build():
        pass

    # `push` method that can be executed separately
    def push():
        pass

    # The situation where `build` and `push` must be
    # executed at the same time
    def build_and_push():
        pass

    # One-click publishing
    def publish():
        pass
