import os
import re
import struct

text = os.popen("commander tokendump --tokengroup znet")

result = re.findall("MFG_EMBER_EUI_64\ +:\ \w+",text.read())

str = list(filter(lambda x: x!=None,result))[0].split(":")[-1]

eui = re.sub('\s+','',str)

def reverse_hex_string(str):
    def helper(s,prev):
        if len(s) == 0:
            return prev
        else:
            a = s[0]
            b = s[1]
            c = s[2]
            d = s[3]

            f =s[2]+s[3]+s[0]+s[1]+prev

            return helper(s[4:],f)

    return helper(str,"")

print(reverse_hex_string(eui))

mac_address = reverse_hex_string(eui)

pattern = mac_address + "\ +\w+\n"

global install_code
install_code = None

with open("install_code.csv","r") as handler:
    text = handler.readlines()
    result = re.findall(pattern,text[0])
    if result == []:
        print("No match")
    else:
        
        install_code = result[0].split(" ")[1]

print(install_code)


def reverse_install_code(str):
    def reverse_iter(s,prev):
        if len(s) < 4:
            return prev
        else:
            a = s[0]
            b = s[1]
            c = s[2]
            c = s[3]

            f = prev + s[2]+s[3]+s[0]+s[1] 
            return reverse_iter(s[4:],f)

    return reverse_iter(str,"")

install_code = reverse_install_code(install_code)


def repalce(matchObj):
    text = matchObj.group(0).split(":")
    text[1] = install_code

    return ":".john(text)

def replace(matchObj):
        text = matchObj.group(0).split(":")
        text[1] = install_code
        return ":".join(text)

with open("token.txt","r") as handler:
    text = ""
    for line in handler.readlines():
        result = re.sub("Install Code\ +:\ +\w+",replace,line)
        text = text + result

with open("token.txt","w") as handler:
    handler.write(text)





    
    


# %%
response = os.popen("commander flash --tokengroup znet --tokenfile token.txt")

print(response.read())


# %%


