import asyncio
import concurrent.futures
from enum import Enum


class Status(Enum):
    active = 1
    inactive = 0


class User:
    def __init__(self, writer, reader, status=Status.active):
        self.status = status
        self.writer = writer
        self.reader = reader

    def __eq__(self, other_user):
        if self.name == other_user.name:
            return True
        return False

    def change_status(self, status):
        self.status = status


class UserHandler:
    def __init__(self):
        self.users = {}
        self.transport = Transport(self)

    @asyncio.coroutine
    def __call__(self, reader, writer):
        user = User(writer, reader)
        yield from self.login(user)

    def login(self, user):
        Transport.send_message(user.writer, 'Login: ')
        login = yield from Transport.read_message(user.reader)
        Transport.send_message(user.writer, 'Pwd: ')
        password = yield from Transport.read_message(user.reader)
        user.name = login.strip().decode('utf-8')
        user.password = password
        if self.enter_to_chat(user):
            yield from self.transport.add_new_connection(user)

    def enter_to_chat(self, new_user):
        if not self.users.get(new_user.name):
            Transport.send_message(new_user.writer, 'Welcome to chat!')
            self.users[new_user.name] = new_user
            print(new_user.name + ' connected')
        else:
            if self.users.get(new_user.name).password != new_user.password:
                Transport.send_message(new_user.writer, 'Incorrect password')
                new_user.writer.close()
                return False

            if self.users.get(new_user.name).status == Status.active:
                Transport.send_message(new_user.writer, 'User %s is online now' % new_user.name)
                new_user.writer.close()
                return False

            self.users[new_user.name].status = Status.active
            print('User %s is online again' % new_user.name)
        return True

    def send_message_to_all(self, initiator_user, message):
        for user_name, user in self.users.items():
            if user_name != initiator_user.name:
                Transport.send_message(user.writer, initiator_user.name + ': ' + message)


class Transport:
    def __init__(self, user_handler):
        self.user_handler = user_handler

    @classmethod
    def send_message(cls, writer, message):
        writer.write(str.encode(message + '\r\n'))

    @classmethod
    def read_message(cls, reader):
        return reader.readline()

    def add_new_connection(self, user):
        while True:
            try:
                data = yield from asyncio.wait_for(self.read_message(user.reader), timeout=120)
                if data:
                    self.user_handler.send_message_to_all(user, data.decode('utf-8')[:-2])
                else:
                    user.status = Status.inactive
                    print(user.name + ' lost connection')
                    break
            except concurrent.futures.TimeoutError:
                user.status = Status.inactive
                print(user.name + ' lost connection by timeout')
                break
        user.writer.close()


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
