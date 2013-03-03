from mesh.standard import Bundle, mount

from nucleus.resources import *

API = Bundle('nucleus',
    mount(Service, 'nucleus.controllers.service.ServiceController'),
)
