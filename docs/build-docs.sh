#!/usr/env sh

# build the CLI docs - dump into cli.rst
for cmd in `./situp.py|head -n2|tail -n1|awk -F : '{print $2}'`;
   do echo $cmd;
done
# run sphinx, writing to tmp

# change git branch

# copy in built docs

# commit

# clean up
