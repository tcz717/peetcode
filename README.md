# peetcode

Peetcode is a scons construction system for leetcode. You can use peetcode to create a project for a problem automatically, compile your code, test the solution with the input file and the expected-output file, and submit your final code.

## How to install

Peetcode requires python3.6 or beyond version. Then,

```bash
git clone https://github.com/tcz717/peetcode.git
cd peetcode
pip install -r requirements.txt
```

If you have multiple version python, you may need to modify the scons's file to specify python version,

```bash
vim $(which scons)
# change python to python3 or python3.6
# exmaple
#! /usr/bin/env python3.6
```

## Usage

Peetcode put all files in the directory of itself. If you would like to construct in other paths, change to your working directory and use `scons -f PEETCODE_PATH/SConstruct` instead of `scons`.

### Create a New Project

Create a new project requires the problem ID and the programming language you would like to use. Then peetcode will create a new folder named with the problem ID, language, and the slug, e.g. `1-cpp-two-sum`.

```shell
scons update # download problems list
scons 1-create # create project folder for problem 1
```

The default language is C++. If you prefer other language (now only support C, C++, C# and Python)

```bash
scons 1-c-create # use C language
```

### Compile the Project

Super simple:

```bash
scons 1
# if the problem has mutiple language version
scons 1-c
```

### Test Your Solution

When a project is created, peetcode automatically extracts the sample data in the problem description page and save it in `ID-LANG-SLUG\test\sample.in`. You can add your test input file in this folder with the `.in` extension. The output of the test is checked when a `.exp` expected-output file is provided.

```bash
scons 1-test
# if the problem has mutiple language version
scons 1-c-test
```

### Debug Test Case

```bash
# run gdb for 1-cpp project and use sample.in as input
scons 1-cpp-sample-debug
```

### Login and Submit Your code

To submit your code, you need to log in leetcode first

```bash
scons login user=USERNAME pass=PASSWORD
```

Then peetcode saves the cookies in the `.cookies` file. So, you don't have to log in again next time.

The submit command is similar to the previous commands

```bash
# you must specify both id and language to submit
scons 1-c-test
```

The result will be shown soon. If the code is not accepted, peetcode will extract the test case which your code isn't passed and save as the input file and the expected-output file (see also [Test Your Solution](#test-your-solution)).

### Template

Peetcode supports using templates to generate the initial code file so that you don't have to copy and paste the same code every time.

The template files should be placed in `templates` folder and name with its language's extension, for example, `template.cpp`.

To indicate the zone where peetcode put the problem default code and upload, you can use a placeholder `$DEFAULTCODE` in your template.

A C++ template file could be

```cpp
#include <vector>
#include <iostream>
#include <sstream>
#include <algorithm>
using namespace std;

$DEFAULTCODE
```