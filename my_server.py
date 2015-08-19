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

    def __eq__(self, other_user):
        if self.name == other_user.name:
            return True
        return False


class Connect:
    def __init__(self, writer, reader):
        self.writer = writer
        self.reader = reader
        self.user = User()


class DataBase:
    def __init__(self):
        self.path_to_db = 'users_db'

    @asyncio.coroutine
    def is_user_exist(self, name):
        db = shelve.open(self.path_to_db)
        result = False
        if db.get(name):
            result = True
        db.close()
        return result

    @asyncio.coroutine
    def is_password_correct(self, user):
        db = shelve.open(self.path_to_db)
        result = False
        if db[user.name] == user.password:
            result = True
        db.close()
        return result

    def create_user(self, user):
        db = shelve.open(self.path_to_db)
        db[user.name] = user.password
        db.close()


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
        if (yield from self.enter_to_chat(connect)):
            yield from self.transport.add_new_connection(connect)

    def enter_to_chat(self, new_connect):
        res = yield from self.db.is_user_exist(new_connect.user.name)
        if not res:
            Transport.send_message(new_connect.writer, 'Welcome to chat!')
            self.connections[new_connect.user.name] = new_connect
            self.db.create_user(new_connect.user)
            print(new_connect.user.name + ' connected')
        else:
            res = yield from self.db.is_password_correct(new_connect.user)
            if not res:
                Transport.send_message(new_connect.writer, 'Incorrect password')
                new_connect.writer.close()
                return False

            if self.connections.get(new_connect.user.name) and self.connections.get(new_connect.user.name).status == Status.active:
                Transport.send_message(new_connect.writer, 'User %s is online now' % new_connect.user.name)
                new_connect.writer.close()
                return False

            self.connections[new_connect.user.name] = new_connect
            print('User %s is online again' % new_connect.user.name)
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
        server.close()
        loop.close()


if __name__ == '__main__':
    main()
