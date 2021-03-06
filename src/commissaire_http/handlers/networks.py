# Copyright (C) 2016  Red Hat, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Networks handlers.
"""

from commissaire import models
from commissaire import bus as _bus
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire_http.handlers import (
    LOGGER, JSONRPC_Handler, create_jsonrpc_response, create_jsonrpc_error)


def _register(router):
    """
    Sets up routing for clusters.

    :param router: Router instance to attach to.
    :type router: commissaire_http.router.Router
    :returns: The router.
    :rtype: commissaire_http.router.Router
    """
    from commissaire_http.constants import ROUTING_RX_PARAMS

    # Networks
    router.connect(
        R'/api/v0/networks/',
        controller=list_networks,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=get_network,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=create_network,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=delete_network,
        conditions={'method': 'DELETE'})

    return router


@JSONRPC_Handler
def list_networks(message, bus):
    """
    Lists all networks.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        container = bus.storage.list(models.Networks)
        return create_jsonrpc_response(
            message['id'],
            [network.name for network in container.networks])
    except Exception as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


@JSONRPC_Handler
def get_network(message, bus):
    """
    Gets a specific network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        name = message['params']['name']
        network = bus.storage.get_network(name)
        return create_jsonrpc_response(message['id'], network.to_dict_safe())
    except _bus.StorageLookupError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


@JSONRPC_Handler
def create_network(message, bus):
    """
    Creates a new network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        name = message['params']['name']
        LOGGER.debug('create_network params: %s', message['params'])
        # Check to see if we already have a network with that name
        input_network = models.Network.new(**message['params'])
        saved_network = bus.storage.get(input_network)
        LOGGER.debug(
            'Creation of already exisiting network "%s" requested.', name)

        # If they are the same thing then go ahead and return success
        if saved_network.to_dict() == input_network.to_dict():
            return create_jsonrpc_response(
                message['id'], saved_network.to_dict_safe())

        # Otherwise error with a CONFLICT
        return create_jsonrpc_error(
            message,
            'A network with that name already exists.',
            JSONRPC_ERRORS['CONFLICT'])
    except _bus.StorageLookupError as error:
        LOGGER.info(
            'Attempting to create new network: "%s"', message['params'])

    # Create the new network
    try:
        input_network = models.Network.new(**message['params'])
        saved_network = bus.storage.save(input_network)
        return create_jsonrpc_response(
            message['id'], saved_network.to_dict_safe())
    except models.ValidationError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


@JSONRPC_Handler
def delete_network(message, bus):
    """
    Deletes an exisiting network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        name = message['params']['name']
        LOGGER.debug('Attempting to delete network "%s"', name)
        bus.storage.delete(models.Network.new(name=name))
        return create_jsonrpc_response(message['id'], [])
    except _bus.StorageLookupError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug('Error deleting network: %s: %s', type(error), error)
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])
