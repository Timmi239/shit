import asyncio
import concurrent.futures

connections = []


@asyncio.coroutine
def handle_connection(reader, writer):
    peername = writer.get_extra_info('peername')
    connections.append(writer)
    print('%s connected!' % str(peername))
    while True:
        try:
            data = yield from asyncio.wait_for(reader.readline(), timeout=240)
            if data:
                for connection_writer in connections:
                    if writer != connection_writer:
                        connection_writer.write(str.encode(str(connection_writer.get_extra_info('peername')) + ': '))
                        connection_writer.write(data)
            else:
                print('%s lost connection' % str(peername))
                connections.remove(peername)
                break
        except concurrent.futures.TimeoutError:
            print('%s lost connection by timeout' % str(peername))
            break
    writer.close()


def main():
    loop = asyncio.get_event_loop()
    server_gen = asyncio.start_server(handle_connection, port=8001)
    print('Server started at port 8001')
    server = loop.run_until_complete(server_gen)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
    finally:
        server.close()
        loop.close()