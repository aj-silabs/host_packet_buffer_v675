
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

