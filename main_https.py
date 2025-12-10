import uvicorn

if __name__ == '__main__':
    # Run with HTTPS (self-signed certificate for development)
    uvicorn.run(
        "app.app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem"
    )
