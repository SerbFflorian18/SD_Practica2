# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import center_pb2 as center__pb2

GRPC_GENERATED_VERSION = '1.63.0'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in center_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class InternalProtocolStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.notifyMaster = channel.unary_unary(
                '/InternalProtocol/notifyMaster',
                request_serializer=center__pb2.notifyMasterRequest.SerializeToString,
                response_deserializer=center__pb2.notifyMasterResponse.FromString,
                _registered_method=True)
        self.canCommit = channel.unary_unary(
                '/InternalProtocol/canCommit',
                request_serializer=center__pb2.canCommitRequest.SerializeToString,
                response_deserializer=center__pb2.canCommitResponse.FromString,
                _registered_method=True)
        self.doCommit = channel.unary_unary(
                '/InternalProtocol/doCommit',
                request_serializer=center__pb2.doCommitRequest.SerializeToString,
                response_deserializer=center__pb2.doCommitResponse.FromString,
                _registered_method=True)
        self.doAbort = channel.unary_unary(
                '/InternalProtocol/doAbort',
                request_serializer=center__pb2.doAbortRequest.SerializeToString,
                response_deserializer=center__pb2.doAbortResponse.FromString,
                _registered_method=True)
        self.ping = channel.unary_unary(
                '/InternalProtocol/ping',
                request_serializer=center__pb2.PingRequest.SerializeToString,
                response_deserializer=center__pb2.PingResponse.FromString,
                _registered_method=True)
        self.newMaster = channel.unary_unary(
                '/InternalProtocol/newMaster',
                request_serializer=center__pb2.newMasterRequest.SerializeToString,
                response_deserializer=center__pb2.newMasterResponse.FromString,
                _registered_method=True)


class InternalProtocolServicer(object):
    """Missing associated documentation comment in .proto file."""

    def notifyMaster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def canCommit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def doCommit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def doAbort(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def newMaster(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_InternalProtocolServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'notifyMaster': grpc.unary_unary_rpc_method_handler(
                    servicer.notifyMaster,
                    request_deserializer=center__pb2.notifyMasterRequest.FromString,
                    response_serializer=center__pb2.notifyMasterResponse.SerializeToString,
            ),
            'canCommit': grpc.unary_unary_rpc_method_handler(
                    servicer.canCommit,
                    request_deserializer=center__pb2.canCommitRequest.FromString,
                    response_serializer=center__pb2.canCommitResponse.SerializeToString,
            ),
            'doCommit': grpc.unary_unary_rpc_method_handler(
                    servicer.doCommit,
                    request_deserializer=center__pb2.doCommitRequest.FromString,
                    response_serializer=center__pb2.doCommitResponse.SerializeToString,
            ),
            'doAbort': grpc.unary_unary_rpc_method_handler(
                    servicer.doAbort,
                    request_deserializer=center__pb2.doAbortRequest.FromString,
                    response_serializer=center__pb2.doAbortResponse.SerializeToString,
            ),
            'ping': grpc.unary_unary_rpc_method_handler(
                    servicer.ping,
                    request_deserializer=center__pb2.PingRequest.FromString,
                    response_serializer=center__pb2.PingResponse.SerializeToString,
            ),
            'newMaster': grpc.unary_unary_rpc_method_handler(
                    servicer.newMaster,
                    request_deserializer=center__pb2.newMasterRequest.FromString,
                    response_serializer=center__pb2.newMasterResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'InternalProtocol', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class InternalProtocol(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def notifyMaster(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/notifyMaster',
            center__pb2.notifyMasterRequest.SerializeToString,
            center__pb2.notifyMasterResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def canCommit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/canCommit',
            center__pb2.canCommitRequest.SerializeToString,
            center__pb2.canCommitResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def doCommit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/doCommit',
            center__pb2.doCommitRequest.SerializeToString,
            center__pb2.doCommitResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def doAbort(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/doAbort',
            center__pb2.doAbortRequest.SerializeToString,
            center__pb2.doAbortResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/ping',
            center__pb2.PingRequest.SerializeToString,
            center__pb2.PingResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def newMaster(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/InternalProtocol/newMaster',
            center__pb2.newMasterRequest.SerializeToString,
            center__pb2.newMasterResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
