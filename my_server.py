import asyncio
import concurrent.futures
from enum import Enum


class Status(Enum):
    active = 1
    inactive = 0


class User:
    def __init__(self, name, password, connection, status=Status.active):
        self.name = name[:-2]
        self.password = password
        self.status = status
        self.connection = connection

    def search_user(self, users_list):
        for user in users_list:
            if user.name == self.name:
                if user.password == self.password:
                    if user.status == Status.inactive:
                        user.status = Status.active
                        return {True: 'User %s is online\r\n' % user.name}
                    else:
                        return {False: 'This user already online\r\n'}
                else:
                    return {False: 'Invalid password\r\n'}
        users_list.append(self)
        return {True: 'New user %s added\r\n' % self.name}


class Handler:
    def __init__(self):
        self.users = []

    def change_status_to_inactive(self, inactive_user):
        for user in self.users:
            if user.name == inactive_user.name:
                user.status = Status.inactive

    @asyncio.coroutine
    def __call__(self, reader, writer):
        writer.write(str.encode('Login:'))
        login = yield from asyncio.wait_for(reader.readline(), timeout=20)
        writer.write(str.encode('Pwd:'))
        password = yield from asyncio.wait_for(reader.readline(), timeout=20)
        current_user = User(login, password, writer)

        result = current_user.search_user(self.users)

        writer.write(str.encode(result[list(result.keys())[0]]))
        if not list(result.keys())[0]:
            writer.close()


        print('%s connected!' % current_user.name)
        while True:
            try:
                data = yield from asyncio.wait_for(reader.readline(), timeout=240)
                if data:
                    for user in self.users:
                        if writer != user.connection:
                            user.connection.write(str.encode(current_user.name.decode("utf-8") + ': '))
                            user.connection.write(data)
                else:
                    print('%s lost connection' % str(current_user.name))
                    self.change_status_to_inactive(current_user)
                    break
            except concurrent.futures.TimeoutError:
                print('%s lost connection by timeout' % str(current_user.name))
                self.change_status_to_inactive(current_user)
                break
        writer.close()


def main():
    loop = asyncio.get_event_loop()
    handler = Handler()
    server_gen = asyncio.start_server(handler, port=8001)
    print('Server started at port 8001')
    server = loop.run_until_complete(server_gen)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
    finally:
        server.close()
        loop.close()