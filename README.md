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
