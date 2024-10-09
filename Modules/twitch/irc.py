import socket

class IRCUser:
    name : str
    user : str
    host : str

    def __init__(self, name : str = None, user : str = None, host : str = None) -> None:
        self.name = name
        self.user = user
        self.host = host

    def __str__(self) -> str:
        result = self.name
        if self.user is not None:
            result += "!" + self.user
        if self.host is not None:
            result += "@" + self.host
        return result
    
    def parse(user_str : str) -> "IRCUser":
        index = 0
        name = ""
        user = None
        host = None
        while index < len(user_str) and user_str[index] != "!" and user_str[index] != "@":
            name += user_str[index]
            index += 1
        if len(name) == 0:
            raise ValueError("Name cannot have zero length.")
        if index < len(user_str) and user_str[index] == "!":
            index += 1
            user = ""
            while index < len(user_str) and user_str[index] != "@":
                user += user_str[index]
                index += 1
            if len(user) == 0:
                raise ValueError("User cannot have zero length.")
        if index < len(user_str) and user_str[index] == "@":
            index += 1
            host = ""
            while index < len(user_str):
                host += user_str[index]
                index += 1
            if len(name) == 0:
                raise ValueError("Host cannot have zero length.")
        return IRCUser(name, user, host)


class IRCMessage:
    command : str
    params : list[str]
    user : IRCUser
    tags : dict[str, str]

    def __init__(self, command : str, params : list[str],
                 user : IRCUser = None, tags : dict[str, str] = None) -> None:
        self.command = command
        self.params = params
        self.user = user
        if tags is None:
            self.tags = dict()
        else:
            self.tags = tags

    def encode_tag_value(self, value : str) -> str:
        result = ""
        for ch in value:
            if ch == ";":
                result += "\\:"
            elif ch == " ":
                result += "\\s"
            elif ch == "\r":
                result += "\\r"
            elif ch == "\n":
                result += "\\n"
            else:
                result += ch
        return result

    def __str__(self) -> str:
        result = ""
        if len(self.tags) > 0:
            result += "@"
            tag_index = 0
            for key, value in self.tags.items():
                result += key
                if value is not None:
                    result += "=" + self.encode_tag_value(value)
                if tag_index < len(self.tags) - 1:
                    result += ";"
                tag_index += 1
            result += " "
        if self.user is not None:
            result += ":" + str(self.user) + " "
        result += self.command
        for i in range(len(self.params)):
            result += " "
            if i == len(self.params) - 1 and\
                (" " in self.params[i] or self.params[i][0] == ":" or len(self.params[i]) == 0):
                result += ":"
            result += self.params[i]
        return result

    def parse(message : str) -> "IRCMessage":
        index = 0
        tags = dict()
        if message[index] == "@":
            index += 1
            while message[index] != " ":
                key = ""
                value = None
                while message[index] != "=" and message[index] != ";" and message[index] != " ":
                    key += message[index]
                    index += 1
                if message[index] == "=":
                    index += 1
                    value = ""
                    while message[index] != ";" and message[index] != " ":
                        value += message[index]
                        index += 1
                if message[index] == ";":
                    index += 1
                tags[key] = value
            while message[index] == " ":
                index += 1

        user = None
        if message[index] == ":":
            index += 1
            user_str = ""
            while message[index] != " ":
                user_str += message[index]
                index += 1
            user = IRCUser.parse(user_str)
            while message[index] == " ":
                index += 1
        
        command = ""
        while index < len(message) and message[index] != " ":
            command += message[index]
            index += 1

        params = []
        while index < len(message):
            while message[index] == " ":
                index += 1
            param = ""
            if message[index] == ":":
                index += 1
                while index < len(message):
                    param += message[index]
                    index += 1
            else:
                while index < len(message) and message[index] != " ":
                    param += message[index]
                    index += 1
            params.append(param)

        return IRCMessage(command, params, user=user, tags=tags)


class IRCClient:
    connection : socket.socket

    def __init__(self, host : str, port : int = 6667) -> None:
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host, port))

    def recv(self) -> IRCMessage:
        bytes = b''
        while True:
            byte = self.connection.recv(1)
            if byte == b'\r':
                self.connection.recv(1)
                break
            bytes += byte
        return IRCMessage.parse(bytes.decode())
    
    def send(self, message : IRCMessage) -> None:
        self.connection.sendall((str(message) + "\r\n").encode())
    
    def close(self) -> None:
        self.connection.close()