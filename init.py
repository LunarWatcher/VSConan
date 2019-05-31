from sys import platform

import os
import json
import re
import subprocess

# Bookmark: Method definitions

def parseJson():
    conan = ""
    vscode = ""
    # This is a two-part method. First load the conan ycm flags. This gets us the include paths and names
    with open("build/conan_ycm_flags.json", "r") as f:
        # Read the content
        content = "".join(f.readlines())
        # And parse it. List comprehension removes the -i part and gives a plain path. Not sure whether the system part is optional
        conan = [re.sub("(?i)-I(?:system)?", "", x) for x in json.loads(content)["includes"]]
    if(!hasVsCode):
        return conan
    # Next, the config is needed. In order to keep the includes linked in the file as well, they need to be added.
    # While it can be done manually, this script also does it. 
    with open(".vscode/c_cpp_properties.json", "r") as f:
        vscode = "".join(f.readlines())
        
    return (conan, vscode)

def handleIncludeInConfigFile(vsCodeConfig, include):
    # Iterate through the config. There can be several configurations per project, hence the iterating
    for configuration in vsCodeConfig["configurations"]:
        # Find the includePath definition
        vsIncludes = configuration["includePath"];
        # Flag because loop labels aren't supported
        match = False;
        for vsInclude in vsIncludes:
            # Attempt to find a path
            if ("vsInclude/" + include in vsInclude):
                match = True;
                break;
            elif platform == "win32":
                # Windows is case-insensitive. 
                if ("vsInclude/" + include.lower() in vsInclude.lower()):
                    match = True;
                    break;
                
        if not match:
            vsIncludes.append("${workspaceFolder}/vsInclude/" + include)
        
hasVsCode = True
# Bookmark: Script
if not os.path.exists(".vscode"):
    print("### WARNING! ###")
    print("Failed to find .vscode. No links will be made. Please create .vscode/c_cpp_properties.json to automatically link")
    print("################")
    hasVsCode = False

# Grab the includes
print("Grabbing dependencies and current configuration...")
if(hasVsCode):
    (includes, rawVsCodeConfig) = parseJson()
else:
    includes = parseJson()

if(includes is None or len(includes) == 0):
    raise Exception("Failed to read data, or data is empty. Make sure build/conan_ycm_flags.json exists and has content")
if(hasVsCode and (rawVsCodeConfig is None or len(rawVsCodeConfig) == 0)):
    raise Exception("VS Code config file is empty. While this script can handle some issues for you, " +
        " You still have to have a minimal file. VS Code can also auto-generate the file.")

if(hasVsCode):
    vsCodeConfig = json.loads(rawVsCodeConfig)

# Create the directory
if not os.path.exists("vsInclude"):
    os.mkdir("vsInclude")

for include in includes:
    # Once we're in the conan directory, the structure is global: 
    # <path>/.conan/data/packageName/packageVersion/authorName/releaseMode (i.e. stable, no parenthesis or space)/package/hash/
    # where <path> leads to the conan folder. authorName is the part right after the @ in the conanfile, and before the first slash.
    # In:
    # cpr/1.3.0@DEGoodmanWilson/stable
    # That would make the authorName DEGoodmanWilson. 
    # This doesn't matter for the current use case. What the regex finds is the package name, which is right after the data. 
    match = re.search(r"data[\\/]+(.*?)[\\/]+", include)
    # No match? Fall back to the secondary format
    if (match is None):
        match = re.search(r".conan[\\/](?!data).*?[\\/]\d+[\\/](.*?)[\\/]", include)
        # If the secondary format fails, the case isn't handled. Throw an exception.
        if(match is None):
            raise Exception("Failed to read name from \"" + include + "\". If this is a mistake, please open an issue in LunarWatcher/VSConan on GitHub")
    # Grab the group
    name = match.group(1)
    if(name is None or name.replace(" ", "") == ""):
        raise Exception("Name is empty for \"" + include + "\"")
    print("Found dependency: " + name)
    if hasVsCode:
        handleIncludeInConfigFile(vsCodeConfig, name)
    if os.path.exists("vsInclude/" + name):
        currentLink = os.readlink("vsInclude/" + name);
        print(currentLink)
        print(include)
        if (currentLink != include):
            print("Dependency \"" + name + "\" updated. Re-linking...");
            os.remove("vsInclude/" + name)
        else:
            print("Already linked. Skipping linking...")
            continue
    elif os.path.islink("vsInclude/" + name):
        print("ERROR: Symbolic link exists, but the directory doesn't. Removing link...")
        os.remove("vsInclude/" + name)
    if platform == "win32":
        # Windows and symlinks from Python don't work out. https://github.com/fishtown-analytics/dbt/issues/766#issuecomment-388213984
        # One hack to get around this is os.system. 
        result = subprocess.check_output("mklink /D \"vsInclude/" + name + "\" \"" + include + "\"", shell=True)
        print(result)
    else:
        # Any other OS is (in theory) fine
        os.symlink(include, "vsInclude/" + name)
    print("Dependency linked.\n")
    
print("All config ready.")
# Dump the updates
if hasVsCode:
    vsCodeConfigStr = json.dumps(vsCodeConfig, indent=4)
    if (vsCodeConfigStr == rawVsCodeConfig):
        # If no changes are made, save the disk and time. No need to write it. This is especially important for bigger files. 
        print("No updates made to the VS config: All items present.")
    else:
        if (len(vsCodeConfigStr) == 0):
            raise Exception("ABORT EMPTY WRITE!")
        else:
            print("Saving config...")
            # Otherwise, open and write the changes.
            with open(".vscode/c_cpp_properties.json", "w") as f:
                f.write(vsCodeConfigStr)
            print("Successfully saved the update configuration.")
