import time

from scheme import Sequence, Token
from spire.core import Configuration, Dependency, Unit 
from spire.mesh import MeshDependency
from spire.runtime import current_runtime
from spire.schema import SchemaDependency
from spire.support.logs import LogHelper
from spire.support.threadpool import ThreadPool
from spire.util import topological_sort

from nucleus.models import *

log = LogHelper('nucleus')

class InvalidDependencyError(Exception):
    """..."""

TIMEOUTS = [(10, 1), (20, 3), (30, 10)]

def next_timeout(attempt):
    for threshold, timeout in TIMEOUTS:
        if attempt <= threshold:
            return timeout

class ServiceRegistry(Unit):
    """The service registry."""

    configuration = Configuration({
        'required_services': Sequence(Token(segments=1, nonempty=True), unique=True),
    })

    schema = SchemaDependency('nucleus')
    threads = Dependency(ThreadPool)

    def bootstrap(self):
        session = self.schema.session
        query = session.query(Service)

        for id in self.configuration.get('required_services', []):
            service = query.get(id)
            if not service:
                Service.create(session, id=id)

        for service in query:
            service.reset()

        session.commit()
        current_runtime().register_mule('service-registry', self.manage)

    def manage(self, mule):
        session = self.schema.session

        attempt = 1
        while True:
            log('info', 'attempting to verify registrations (attempt %d)', attempt)
            attempt += 1

            try:
                registered = self._verify_registrations(session)
            finally:
                session.close()

            if registered:
                log('info', 'all services registered')
                break

            timeout = next_timeout(attempt)
            if timeout is not None:
                time.sleep(timeout)
            else:
                raise Exception('missing services')

        attempt = 1
        while True:
            log('info', 'attempting to start up all services (attempt %d)', attempt)
            attempt += 1

            try:
                ready = self._manage_services(session)
            finally:
                session.close()

            if ready:
                log('info', 'all services ready')
                break

            timeout = next_timeout(attempt)
            if timeout is not None:
                time.sleep(timeout)
            else:
                raise Exception('service startup failed')

    def _enumerate_services(self, session):
        graph = {}
        query = session.query(Service)

        for service in list(query):
            graph[service] = set()
            if service.dependencies:
                for id in service.dependencies:
                    dependency = query.get(id)
                    if dependency:
                        graph[service].add(dependency)
                    else:
                        raise InvalidDependencyError(id)

        return topological_sort(graph)

    def _manage_services(self, session):
        yielding = []
        for service in self._enumerate_services(session):
            if service.status == 'ready' or not service.registered:
                continue
            
            status = service.status
            if status == 'unknown':
                service.instruct({'status': 'starting'})
            elif status in ('starting', 'restarting'):
                service.instruct({'status': 'starting', 'stage': service.stage})
            elif status == 'yielding':
                yielding.append(service)

        for service in yielding:
            if service.dependents_ready(session):
                service.instruct({'status': 'starting', 'stage': service.stage})

        session.commit()
        ready = True

        statuses = []
        for service in session.query(Service).order_by('id'):
            statuses.append('%s=%s' % (service.id, service.status))
            if service.status != 'ready':
                ready = False

        log('info', 'service status: %s' % ', '.join(statuses))

        session.rollback()
        return ready

    def _verify_registrations(self, session):
        registered = True
        registrations = []

        for service in session.query(Service).order_by('id'):
            registrations.append('%s=%r' % (service.id, service.registered))
            if not service.registered:
                registered = False

        log('info', 'registration status: %s' % ', '.join(registrations))
        session.rollback()
        return registered
