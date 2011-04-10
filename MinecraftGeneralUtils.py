import ParseMinecraftAlpha

######################################################
# find: Returns the first child named "name".
#       If no child name matches "name", return None
######################################################
def find(tag, name):
    members = tag.getMembers()
    return_member = None
    for member in members:
        member_name = member.getName()
        if member_name is not None and member_name == name:
            return_list.append(member)
            break
    return return_member

######################################################
# findAll: Returns all descendants named "name".
#          If none are found, return an empty list
######################################################    
def findAll(tag, name):
    return_list = []
    members = tag.getMembers()
    for member in members:
        member_name = member.getName()
        if member_name is not None and member_name == name:
            return_list.append(member)
        return_list.extend(findAll(member, name))
    return return_list