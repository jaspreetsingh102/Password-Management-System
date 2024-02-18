#system Password
import hashlib as Hash
def To_Md5(inp):
    return Hash.md5(inp.encode()).hexdigest()
inp="0000"
Hashed_System_Password=To_Md5(inp)
with open("System_Password.txt",'w') as file:
    file.write(Hashed_System_Password)