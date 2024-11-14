import service_pb2_grpc as api_pb2_grpc
import service_pb2 as api_pb2
import grpc


def run():
  with grpc.insecure_channel('0.0.0.0:50051') as channel:
    stub = api_pb2_grpc.OtpServiceStub(channel)
    response = stub.SendOtp(api_pb2.SendOtpRequest(phone="phone"))
    print("Greeter client received: " + response.code)


if __name__ == '__main__':
  run()