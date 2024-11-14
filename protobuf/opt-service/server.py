import service_pb2_grpc as api_pb2_grpc
import service_pb2 as api_pb2
from concurrent import futures
import logging
import key
import requests

import grpc


class OtpService(api_pb2_grpc.OtpService):
    def SendOtp(self, request, context, **kwargs):
        url = f'https://a.hi-call.ru/voice/{key.key}/{request.phone}/'
        res = requests.get(url)
        if res.status_code != 200 or 'code' not in res.json():
            return grpc.StatusCode.INTERNAL
        return api_pb2.SendOtpResponse(code=res.json()['code'])

def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_OtpServiceServicer_to_server(OtpService(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()