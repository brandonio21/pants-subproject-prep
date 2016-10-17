Pants Subproject Prep
=====================
A tool for [pantsbuild](https://github.com/pantsbuild/pants) which replaces
subproject dependency targets with ones compatible for their parent project.

Motivation
----------
Pantsbuild is a great system. However, it's design assumes that the user is 
working with a single monolithic repository for a single project. If a user
has two projects and wants one project to depend on the other, its pants
build structure must be changed in order to be compatible with the parent's 
build structure. 

This tool automates that process for my use case, which is by only changing
targets within the `dependencies` field of subprojects' `BUILD` files.


Consider the following project structure:
```
path
├── pants
├── pants.ini
├── projectA
│   └── src
│       └── python
|           └── main
│               ├── BUILD
│               └── main.py
└── projectB
    ├── pants
    ├── pants.ini
    └── src
        └── python
            ├── libA
            |   ├── BUILD
            |   └── lib.py
            └── libB
                ├── BUILD
                └── lib.py
```

Since projectB has come from elsewhere, its `BUILD` files are already
configured to depend on things relative to its build root. Thus, if 
projectA's `BUILD` files attempt to depend on projectB's `BUILD` files,
`pants` will raise an Exception, saying that it cannot find projectB's dependency
targets. This is because they are relative to projectB's build root and we are
building using projectA's build root.

A more permanent solution would involve allowing some sort of 
`additional_build_roots` option in `pants.ini`. However, that is not currently 
available. This script is my own personal workaround.

Downsides
---------
Unfortunately, since I am most interested in getting the subproject working for
building the parent project, this tool breaks the subprojects's ability to be built
independently of the parent project.

How does it work?
-----------------
This tool looks at all subdirectories of the parent project and tries to discover
possible pants subprojects (those with an executable `pants` file or a `pants.ini`).
These subproject folders are then scanned for BUILD files. Any BUILD files, then,
are permanently edited.

Currently, the script finds targets in the `dependencies` field of all BUILD rules,
checks whether it is relative to the subproject's build root, and if so, alters the
dependency to be relative to the parent project's build root instead.

Unfortunately, this may be a little fickle, as the internal logic is simply using
regex matching. In a future version (if I have time), I'd like to instead use
Python's powerful AST-modification features to edit the BUILD file.

Usage
-----
Run the script:

```
cd <pants-project-build-root>
git clone https://github.com/brandonio21/pants-subproject-prep
python pants-subproject-prep/subproject_prep.py
```

This will then do all of the work described above and leave two patch files in 
its wake, one describing the work performed and the other describing how to undo
the work performed (just in case something went horribly wrong).
