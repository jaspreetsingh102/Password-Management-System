from cryptography.fernet import Fernet
import hashlib as Hash
import pyttsx3 as Speak
import maskpass
def talky(x):
    engine = Speak.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-70)
    def speak(x):
        engine.say(x)
        engine.runAndWait()
    speak(x)
To_Sha512 = lambda Login_Password : Hash.sha512(Login_Password.encode()).hexdigest()
To_Sha256 = lambda Login_Username : Hash.sha256(Login_Username.encode()).hexdigest()
To_Md5 = lambda x : Hash.md5(x.encode()).hexdigest()
To_Filename = lambda Hashed_Username : Hashed_Username+''+".txt"
To_Filekey = lambda Hashed_Username : Hashed_Username+''+".key"
def Check_Username(Hashed_Username,Existing_Username):
    if(Hashed_Username==Existing_Username):
        return True
    else:
        return False
def Check_Password(Hashed_Password,Existing_Password):
    if(Hashed_Password==Existing_Password):
        return True
    else:
        return False
def Check_Sitename(Sitename,Existing_Sitename):
    if(Sitename==Existing_Sitename):
        return True
    else:
        return False
def Check_Siteusername(Encrypted_Siteusername,Existing_Siteusername):
    if(Encrypted_Siteusername==Existing_Siteusername):
        return True
    else:
        return False
def Check_Sitepassword(Encrypted_Sitepassword,Existing_Sitepassword):
    if(Encrypted_Sitepassword==Existing_Sitepassword):
        return True
    else:
        return False
def Save_New(filename,Cipher):
    x="Save New Details Here"
    talky(x)
    print()
    print("----- Save New -----")
    print()
    x="Kindly Enter The Sitename In The Next Line"
    talky(x)
    Sitename=input("Enter Your Site Name : ")
    x="Kindly Enter The Siteusername In The Next Line"
    talky(x)
    Siteusername=input("Enter Your Username On Site : ").encode()
    x="Kindly Enter The Sitepassword In The Next Line"
    talky(x)
    Sitepassword=input("Enter Site Password : ").encode()
    with open(filename,'a') as file:
        file.write(Sitename+"|"+Cipher.encrypt(Siteusername).decode()+"~"+Cipher.encrypt(Sitepassword).decode()+"\n")
    print()
    x="Save Successful"
    print(x)
    talky(x)
    Passman_Represent()
    Passman_Choice(filename,Cipher)   
def Show_All(filename,Cipher):
    x="Showing All Details Here"
    talky(x)
    print()
    print("----- Show All -----")
    with open(filename,'r') as file:
        for line in file.readlines():
            Single_Line=line.rstrip()
            Sitename,Decode_Line=Single_Line.split("|")
            Siteusername,Sitepassword=Decode_Line.split("~")
            print()
            print("Sitename is : ",Sitename)
            print("Site Username is : ",Cipher.decrypt(Siteusername.encode()).decode()) 
            print("Site Password is : ",Cipher.decrypt(Sitepassword.encode()).decode())
    Passman_Represent()
    Passman_Choice(filename,Cipher)
def Update_Siteusername(filename,Cipher,To_Replace_Siteusername):
    print()
    x="Kindly Enter New Siteusername In The Next Line"
    talky(x)
    New_Siteusername=input("Enter New Username : ")
    x="Kindly Confirm New Siteusername In The Next Line"
    talky(x)
    Confirm_Siteusername=input("Confirm New Siteusername : ")
    if(New_Siteusername==Confirm_Siteusername):
        To_Siteusername=Confirm_Siteusername.encode()
        Replace_To_Siteusername=Cipher.encrypt(To_Siteusername).decode()
        with open(filename,'r') as file:
            lines=file.read()
        lines=lines.replace(To_Replace_Siteusername,Replace_To_Siteusername)
        with open(filename,'w') as file:
            file.write(lines)
        print()
        x="Siteusername Updated Successfully"
        print(x)
        talky(x)
    elif(New_Siteusername!=Confirm_Siteusername):
        print()
        x="Siteusername Match Unsuccessful"
        print(x)
        talky(x)
        Update_Siteusername(filename,Cipher,To_Replace_Siteusername)
def Update_Sitepassword(filename,Cipher,To_Replace_Sitepassword):
    print()
    x="Kindly Enter New Sitepassword In The Next Line"
    talky(x)
    New_Sitepassword=input("Enter New Sitepassword : ")
    x="Kindly Confirm New Sitepassword In The Next Line"
    talky(x)
    Confirm_Sitepassword=input("Confirm New Sitepassword : ")
    if(New_Sitepassword==Confirm_Sitepassword):
        To_Sitepassword=Confirm_Sitepassword.encode()
        Replace_To_Sitepassword=Cipher.encrypt(To_Sitepassword).decode()
        with open(filename,'r') as file:
            lines=file.read()
        lines=lines.replace(To_Replace_Sitepassword,Replace_To_Sitepassword)
        with open(filename,'w') as file:
            file.write(lines)
        print()
        x="Sitepassword Updated Successfully"
        print(x)
        talky(x)
    elif(New_Sitepassword!=Confirm_Sitepassword):
        print()
        x="Sitepassword Match Unsuccessful"
        print(x)
        talky(x)
        Update_Siteusername(filename,Cipher,To_Replace_Sitepassword)
def Update_Details(filename,Cipher):
    print()
    print("----- Update Details -----")
    print()
    x="Kindly Enter The Sitename In The Next Line"
    talky(x)
    Sitename=input("Enter Sitename To Update Details : ")
    x="Kindly Enter The Siteusername In The Next Line"
    talky(x)
    Siteusername=input("Enter Siteusername To Update Details : ")
    x="Kindly Enter The Sitepassword In The Next Line"
    talky(x)
    Sitepassword=input("Enter Sitepassword To Update Details : ")
    file=open(filename,'r')
    for line in file.readlines():
        Single_Line=line.rstrip()
        Existing_Sitename,Decode_Line=Single_Line.split("|")
        Existing_Siteusername,Existing_Sitepassword=Decode_Line.split("~")
        To_Replace_Siteusername=Existing_Siteusername
        To_Replace_Sitepassword=Existing_Sitepassword
        decrypted_siteusername=Cipher.decrypt(Existing_Siteusername.encode()).decode()
        decrypted_sitepassword=Cipher.decrypt(Existing_Sitepassword.encode()).decode()
        Verified_Sitename=Check_Sitename(Sitename,Existing_Sitename)
        if(Verified_Sitename==True):
            Verified_Siteusername=Check_Siteusername(Siteusername,decrypted_siteusername)
            Verified_Sitepassword=Check_Sitepassword(Sitepassword,decrypted_sitepassword)
            if(Verified_Siteusername==True and Verified_Sitepassword==True):
                Update_Siteusername(filename,Cipher,To_Replace_Siteusername)
                Update_Sitepassword(filename,Cipher,To_Replace_Sitepassword)
                Passman_Represent()
                Passman_Choice(filename,Cipher)
            elif(Verified_Siteusername==True and Verified_Sitepassword==False):
                print()
                x="Sitepassword Match Unsuccessful"
                print(x)
                talky(x)
                x="Returning To Passman Menu"
                talky(x)
                Passman_Represent()
                Passman_Choice(filename,Cipher)
            Verified_Siteusername=False
            if(Verified_Siteusername==False):
                print()
                x="Siteusername Match Unsuccessful"
                print(x)
                talky(x) 
                x="Returning To Passman Menu"
                talky(x)
                Passman_Represent()
                Passman_Choice(filename,Cipher)
    Verified_Sitename=False
    if(Verified_Sitename==False):
        print()
        x="Sitename Match Unsuccessful"
        print(x)
        talky(x) 
        x="Returning To Passman Menu"
        talky(x)
        Passman_Represent()
        Passman_Choice(filename,Cipher)
def Passman_Choice(filename,Cipher):
    x="Kindly Enter Your Choice In The Next Line"
    talky(x)
    print()
    inp=int(input("Enter Your Choice : "))
    if(inp==1):
        Save_New(filename,Cipher)
    elif(inp==2):
        Show_All(filename,Cipher)
    elif(inp==3):
        Update_Details(filename,Cipher)
    elif(inp==4):
        User_Menu()
    elif(inp==0):
        x="Exiting Passman , Thank you for using our services"
        print(x)
        talky(x)
        exit()
def Passman_Represent():
    print()
    print("---------- Passman Menu ----------")
    x="Here Is The Passman Menu"
    talky(x)
    print()
    x="Press 1 To Save New Login Details"
    print(x)
    talky(x)
    x="Press 2 To Show All Login Details"
    print(x)
    talky(x)
    x="Press 3 To Update Any Login Details"
    print(x)
    talky(x)
    x="Press 4 To Return To A User Menu"
    print(x)
    talky(x)
    x="Press 0 To Exit"
    print(x)
    talky(x)
def Load_User_Key(filekey):
    with open(filekey,'rb') as file:
        Key=file.read()
    return Key
def Passman_Menu(filename,filekey):
    User_Key=Load_User_Key(filekey)
    Cipher=Fernet(User_Key)
    Passman_Represent()
    Passman_Choice(filename,Cipher)
def Check_Username_Password(Hashed_Username,Existing_Username,Hashed_Password,Existing_Password,Count):
    Verified_Username=Check_Username(Hashed_Username,Existing_Username)
    Verified_Password=Check_Password(Hashed_Password,Existing_Password)
    if(Verified_Username==True and Verified_Password==True):
        filename=To_Filename(Hashed_Username)
        filekey=To_Filekey(Hashed_Username)
        x="Username and Password Verified Sucessfully"
        print(x)
        talky(x)
        Passman_Menu(filename,filekey)
        exit()
    elif(Verified_Username==True and Verified_Password==False):
        if(Count==0):
            Count=str(Count)
            x='You Have '+''+Count+''+' Try Left To Enter The Correct System Password'
            print(x)
            talky(x)
            x="Exiting Passman , Thank you for using our services"
            print(x)
            talky(x)
            Count=int(Count)
            exit()
        x="Password Match Unsucessful"
        print(x)
        talky(x)
        Count=str(Count)
        x='You Have '+''+Count+''+' Try Left To Enter The Correct Passman Account Password'
        print(x)
        talky(x)
        Count=int(Count)
        x="Kindly Enter Password In The Next Line"
        talky(x)
        Count=Count-1
        Login_Password=input("Enter Password : ")
        print()
        Hashed_Password=To_Sha512(Login_Password)
        Check_Username_Password(Hashed_Username,Existing_Username,Hashed_Password,Existing_Password,Count)      
def User_Login(Hashed_Username,Hashed_Password):
    print()
    print("----- Login To Passman Account -----")
    print()
    file=open("Users.txt",'r')
    Count=2
    for I in file.readlines():
        line=I.rstrip()
        Existing_Username,Existing_Password=line.split("|")
        Check_Username_Password(Hashed_Username,Existing_Username,Hashed_Password,Existing_Password,Count)   
    Already_Username=False
    if(Already_Username==False):
        x="Username Not Found , Creating A Passman Account"
        print(x)
        talky(x) 
        User_Create(Hashed_Username,Hashed_Password)
        exit()
def User_Update(Hashed_Username,Hashed_Password):
    print()
    print("----- Update A Passman Account -----")
    print()
    file=open("Users.txt",'r')
    for I in file.readlines():
        line=I.rstrip()
        Existing_Username,Existing_Password=line.split("|")
        Verified_Username=Check_Username(Hashed_Username,Existing_Username)
        Verified_Password=Check_Password(Hashed_Password,Existing_Password)
        if(Verified_Username==True and Verified_Password==True):
            To_Replace_Password=Existing_Password
            x="Kindly Enter The New Password In The Next Line"
            talky(x)
            New_Password=input("Enter New Password : ")
            Hashed_New_Password=To_Sha512(New_Password)
            x="Kindly Confirm The New Password In The Next Line"
            talky(x)
            Confirm_New_Password=input("Confirm New Password : ")
            Hashed_Confirm_Password=To_Sha512(Confirm_New_Password)
            if(Hashed_New_Password==Hashed_Confirm_Password):
                Replace_To_Password=Hashed_Confirm_Password
                with open("Users.txt",'r') as file:
                    lines=file.read()
                lines=lines.replace(To_Replace_Password,Replace_To_Password)
                with open("Users.txt",'w') as file:
                    file.write(lines)
                print()
                x="Password Updated Successfully"
                print(x)
                talky(x)
                x="Returning To User Menu"
                talky(x)
                User_Menu()         
            elif(Hashed_New_Password!=Hashed_Confirm_Password):
                print()
                x="Password Match Unsuccessful"
                print(x)
                talky(x)
                User_Update(Hashed_Username,Hashed_Password)
        elif(Verified_Username==True and Verified_Password==False):
            x="Password Match Unsuccessful"
            print(x)
            talky(x)
            x="Kindly Enter Password In The Next Line"
            talky(x)
            print()
            Login_Password=input("Enter Password : ")
            Hashed_Password=To_Sha512(Login_Password)
            User_Update(Hashed_Username,Hashed_Password)
    Verified_Username=False
    if(Verified_Username==False):
        x="Username Not Found"
        print(x)
        talky(x) 
        x="Returning To User Menu"
        talky(x)
        User_Menu()
def User_Create(Hashed_Username,Hashed_Password):
    def Create_New_User(Hashed_Username,Hashed_Password):
        file=open("Users.txt",'a')
        file.write(Hashed_Username+'|'+Hashed_Password+"\n")
        file.close()
    def Create_User_File(Hashed_Username):
        filename=To_Filename(Hashed_Username)
        file=open(filename,'a')
        file.close()
    def Create_User_Key(Hashed_Username):
        filekey=To_Filekey(Hashed_Username)
        Key=Fernet.generate_key()
        with open(filekey,"wb") as file:
            file.write(Key)
    file=open("Users.txt",'r')
    for I in file.readlines():
        line=I.rstrip()
        Existing_Username,Existing_Password=line.split("|")
        Already_Username=Check_Username(Hashed_Username,Existing_Username)
        if(Already_Username==True):
            print()
            x="Username Found , Logging into Passman Account"
            print(x)
            talky(x) 
            User_Login(Hashed_Username,Hashed_Password)
            exit()
    print()
    print("----- Create A Passman Account -----")
    print()
    x="Kindly Confim Password In The Next Line"
    talky(x)
    Confirm_Password=input("Confirm Password : ")
    Hashed_Confirm_Password=To_Sha512(Confirm_Password)
    if(Hashed_Confirm_Password==Hashed_Password):
        Create_New_User(Hashed_Username,Hashed_Password)
        Create_User_File(Hashed_Username)
        Create_User_Key(Hashed_Username)
        print()
        x="Passman Account Created Sucessfully"
        print(x)
        talky(x)
        x="Returning To User Menu"
        talky(x)
        User_Menu()
    else:
        print()
        x="Password Match Unsucessful , Returning To Confirm Password"
        print(x)
        talky(x)
        User_Create(Hashed_Username,Hashed_Password)
def User_Choice():
    x="Kindly Enter Your Choice In The Next Line"
    talky(x)
    print()
    inp=int(input("Enter Your Choice : "))
    if(inp in [1,2,3]):
        x="Kindly Enter Username In The Next Line"
        talky(x)
        print()
        Login_Username=input("Enter Username : ")
        Hashed_Username=To_Sha256(Login_Username)
        x="Kindly Enter Password In The Next Line"
        talky(x)
        Login_Password=input("Enter Password : ")
        Hashed_Password=To_Sha512(Login_Password)
        if(inp==1):
            User_Create(Hashed_Username,Hashed_Password)
        elif(inp==2):
            User_Login(Hashed_Username,Hashed_Password)
        elif(inp==3):
            User_Update(Hashed_Username,Hashed_Password)
    elif(inp==4):
        x="Returning To System Menu"
        talky(x)
        System_Menu()
    elif(inp==0):
        x="Exiting Passman , Thank you for using our services"
        print(x)
        talky(x)
        exit()
    else:
        x="Invalid Choice"
        print(x)
        talky(x)
        User_Choice()
def User_Menu():
    print()
    print("---------- User Menu ----------")
    x="Here Is The User Menu"
    talky(x)
    print()
    x="Press 1 To Create A Passman Account"
    print(x)
    talky(x)
    x="Press 2 To Login To Passman Account"
    print(x)
    talky(x)
    x="Press 3 To Update A Passman Account"
    print(x)
    talky(x)
    x="Press 4 To Return To System Menu"
    print(x)
    talky(x)
    x="Press 0 To Exit"
    print(x)
    talky(x)
    User_Choice()
def Reset_Password():
    print()
    print("----- Reset Password -----")
    print()
    x="Kindly Enter The New System Password In The Next Line"
    talky(x)
    New_System_Password=input("Enter New Password : ")
    Hashed_New_System_Password=To_Md5(New_System_Password)
    x="Kindly Confirm The New System Password In The Next Line"
    talky(x)
    Confirm_New_System_Password=input("Confirm New Password : ")
    Hashed_Confirm_New_System_Password=To_Md5(Confirm_New_System_Password)
    if(Hashed_New_System_Password==Hashed_Confirm_New_System_Password):
        f=open("System_Password.txt",'w')
        f.write(Hashed_New_System_Password)
        f.close()
        print()
        x="System Password Reset Succesful"
        print(x)
        talky(x)
        x="Returning To System Menu"
        talky(x)
        System_Menu()
    else:
        print()
        x="Password Match Unsuccessful , Returning To Reset Password"
        print(x)
        talky(x)
        Reset_Password()
def Check_System_Password(Hashed_System_Password,Existing_System_Password,inp):
    if(Hashed_System_Password==Existing_System_Password):
        x="System Password Verified Sucessfully"
        print(x)
        talky(x)
        print()
        if(inp==1):
            x="Entering User Menu"
            print(x)
            talky(x)
            User_Menu()   
        if(inp==2):
            x="Initializing System Password Reset"
            print(x)
            talky(x)
            Reset_Password()
def Enter_System_Password(inp):
    print("----- System Password -----")
    print()
    x="Entering The System Password"
    talky(x)
    f=open("System_Password.txt",'r')
    Eisting_System_Password=f.read()
    f.close()
    count=3
    while(count>0):   
        count=str(count)
        x='You Have '+''+count+''+' Try Left To Enter The Correct System Password'
        print(x)
        talky(x)
        x="Kindly Enter The Correct System Password In The Next Line"
        talky(x)
        System_Password=maskpass.askpass(prompt="Enter System Password : ",mask="*")
        print()
        Hashed_System_Password=To_Md5(System_Password)
        Check_System_Password(Hashed_System_Password,Eisting_System_Password,inp)
        count=int(count)
        count=count-1
        if(count==0):
            count=str(count)
            x='You Have '+''+count+''+' Try Left To Enter The Correct System Password'
            print(x)
            talky(x)
            x="Exiting Passman , Thank you for using our services"
            print(x)
            talky(x)
            print()
            count=int(count)
def Desc_Talky():
    x="Entering To Learn More About Talky"
    talky(x)
    print("----- More About Talky -----")
    print()
    x="Here is More About Talky"
    talky(x)
    x="Talky Is An Automated Voice Bot Assistant Which Uses Voice Over Narration To Relay Information To The User"
    print(x)
    talky(x)
    x="Talky Aims To Provide A Natural And More User Friendly Experience"
    print(x)
    talky(x)
    x="Talky Uses Python's Pyttsx3 Module"
    print(x)
    talky(x)
    x="Returning To System Menu"
    talky(x)
    System_Menu()
def Desc_Passman():
    x="Entering To Learn More About Passman"
    talky(x)
    print("----- More About Passman -----")
    print()
    x="Here is More About Passman"
    talky(x)
    x="Passman Is A Superhero Which Protects Your Sensitive Passwords From Unauthorized Access"
    print(x)
    talky(x)
    x="Passman Aims To Provide Functionality To The User By Storing Their Password In An Systematic And Organized Format"
    print(x)
    talky(x)
    x="Passman Uses Python's Cryptography, Hashlib and Maskpass Module"
    print(x)
    talky(x)
    x="Returning To System Menu"
    talky(x)
    System_Menu()
def System_Choice():
    x="Kindly Enter Your Choice In The Next Line"
    talky(x)
    print()
    inp=int(input("Enter Your Choice : "))
    print()
    if(inp==1 or inp==2):
        Enter_System_Password(inp)
    elif(inp==3):
        Desc_Talky()
    elif(inp==4):
        Desc_Passman()
    elif(inp==0):
        x="Exiting Passman , Thank you for using our services"
        print(x)
        talky(x)
        exit()
    else:
        x="Invalid Choice"
        print(x)
        talky(x)
        System_Menu()
def System_Menu():
    print()
    print("---------- System Menu ----------")
    x="Here Is The System Menu"
    talky(x)
    print()
    x="Press 1 To Enter System Password"
    print(x)
    talky(x)
    x="Press 2 To Reset System Password"
    print(x)
    talky(x)
    x="Press 3 To Describe Talky"
    print(x)
    talky(x)
    x="Press 4 To Describe Passman"
    print(x)
    talky(x)
    x="Press 0 To Exit"
    print(x)
    talky(x)
    System_Choice()
System_Menu()