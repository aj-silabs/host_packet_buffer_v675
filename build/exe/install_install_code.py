import re
import os
import optparse

ADAPTERS = "commander adapter probe"
NO_ADAPTER_PATTERN = r"ERROR: Cannot connect to J-Link"
ONE_ADAPTER_PATTERN =r"J-Link Serial\ + :\ +(\w+)"
MUL_ADAPTER_PATTERN = r"Available USB serial numbers:\n((\w+\n)+)DONE"

def parseOptions():
    parser = optparse.OptionParser(usage ="""\
    install_and_verify  [device type] [adapter type] 
    """ )
    
    parser.add_option("-d", "--device", dest="device", 
                                help=("Specify device type"))
                                
    parser.add_option("-s", "--jlink", dest="adapter", 
                                help=("Specify Jlink serial number"))
                                
    parser.add_option("-r", "--r",action="store_true", dest="reverse", 
                                help=("reverse sequence of UINT16 of INSTALL CODE"))
                                        
    opts, args = parser.parse_args()

    return opts,args
        
    if opts.device:
        print(opts.device)
    if opts.adapter:
        print(opts.adapter)
    return opts, args

def get_adapter():
    response = os.popen(ADAPTERS,'r').read()
    result = re.search(NO_ADAPTER_PATTERN,response)
    
    assert False if result else True,"No adapter attached"
    #pattern = r"Available USB serial numbers:\n((\w+\n)+)DONE"
    #result = re.search(r"Available USB serial numbers:\n((\w+\n)+)DONE",response)
    result = re.search(MUL_ADAPTER_PATTERN,response)
    if result is not None:
        result = result.group(1)
        assert False if result else True,"Multiple adapters,pls specify adapter"
    else:
        result = re.search(r"J-Link Serial\ + :\ +(\w+)",response)
        return result.group(0).split(":")[1].strip() 

def get_mac_addr(device_type,adapter):
    cmd = os.popen("commander tokendump --tokengroup znet --device {} -s {}".format(device_type,adapter))
    response = cmd.read()

    device_info = re.search(r"ERROR: The given part number",response)

    adapter_info = re.search(r"ERROR: Unable to connect with device with given serial number",response)

    assert False if device_info is not None else True,"MISMATCH DEVICE TYPE"

    assert False if adapter_info is not None else True, "MISMATCH adapter"
    
    result = re.findall("MFG_EMBER_EUI_64\ +:\ \w+",response)
    
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
    mac_address = reverse_hex_string(eui)
    return mac_address

def remove_duplicates(pairs):
    def remove_duplicates_iter(pairs_rest,prev):
        if pairs_rest == []:
            return prev
        else:
            eui = pairs_rest[0].split(" ")[0].strip()
    
            if "\n".join(list(map(lambda pair:pair.split(" ")[0],prev))).find(eui) != -1:
                return remove_duplicates_iter(pairs_rest[1:],prev)
            else:
                prev.append(pairs_rest[0])
                return remove_duplicates_iter(pairs_rest[1:],prev)
    return remove_duplicates_iter(pairs,[])

def get_install_code_from_file(eui,reverse=True):
    pattern = eui.lower() + "\ *\w+\n"

    try:
        with open("install_code.csv",'r') as handler:
            lines = handler.readlines()
        
        lines = remove_duplicates(lines)

        with open("install_code.csv",'w') as handler:
            handler.write("\n".join(lines))
    
    
        with open("install_code.csv","r") as handler:
            for text in handler.readlines():
                result = re.findall(pattern,text)
                
                if result == []:
                    install_code = None
                    print("No matched InstallCode in this line")
                else:
                    install_code = result[0].split(" ")[1]
                    break
    except:
        assert False, "FILE install_code.csv doesn't exist or Open Error"
    
    
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
    assert False if install_code is None else True, "INSTALL CODE NOT FOUND" 
    if reverse:
        install_code = reverse_install_code(install_code)
    return install_code

def flash_install_code(eui,code,device,adapter):
    text = os.popen("commander tokendump --tokengroup znet --token MFG_INSTALLATION_CODE --device {} -s {}".format(device,adapter),'r').read().split("\n")
#    text = os.popen("commander tokendump --tokengroup znet --token MFG_INSTALLATION_CODE --device "+ device).read().split("\n")

    content = ''
    
    for line in text:
        if ("DONE" in line) or ("WARNING" in line) or ('Reconfiguring' in line):
            continue
        else:
            content = content + line + "\n"
    
    with open("token.txt","w") as handler:
        handler.write(content)

    def replace_flag(matchObj):
        flag = matchObj.group(0).split(":")
        print("flag:",flag)
        flag[1] = "0x0006"
        return ":".join(flag)
    
    with open("token.txt","r") as handler:
        text = ""
        for line in handler.readlines():
            if ("DONE" in line) or ("WARNING" in line) or ('Reconfiguring' in line):
                continue
            else:
                print("Modify the install_code flags")
                result = re.sub(r"Install Code Flags\ +:\ *\w+",replace_flag,line)
                print(result)
                text = text + result
    
    with open("token.txt",'w') as handler:
        handler.write(text)

    def replace_code(matchObj):
            text = matchObj.group(0).split(":")
            print(text)
            text[1] = code.strip().upper()
            return ":".join(text) 
    
    with open("token.txt","r") as handler:
        text = ""
        for line in handler.readlines():
            if ("DONE" in line) or ("WARNING" in line) or ('Reconfiguring' in line):
                continue
            else:
                result = re.sub("Install Code\ +:\ *\w+",replace_code,line)
                print(result)
                text = text + result

    with open("token.txt","w") as handler:
        handler.write(text)

    result = os.popen("commander flash --tokengroup znet --tokenfile token.txt --device {} -s {}".format(device,adapter),'r').read()

    print(result)

def verify_install_code(eui,code,device,adapter):
#    response = os.popen("commander flash --tokengroup znet --tokenfile token.txt --device efr32mg22")
    
    
#    text = os.popen("commander tokendump --tokengroup znet --token MFG_INSTALLATION_CODE --device efr32mg22")
    text = os.popen("commander tokendump --tokengroup znet --token TOKEN_MFG_INSTALLATION_CODE --device {} -s {}".format(device,adapter))
    result=re.findall("Install\ Code\ +:\ +\w+\n",text.read())
    result[0].split(":")[1][0:-1].strip()
    
    
    print("Original install code:\n",code)
    print("Install code read from flash\n",result[0].split(":")[1][0:-1].strip())
    if code.upper().strip() in result[0].split(":")[1][0:-1].strip():
        print("Code Installed successfully\n")
    else:
        print("Code IS NOT INSTALLED\n")
    
if __name__ == "__main__":
    opts,args = parseOptions()

    if opts.adapter is None:
        adapter = get_adapter()
        opts.adapter = adapter

    assert opts.device,"Specify device type"

    opts.reverse = True
    eui = get_mac_addr(opts.device,opts.adapter)
    print("MAC ADDRESS:",eui)
    code = get_install_code_from_file(eui,opts.reverse)
    flash_install_code(eui,code,opts.device,opts.adapter)
    verify_install_code(eui,code,opts.device,opts.adapter)

