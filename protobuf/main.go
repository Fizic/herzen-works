package main

import (
	"context"
	"fmt"
	"log"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"test/github.com/otp"
)

func newGRPCClientConn(addr string) (*grpc.ClientConn, error) {
	if addr == "" {
		return nil, fmt.Errorf("address is required")
	}

	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to service at %s: %w", addr, err)
	}

	return conn, nil
}

func Request() {
	conn, err := newGRPCClientConn("localhost:50051")
	if err != nil {
		log.Fatalf("error connecting to item service: %v", err)
	}

	c := otp.NewOtpServiceClient(conn)
	res, err := c.SendOtp(context.Background(), &otp.SendOtpRequest{Phone: "phone"})
	if err != nil {
		return
	}
	fmt.Println(res.Code, err)
}

func main() {
	Request()
}
