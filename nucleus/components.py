from spire.core import Component, Dependency
from spire.mesh import MeshServer
from spire.runtime import onstartup

from nucleus.bundles import *
from nucleus.engine.registry import ServiceRegistry
from nucleus.resources import *

class Nucleus(Component):
    api = MeshServer.deploy(bundles=[API])
    registry = Dependency(ServiceRegistry)

    @onstartup()
    def bootstrap(self):
        self.registry.bootstrap()
