from mesh.standard import *
from scheme import *

__all__ = ('Service',)

class Service(Resource):
    """A service."""

    name = 'service'
    version = 1

    class schema:
        id = Token(segments=1, nonempty=True, oncreate=True, operators='equal')
        endpoint = Text()
        pid = Integer()
        dependencies = Sequence(Token(segments=1, nonempty=True), unique=True)
        registered = Boolean(readonly=True)
        required = Boolean(default=True)
        status = Enumeration('unknown starting restarting yielding ready',
            oncreate=False, operators='equal')
        stage = Token()
