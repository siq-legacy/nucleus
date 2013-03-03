from spire.core import Dependency
from spire.mesh import ModelController
from spire.runtime import current_runtime
from spire.schema import NoResultFound, SchemaDependency

from nucleus import resources
from nucleus.engine.registry import ServiceRegistry
from nucleus.models import *

class ServiceController(ModelController):
    resource = resources.Service
    version = (1, 0)

    model = Service
    mapping = 'id endpoint pid dependencies registered required status stage'

    registry = Dependency(ServiceRegistry)
    schema = SchemaDependency('nucleus')

    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = session.query(Service).get(data['id'])

        if subject:
            subject.update_with_mapping(data, attrs='endpoint pid dependencies required')
        else:
            subject = Service.create(session, **data)

        subject.registered = True
        session.commit()
        response({'id': subject.id})
