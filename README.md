# VSConan

Because linking Conan includes with VS Code configuration is hard.

# How do I use it?

Usage is extremely simple. Grab the init.py script and put it in the project root. It needs to be executed from there. 

You'll also need the `ycm` generator. This generates the necessary JSON file. For sanity reasons, the script assumes the build folder is `build/`. If it isn't, you'll need to make adjustments to the script. If you build in the active tree though, you should re-consider your project structure. 

This has two uses:

1. Add the includes to c_cpp_configurations
2. Creating the system-specific symlinks. 

Both of which run independently of each other. 

Note that `.vscode/c_cpp_configurations` **need to exist** for this script to work. Create one or generate one using VS Code's template (`C/C++: Edit Configurations` from the command palette is one way to generate it)

## Integration use

It's not always desired to copy-paste the script. It also makes updates harder. The init script can easily be implemented into any build script-based system, or a standard script. 

Either way, you need a submodule:

```
git submodule add https://github.com/LunarWatcher/VSConan.git
```

### Python 

Place the import statement where you want it. This should go **after** any of your config

```python
import VSConan.init
```

Alternatively:

```python
import os
os.system("python VSConan/init.py")
```



### Anything that can interface with the command line

Essentially, this approach uses `os.system` for your favorite language. Bash, batch, and those types of languages are pretty straight-forward with:

```
python VSConan/init.py
```

The exact syntax varies, but something along the lines of that. 

Programming languages likely have their own classes that can execute that command. This also means you can add it to your build system, assuming you have one that supports scripting. 



# How does it work?

As mentioned in the last part, it takes advantage of the `ycm` file. On my Windows 10 computer, the `ycm` generator generates something like this:

```json
{
  "includes": [
    "-isystemC:\\Users\\...\\.conan\\data\\jsonformoderncpp\\3.6.1\\vthiery\\stable\\package\\5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9\\include",
    ... more here
  ],
  "defines": [
    ...
  ],
  "flags": []
}
```

This is where this script comes in. It reads the file, and finds the name of the dependency. In the above example, it extracts `jsonformoderncpp`. If there are more, it naturally extracts all of those as well. In addition, it grabs the paths without the `-i` part. 

After this, it leverages symlinks. A `vsInclude` folder is created, in which there are folders with the names of the library (i.e. `jsonformoderncpp`) that point to the conan include path for the project. This also makes it portable: the `vsInclude` folder is excluded from Git, and through that enables user-specific config while keeping the same static paths. 

On Windows, because of an OSError with `os.symlink`, it uses `os.system` with `mklink` instead. There shouldn't be a problem with other operating systems.

After the script is run, you'll have a project structure similar to this:
```
<root>/
  |- .vscode/
  |- vsInclude/
    |- Dependency1 (symlink)
    |- Dependency2 (symlink)
    |- ...
  |- (the rest of the project)
```

Aside the symlinks, the script takes it one step further, and actually writes your config for you. It alters the configurations to make sure it matches all the conan dependencies found, an does so for all the configurations. The includes are appended with items in the format of:

```json
"${workspaceFolder}/vsInclude/DependencyName"
```

If you don't trust the script to do this part correctly, either back up your old configuration (highly advised anyway - there could always be a bug somewhere), or you can remove the part and manually add the includes. 

Which means once you've imported a project containing this file, and you've created some config you're happy with, run the `init.py` script to add the conan dependencies as well. 

# Why symlinks?

Mainly because it integrates with the workspace, and enables access to the includes as if they were a part of the project. You can still open them regardless of whether it's a symlink or not, but the browsing experience is different.

