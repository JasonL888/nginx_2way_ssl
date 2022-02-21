# nginx 2-way SSL test bed
Using python to test out 2-way SSL with nginx setup

# Pre-Requisites

## Server SSL Certificates

* Create Certificate Authority certificate
  * when prompted enter Country Name/State/etc
  * when prompted PEM pass phrase - REMEMBER it

```
cd server/certs
openssl req -x509 -new -out RootCA.crt -keyout RootCA.key -days 3650
```

* Create certificate signing request for Server ```localhost```
  * when prompted enter Country Name/State/etc
    * for CommonName - must match the FQDN in URL - in this case ```localhost```

```
openssl req -newkey rsa:2048 -out localhost.csr -pubkey -new -keyout localhost.key
```

* Using RootCA sign the Server ```localhost``` certificate

```
openssl x509 -req -in localhost.csr -CA RootCA.crt -CAkey RootCA.key -CAcreateserial -out localhost.crt -days 3650
```

* Remove passphrase from Server ```localhost``` key (else blocks nginx startup)

```
cp localhost.key localhost.key.backup
openssl rsa -in localhost.key.backup > localhost.key
```

## nginx SSL configuration
default.conf
```
server {
    listen  80;
    listen  443 ssl;

    # Turn SSL on
    #ssl on; deprecated
    server_name  localhost;
    ssl_certificate /etc/nginx/certs/localhost.crt;
    ssl_certificate_key /etc/nginx/certs/localhost.key;

    # Turn on client verification
    # simulate client cert is signed by trusted CA
    ssl_client_certificate /etc/nginx/certs/ClientRootCA.crt;
    # simulate client cert is not signed by trusted CA
    #ssl_client_certificate /etc/nginx/certs/RootCA.crt;
    ssl_verify_client on;
    ssl_verify_depth 2;


    # Any error during the connection can be found on the following path
    error_log /var/log/nginx/error.log debug;

    ssl_prefer_server_ciphers on;
    ssl_protocols TLSv1.1 TLSv1.2;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:ECDHE-RSA-RC4-SHA:ECDHE-ECDSA-RC4-SHA:RC4-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK';

    keepalive_timeout 10;
    ssl_session_timeout 5m;

    location / {
        root   /usr/share/nginx/html;
        autoindex on;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }

}
```

## Client SSL certificate

* Create Certificate Authority certificate
  * to simulate CA different from the Server CA

```
cd client
openssl req -x509 -new -out ClientRootCA.crt -keyout ClientRootCA.key -days 3650
```

* Create certificate signing request for Client
  * when prompted enter Country Name/State/etc
    * for CommonName - must match the FQDN in URL - in this case ```localhost```

```
openssl req -newkey rsa:2048 -out client.csr -pubkey -new -keyout client.key
```

* Using Client RootCA sign the Client certificate

```
openssl x509 -req -in client.csr -CA ClientRootCA.crt -CAkey ClientRootCA.key -CAcreateserial -out client.crt -days 3650
```

* Remove passphrase from Client key (for simplicity)

```
cp client.key client.key.backup
openssl rsa -in client.key.backup > client.key
```

* copy Client CA root to server (for nginx client SSL verification)

```
cp ClientRootCA.crt ..\server\certs
```

# How to Use

## Launch nginx Server
* logs are in logs folder

```
cd server
docker-compose -d up
```

## Launch python client

```
cd client
python3 client.py
```

* Client fail to SSL check Server cert  
  * if client connects to 127.0.0.1 but server cert commonName as 'localhost',
    * client issues error
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: IP address mismatch, certificate is not valid for '127.0.0.1'. (_ssl.c:1129)
```
    * server error log shows
```
2022/02/21 08:46:43 [info] 30#30: *37 SSL_do_handshake() failed (SSL: error:14094412:SSL routines:ssl3_read_bytes:sslv3 alert bad certificate:SSL alert number 42) while SSL handshaking, client: 172.20.0.1, server: 0.0.0.0:443
```

* Client succeed in SSL check of Server cert
  * if client connects to localhost and server cert commonName is 'localhost'
  * if server uses ClientRootCA.crt as 'List of Trusted CA'
    * client shows
```
good connection
200 OK
b'<html>\r\n<head><title>Index of /</title></head>\r\n<body>\r\n<h1>Index of /</h1><hr><pre><a href="../">../</a>\r\n<a href="a.txt">a.txt</a>                                              21-Feb-2022 06:08                   3\r\n</pre><hr></body>\r\n</html>\r\n'
```

    * server shows
```
2022/02/21 08:46:50 [info] 30#30: *38 client 172.20.0.1 closed keepalive connection
```

* Server fails in SSL check of Client cert
  * edit nginx default.conf to use an incorrect CA for Client and restart nginx
```
# simulate client cert is signed by trusted CA
#ssl_client_certificate /etc/nginx/certs/ClientRootCA.crt;
# simulate client cert is not signed by trusted CA
ssl_client_certificate /etc/nginx/certs/RootCA.crt;
```
  * if client connects to localhost and server cert commonName is 'localhost'
  * if server uses RootCA.crt as 'List of Trusted CA' - to simulate client cert not accepted
    * client shows
```
good connection
400 Bad Request
b'<html>\r\n<head><title>400 The SSL certificate error</title></head>\r\n<body>\r\n<center><h1>400 Bad Request</h1></center>\r\n<center>The SSL certificate error</center>\r\n<hr><center>nginx/1.19.2</center>\r\n</body>\r\n</html>\r\n'
```

    * server shows
```
2022/02/21 08:57:26 [info] 29#29: *2 client SSL certificate verify error: (21:unable to verify the first certificate) while reading client request headers, client: 172.20.0.1, server: localhost, request: "GET / HTTP/1.1", host: "localhost:8443"
```
