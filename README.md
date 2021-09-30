## lark-action
Adding semantic actions to Lark parser frontend.

Features:

0. semantic action support
1. inline python code
2. %mkrepl
3. Use `#` for comments instead of `//`.

(**CONFESS: I develop this because the existing tools are crazily shitty.**)

## Usage

```
%mkrepl # generate a repl for you; not necessary

# inline python code into the generated parser
%%
def my_func():
    print("call myfunc")
%%


        
start : ESCAPED_STRING -> { $1 } # $1 accesses the 1-st component
      | "%" start      -> my_func()

%import common.WS
%import common.ESCAPED_STRING
%ignore WS
```

execute command `python -m lark_action <grammar.lark> [-- package=""] [--module="mylang"]`, with default arguments you get 3 generated files: `mylang.lark` and `mylang_raw.py` and `mylang.py`.

You can directly access the generated parser via `from mylang import parser`.

If `%mkrepl` is specified, you get a simple repl to check your parser:
```
python mylang.py
input 'q' and exit.
> % "asd"
call myfunc
None
```
