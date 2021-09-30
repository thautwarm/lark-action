# Generated from lark-action.
def __get_location(token):
    return (token.line, token.column)

def __get_value(token):
    return token.value


def my_func():
    print("call myfunc")


from mylang_raw import Transformer, Lark_StandAlone
class mylang_Transformer(Transformer):

    def start_0(self, __args):
        return  { __args[1-1] }
    def start_1(self, __args):
        return  my_func()


parser = Lark_StandAlone(transformer=mylang_Transformer())
if __name__ == '__main__':

        while True:
            print("input q and exit.")
            source = input("> ")
            if source.strip() == "q":
                break
            if not source.strip():
                continue
            print(parser.parse(source))
