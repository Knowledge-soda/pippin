# Pippin

## Usage

There are 3 modes of use: interpreted, compiled to C and compiled to ad_hoc bytecode.

To interpret the code use:
```
python3 pippin.py -i <filename>
```

To compile the code to C use:
```
python3 pippin.py -o <output> -c <filename>
```
and then compile with any modern C compiler.

To compile the code to ad_hoc bytecode use:
```
python3 pippin.py -o <output> <filename>
```
and then use compiled version of `V1/vm.c` to run it:
```
./V1/vm <filename>
```
