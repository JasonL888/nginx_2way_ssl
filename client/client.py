import http.client
import json
import ssl

def ssl_connect(host, client_cert_file, client_cert_key):
    # Defining parts of the HTTP request
    request_url='/'
    #request_headers = {
    #    'Content-Type': 'application/json'
    #}
    #request_body_dict={
    #    'test_1': 'apple',
    #    'test_2': 100
    #}

    # Define the client certificate settings for https connection
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(certfile=client_cert_file, keyfile=client_cert_key)
    context.load_verify_locations(cafile=server_ca_trusted)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True

    # Create a connection to submit HTTP requests
    try:
        connection = http.client.HTTPSConnection(host, port=8443, context=context)
        connection.request(method="GET",url=request_url)
        response = connection.getresponse()
        print(response.status, response.reason)
        data = response.read()
        print(data)
    except Exception as ex:
        print( ex )

if __name__ == '__main__':
    client_cert_file = 'client.crt'
    client_cert_key= 'client.key'
    server_ca_trusted = '../server/certs/RootCA.crt'

    print('\nsimulate SSL error with mismatch between server FQDN and cert commonName')
    ssl_connect('127.0.0.1', client_cert_file, client_cert_key)
    pause=input('Press enter to continue')

    # good SSL connection
    print('\ngood connection')
    ssl_connect('localhost', client_cert_file, client_cert_key)
