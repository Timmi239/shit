import asyncio
import concurrent.futures
import shelve
from enum import Enum


class Status(Enum):
    active = 1
    inactive = 0


class User:
    def __init__(self, status=Status.active):
        self.status = status

    def is_password_correct(self, password):
        return self.password == password


class Connect:
    def __init__(self, writer, reader):
        self.writer = writer
        self.reader = reader
        self.user = User()


class DataBase:
    def __init__(self):
        self.db = shelve.open('users_db')

    @asyncio.coroutine
    def is_name_exists(self, name):
        return name in self.db

    @asyncio.coroutine
    def get_password(self, name):
        return self.db[name]

    @asyncio.coroutine
    def create_user(self, user):
        self.db[user.name] = user.password


class UserHandler:
    def __init__(self):
        self.db = DataBase()
        self.connections = {}
        self.transport = Transport(self)

    @asyncio.coroutine
    def __call__(self, reader, writer):
        connect = Connect(writer, reader)
        yield from self.login(connect)

    def login(self, connect):
        Transport.send_message(connect.writer, 'Login: ')
        login = yield from Transport.read_message(connect.reader)
        Transport.send_message(connect.writer, 'Pwd: ')
        password = yield from Transport.read_message(connect.reader)
        connect.user.name = login.strip().decode('utf-8')
        connect.user.password = password
        if (yield from self.enter_to_chat_successfully(connect)):
            yield from self.transport.add_new_connection(connect)

    def enter_to_chat_successfully(self, connect):
        if not (yield from self.db.is_name_exists(connect.user.name)):
            Transport.send_message(connect.writer, 'Welcome to chat!')
            self.connections[connect.user.name] = connect
            yield from self.db.create_user(connect.user)
            print(connect.user.name + ' connected')
        else:
            pwd = yield from self.db.get_password(connect.user.name)
            if not connect.user.is_password_correct(pwd):
                Transport.send_message(connect.writer, 'Incorrect password')
                connect.writer.close()
                return False
            if self.connections.get(connect.user.name) and self.connections[connect.user.name].user.status == Status.active:
                Transport.send_message(connect.writer, 'User %s is online now' % connect.user.name)
                connect.writer.close()
                return False

            self.connections[connect.user.name] = connect
            print('User %s is online again' % connect.user.name)
        return True

    def send_message_to_all(self, initiator_connect, message):
        for user_name, connection in self.connections.items():
            if user_name != initiator_connect.user.name and connection.user.status == Status.active:
                Transport.send_message(connection.writer, initiator_connect.user.name + ': ' + message)


class Transport:
    def __init__(self, user_handler):
        self.user_handler = user_handler

    @classmethod
    def send_message(cls, writer, message):
        writer.write(str.encode(message + '\r\n'))

    @classmethod
    def read_message(cls, reader):
        return reader.readline()

    def add_new_connection(self, connect):
        while True:
            try:
                data = yield from asyncio.wait_for(self.read_message(connect.reader), timeout=120)
                if data:
                    self.user_handler.send_message_to_all(connect, data.strip().decode('utf-8'))
                else:
                    connect.user.status = Status.inactive
                    print(connect.user.name + ' lost connection')
                    break
            except concurrent.futures.TimeoutError:
                connect.user.status = Status.inactive
                print(connect.user.name + ' lost connection by timeout')
                break
        connect.writer.close()


def main():
    loop = asyncio.get_event_loop()
    handler = UserHandler()
    server_gen = asyncio.start_server(handler, port=8001)
    print('Server started at port 8001')
    server = loop.run_until_complete(server_gen)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
    finally:
        handler.db.db.close()
        server.close()
        loop.close()


if __name__ == '__main__':
    main()
