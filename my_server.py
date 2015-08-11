import asyncio
import concurrent.futures
from enum import Enum


class Status(Enum):
    active = 1
    inactive = 0


class User:
    def __init__(self, name, password, connection, status=Status.active):
        self.name = name[:-2].decode('utf-8')
        self.password = password
        self.status = status
        self.connection = connection

    def __eq__(self, other_user):
        if self.name == other_user.name:
            return True
        return False


class Handler:
    def __init__(self):
        self.users = []

    def change_user_status(self, inactive_user, status, reason):
        for user in self.users:
            if user.name == inactive_user.name:
                print(reason)
                user.status = status

    def send_message_to_all(self, current_user, message):
        for user in self.users:
            if current_user.connection != user.connection:
                ChatServer.send_message(user.connection, current_user.name + ': ' + message)

    def check_user_existence(self, new_user):
        for user in self.users:
            if user.name == new_user.name and user.password == new_user.password:
                return True
        return False

    def check_user_inactivity(self, new_user):
        for user in self.users:
            if user.name == new_user.name and user.status == Status.inactive:
                return True
        return False

    @asyncio.coroutine
    def __call__(self, reader, writer):

        writer.write(str.encode('Login: '))
        login = yield from reader.readline()
        writer.write(str.encode('Pwd: '))
        password = yield from reader.readline()
        current_user = User(login, password, writer)

        if current_user not in self.users:
            ChatServer.send_message(current_user.connection, 'Welcome to chat!')
            self.users.append(current_user)
            print(current_user.name + 'connected')

        else:
            if not self.check_user_existence(current_user):
                ChatServer.send_message(current_user.connection, 'Incorrect password')
                current_user.connection.close()
                return

            if not self.check_user_inactivity(current_user):
                ChatServer.send_message(current_user.connection, 'User %s is online now' % current_user.name)
                current_user.connection.close()
                return

            self.change_user_status(current_user, Status.active, 'User %s is online again' % current_user.name)

        while True:
            try:
                data = yield from asyncio.wait_for(reader.readline(), timeout=240)
                if data:
                    self.send_message_to_all(current_user, data.decode('utf-8')[:-2])
                else:
                    self.change_user_status(current_user, Status.inactive, 'lost connection')
                    break
            except concurrent.futures.TimeoutError:
                self.change_user_status(current_user, Status.inactive, 'lost connection by timeout')
                break
        writer.close()


class ChatServer():
    def __init__(self):
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

    @classmethod
    def send_message(cls, writer, message):
        writer.write(str.encode(message + '\r\n'))


def main():
    ChatServer()


if __name__ == '__main__':
    main()
