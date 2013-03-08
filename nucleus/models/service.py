from mesh.exceptions import ConnectionFailed
from mesh.transport.http import Connection
from spire.schema import *

__all__ = ('Service',)

schema = Schema('nucleus')

class Service(Model):
    """A nucleus service."""

    class meta:
        schema = schema
        tablename = 'service'

    id = Token(segments=1, nullable=False, primary_key=True)
    endpoint = Text()
    pid = Integer()
    dependencies = Array(TextType)
    registered = Boolean(nullable=False, default=False)
    required = Boolean(nullable=False, default=True)
    status = Enumeration('unknown starting restarting yielding ready',
        nullable=False, default='unknown')
    stage = Token()

    def __repr__(self):
        return 'Service(id=%r, status=%r)' % (self.id, self.status)

    @classmethod
    def create(cls, session, **attrs):
        service = cls(**attrs)
        session.add(service)
        return service

    def dependents_ready(self, session):
        for dependent in self.enumerate_dependents(session):
            if dependent.status != 'ready':
                return False
        else:
            return True

    def enumerate_dependents(self, session):
        dependents = []
        for service in session.query(Service):
            dependencies = service.dependencies
            if dependencies and self.id in dependencies:
                dependents.append(service)
        return dependents

    def instruct(self, payload, ignore_response=False, timeout=None):
        connection = Connection(self.endpoint, timeout=timeout)
        try:
            response = connection.request('POST', body=payload,
                mimetype='application/json', serialize=True)
        except ConnectionFailed:
            if ignore_response:
                return
            else:
                raise

        if ignore_response:
            return
        elif not response.ok:
            raise Exception('response invalid: %s' % response.status)

        content = response.unserialize()
        if content['status'] == 'ready':
            self.status = 'ready'
            self.stage = None
        else:
            self.status = content['status']
            self.stage = content['stage']

        if self.status == 'restarting':
            self.registered = False

    def reset(self):
        self.registered = False
        self.status = 'unknown'
        self.stage = None
