import os, sys, gzip
from struct import unpack, pack

DEBUG = False

class BadFileException(Exception):
    def __init__(self):
        self.value = "Bad File! It must begin with TAG_Compound (10)"
    def __str__(self):
        return repr(self.value)

class Tag:
    tag_types = ["TagEnd", "TagByte", "TagShort", 
                  "TagInt", "TagLong", "TagFloat", 
                  "TagDouble", "TagByteArray", "TagString",
                  "TagList", "TagCompound"]
    
    def __init__(self, parent, named=True):
        self.named = named
        self.parent = parent
        self.tag_name = ""
        self.name = ""
        self.payload = 0x0
        
    def __str__(self):
        level = self.getLevel()
        output_string = "{0}{1}{2}: {3}\n".format("    "*level, self.tag_name, "(\"{0}\")".format(self.name) if self.named else "", self.payload)
        return output_string

    def parse(self, file):
        pass
    
    def toBytes(self, with_type_byte=True):
        bytes = []
        if with_type_byte:
            bytes.append(pack(">c", chr(self.tag_types.index(self.__class__.__name__))))
        if self.named:
            length = len(self.name)
            bytes.append(pack(">H", length))
            bytes.append(self.name.encode("utf-8"))
        return bytes

    def readString(self, file):
        if self.named:
            length, = unpack(">H", file.read(2))
            return file.read(length).decode("utf-8")
        else:
            return ""
    
    def readTag(self, tag_number, named=True):
        class_name = self.tag_types[tag_number]
        new_class = globals()[class_name](self, named)
        return new_class
    
    def getLevel(self):
        parent = self.parent
        level = 0
        while parent:
            parent = parent.parent
            level += 1
        return level

    def getName(self):
        if self.named:
            return self.name
        else:
            return None

    def getMembers(self):
        return []

    def debugPrint(self):
        if DEBUG:
            print(str(self))

class TagByte(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Byte"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload = ord(file.read(1))
        self.debugPrint()
    
    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">c", chr(self.payload)))
        return bytes
        
class TagShort(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Short"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload, = unpack(">h", file.read(2))
        self.debugPrint()
    
    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">h", self.payload))
        return bytes

class TagInt(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Int"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload, = unpack(">i", file.read(4))
        self.debugPrint()

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">i", self.payload))
        return bytes

class TagLong(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Long"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload, = unpack(">q", file.read(8))
        self.debugPrint()

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">q", self.payload))
        return bytes

class TagFloat(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Float"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload, = unpack(">f", file.read(4))
        self.debugPrint()

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">f", self.payload))
        return bytes

class TagDouble(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_Double"

    def parse(self, file):
        self.name = self.readString(file)
        self.payload, = unpack(">d", file.read(8))
        self.debugPrint()

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">d", self.payload))
        return bytes

class TagByteArray(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_ByteArray"
        self.payload = bytearray()

    def parse(self, file):
        self.name = self.readString(file)
        self.payload = self.readByteArray(file)
        self.debugPrint()
    
    def readByteArray(self, file):
        length, = unpack(">i", file.read(4))
        return file.read(length)

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">i", len(self.payload)))
        bytes.append(self.payload)
        return bytes

class TagString(Tag):
    def __init__(self,  parent, named=True):
        self.parent = parent
        self.named = named
        self.tag_name = "TAG_String"
        self.name = ""
        self.payload = ""

    def parse(self, file):
        self.name = self.readString(file)
        self.payload = self.readString(file)
        self.debugPrint()

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        payload = self.payload.encode("utf-8")
        bytes.append(pack(">H", len(payload)))
        bytes.append(payload)
        return bytes

class TagList(Tag):
    def __init__(self,  parent, named=True):
        super().__init__(parent, named)
        self.tag_name = "TAG_List"
        self.payload_type_number = 0
        self.number = 0
        self.members = []
    
    def __str__(self):
        level = self.getLevel()
        output_string = "{0}{1}{2}: {3} elements of type {4}\n\n".format("    "*level, self.tag_name, "(\"{0}\")".format(self.name) if self.named else "", self.number, self.members[0].tag_name)
        for member in self.members:
            output_string += "{0}".format(member)
        output_string +="\n"
        return output_string
    
    def parse(self, file):
        self.name = self.readString(file)
        self.payload_type_number = ord(file.read(1))
        self.number, = unpack(">i", file.read(4))
        self.members = self.readMembers(file, self.payload_type_number, self.number)
        self.debugPrint()
    
    def readMembers(self, file, payload_type_number, number):
        members = []
        for i in range(0, number):
            new_class = self.readTag(payload_type_number, False)
            new_class.parse(file)
            members.append(new_class)
        return members
    
    def getMembers(self):
        return self.members

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        bytes.append(pack(">c", chr(self.payload_type_number)))
        bytes.append(pack(">i", self.number))
        for member in self.members:
            bytes.extend(member.toBytes(False))
        return bytes

class TagCompound(Tag):
    def __init__(self,  parent, named=True):
        self.parent = parent
        self.named = named
        self.tag_name = "TAG_Compound"
        self.name = ""
        self.members = []
    
    def add(self, object):
        self.members.extend(object)
    
    def remove(self, object):
        self.members.remove(object)

    def __str__(self):
        level = self.getLevel()
        output_string = "{0}{1}{2}: {3} entries \n{0}{{\n".format("    "*level, self.tag_name, "(\"{0}\")".format(self.name) if self.named else "", len(self.members))
        for member in self.members:
            output_string += "{0}".format(member)
        output_string += "{0}}}\n".format("    "*level)
        return output_string
        
    def parse(self, file):
        self.name = self.readString(file)
        self.members = self.readMembers(file)
        self.debugPrint()
     
    def readMembers(self, file):
        members = []
        tag_number = ord(file.read(1))
        while tag_number != 0:
            new_class = self.readTag(tag_number)
            new_class.parse(file)
            members.append(new_class)
            tag_number = ord(file.read(1))
        return members
    
    def getMembers(self):
        return self.members

    def toBytes(self, with_type_byte=True):
        bytes = super().toBytes(with_type_byte)
        for member in self.members:
            bytes.extend(member.toBytes())
        bytes.append(pack(">c", chr(0)))
        return bytes

def read(file_name):
    with gzip.open(file_name, "rb") as file:
        byte = file.read(1)
        tag = None
        if(ord(byte) == 10):
            tag = TagCompound(None)
            tag.parse(file)
        else:
            raise BadFileError()
    return tag

def write(tag, file_name):
    with gzip.open(file_name, "wb") as out:
        for byte in tag.toBytes():
            out.write(byte)

if __name__ == "__main__":
    args = sys.argv
    if(len(args) not in [2, 3]):
        exit("Usage: {0} <input file> [output file]".format(args[0]))
    if(not(os.path.exists(args[1]))):
        exit("File {0} doesn't exist!".format(args[1]))
    tag = read(args[1])
    if len(args) == 3:
        out = open(args[2], "w")
        out.write(str(tag))
        out.close()
    else:
        print(tag)
    