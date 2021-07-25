from collections import defaultdict
import copy, sys, functools, fractions, traceback

def kaiseki(s, acc = [], sacc = ''):

    if s == '':
        # accに副作用があるとなぜかダメらしい
        if sacc != '':
            return acc + [sacc]
        else:
            return acc

    elif s[0] == '"':
        stmp = ''
        while 1:

            s = s[1:]

            if s == '':
                print('文字列エラー')
                return
            elif s[0] == '\\':
                stmp += '\\'
                s = s[1:]
            elif s[0] == '"':
                return kaiseki(s[1:], acc + ['"' + stmp + '"'])
            
            stmp += s[0]

    elif s[0] == "'":
        return kaiseki(s[1:], acc + ["'"], sacc)

    elif s[0] == '#' or s[0] == ';':
        while 1:
            if s[0] == '\n' or s == "":
                return kaiseki(s, acc)
            else:
                s = s[1:]

    elif s[0] == '(':
        stmp = ''
        cnt = 0

        while 1:
            s = s[1:]
            if s == '':
                print('括弧エラー')
                return
            elif s[0] == ')' and cnt == 0:
                return kaiseki(s[1:], acc + [kaiseki(stmp)])
            elif s[0] == '(':
                cnt += 1
            elif s[0] == ')':
                cnt -= 1

            stmp += s[0]

    elif s[0] == ')':
        print('括弧エラー')
        return

    elif s[0] == ' ' or s[0] == '\n':
        if sacc != '':
            return kaiseki(s[1:], acc + [sacc], '')
        else:
            return kaiseki(s[1:], acc, '')

    else:
        return kaiseki(s[1:], acc, sacc + s[0])

class GSetter:
    pass

class Sub(GSetter):
    def __init__(self, k, env):
        self.val = main(k[1], env)
        if ':' in k[0]:
            self.sub = slice(*[main(i if i != '' else 'None', env) for i in k[0].split(':')])
        else:
            self.sub = main(k[0], env)

    def get(self):
        if isinstance(self.val, GSetter):
            return self.val.get()[self.sub]
        else:
            return self.val[self.sub]

    def set(self, it):
        if isinstance(self.val, GSetter):
            self.val.get()[self.sub] = it
        else:
            self.val[self.sub] = it

class Method(GSetter):
    def __init__(self, k, env):
        self.a = main(k[1], env)
        self.k = k
        self.env = env
        for i in k[2:-1]:
            if type(i) == list:
                self.a = getattr(self.a, i[0])(*[main(j, env) for j in i[1:]])
            else:
                self.a = getattr(self.a, i)

    def get(self):
        if isinstance(self.a, GSetter):
            a = self.a.get()
        else:
            a = self.a
        if type(self.k[-1]) == list:
            return getattr(a, self.k[-1][0])(*[main(j, self.env) for j in self.k[-1][1:]])
        else:
            return getattr(a, self.k[-1])

    def set(self, it):
        if isinstance(self.a, GSetter):
            a = self.a.get()
        else:
            a = self.a

        if type(self.k[-1]) == list:
            b = getattr(a, self.k[-1][0])(*[main(j, self.env) for j in self.k[-1][1:]])
            b = it
            return it
        else:
            return setattr(a, self.k[-1], it)

class Py(GSetter):
    def __init__(self, k):
        self.a = k[1]

    def get(self):
        return globals()[self.a]

    def set(self, it):
        globals()[self.a] = it

# ここかなり苦労してる
def arg(parms, args, kwargs):
    d = {}

    # 括弧なしで全体リスト
    if type(parms) == str:
        d[parms] = args
        d.update(kwargs)
        return d
    
    # まずparmsのリストを作って 適用されるたびに消す
    rest = []

    for i in parms:
        if type(i) == list:
            rest.append(i[0])
        else:
            rest.append(i)
        
    for i in range(len(args)):
        # rest
        if parms[i] == '.':
            d[parms[i + 1]] = args[i:]
            d.update(kwargs)
            return d

        elif type(parms[i]) == list:
            d[parms[i][0]] = args[i]

        else:
            d[parms[i]] = args[i]
    d.update(kwargs)
    return d

class Env(dict):
    def __init__(self, parms=(), args=(), kwargs={}, outer=None):
        a = arg(parms, args, kwargs)
        self.update(a)
        self.outer = outer

    def find(self, var):
        if var in self:
            return self
        elif self.outer == None:
            return None
        else:
            return self.outer.find(var)

glv = Env()
nowenv = None


def main(k, env):
    global nowenv
    nowenv = env

    if len(k) == 0:
        return None

    elif "'" in k:
        i = k.index("'")
        del k[i]
        k[i] = ['quote', k[i]]
        return main(k, env)

    elif type(k) != list:
        a = env.find(k)
        if a == None:
            return eval(k)
        elif a:
            return a[k]

    elif k[0] == 'quote' and len(k) == 2:
        return k[1]

    elif k[0] == 'import':
        _from = k.index(':from') if ':from' in k else -1
        _import = k[1]
        _as = k.index(':as') if ':as' in k else -1
        s = ''

        if _from != -1:
            s = 'from %s ' % k[_from + 1]
        s += 'import ' + _import
        if _as != -1:
            s += ' as %s' % k[_as + 1]
        exec(s, globals())

    elif k[0] == 'if':
        for i in range(1, len(k), 2):
            if i == len(k) - 1:
                return main(k[i], env)
            elif main(k[i], env):
                return main(k[i + 1], env)

    elif k[0] == 'and':
        for i in k[1:]:
            a = main(i, env)
            if not a:
                return a
        return a

    elif k[0] == 'or':
        for i in k[1:]:
            a = main(i, env)
            if a:
                return a
        return a
                
    elif k[0] == 'let':

        val = main(k[2], env)
        if isinstance(val, GSetter):
            val = val.get()
        env[k[1]] = val
        return val

    elif k[0] == 'def':
        return main(['let', k[1], ['lambda', k[2], *k[3:]]], env)

    elif k[0] == 'lambda' or k[0] == 'fn':
        return lambda *args, **kwargs: \
                main(['do', *k[2:]], Env(k[1], args, kwargs, env))
    
    elif k[0] == 'begin' or k[0] == 'do':
        if len(k) == 1:
            return None
        for i in k[1:-1]:
            main(i, env)
        a = main(k[-1], env)
        if isinstance(a, GSetter):
            return a.get()
        else:
            return a

    # 添字
    elif type(k[0]) == str \
            and (k[0].isdigit() or type(k[0][0]) == '"' or ':' in k[0]):
        return Sub(k, env)

    elif k[0] == '->':
        return Method(k, env)

    elif k[0] == 'py':
        return Py(k)

    elif k[0] == 'set':
        a = main(k[1], env)
        b = main(k[2], env)
        if isinstance(b, GSetter):
            b = b.get()

        if isinstance(a, GSetter):
            a.set(b)
        else:
            env.find(k[1])[k[1]] = b
        return b

    elif k[0] == '+=':
        env.find(k[1])[k[1]] += main(k[2], env) 

    elif k[0] == '-=':
        a = main(['=', k[1], ['-', k[1], k[2]]], env)
        return a

    elif k[0] == '*=':
        a = main(['=', k[1], ['*', k[1], k[2]]], env)
        return a

    elif k[0] == '/=':
        a = main(['=', k[1], ['/', k[1], k[2]]], env)
        return a

    elif k[0] == '//=':
        a = main(['=', k[1], ['//', k[1], k[2]]], env)
        return a

    elif k[0] == '%=':
        a = main(['=', k[1], ['%', k[1], k[2]]], env)
        return a

    # リストだった場合
    else:
        acc = []
        key = {}
        keyacc = None
        for i in k:
            if i[0] == ':':
                keyacc = i[1:]
            else:
                a = main(i, env)
                if isinstance(a, GSetter):
                    a = a.get()
                if keyacc:
                    key[keyacc] = a
                    keyacc = None
                else:
                    acc.append(a)
        return acc[0](*acc[1:], **key)

def _eval(s):
    s = s.replace('(', ' ( ').replace(')', ' ) ')
    s = s.replace("'", " ' ")
    # m = [main(i, glv) for i in kaiseki(s)]
    m = main(['do'] + kaiseki(s), glv)
    return m

glv['+']        = lambda *args: functools.reduce(lambda x, y: x + y, args[1:], args[0])
glv['-']        = lambda *args: functools.reduce(lambda x, y: x - y, args[1:], args[0])
glv['*']        = lambda *args: functools.reduce(lambda x, y: x * y, args[1:], args[0])
glv['/']        = lambda *args: functools.reduce(lambda x, y: x / y, args[1:], args[0])
glv['//']       = lambda x, y: x // y
glv['%']        = lambda x, *args: x % args
glv['=']        = lambda *args: all(i == args[0] for i in args[1:])
glv['==']       = lambda *args: all(i == args[0] for i in args[1:])
glv['is']       = lambda *args: all(i is args[0] for i in args[1:])
glv['eval_']    = lambda arg: main(arg, nowenv)
glv['isa']      = isinstance
glv['Set']      = set
glv['identity'] = lambda x: x
glv['mklist']   = lambda *args: list(args)
glv['mktuple']  = lambda *args: args
glv['mkdict']   = lambda **kwargs: kwargs

glv['apply']    = lambda f, lst: f(*lst)

def repl():
    while 1:
        try:
            print('nolis> ', end = '')
            print(_eval(input()))
            print()
        except SystemExit:
            print('bye.')
            exit()
        except EOFError:
            print('bye.')
            exit()
        except:
            traceback.print_exc()
            print()

if __name__ == '__main__':
    #print(kaiseki("'(hello world)"))
    #exit()
    if len(sys.argv) == 1:
        repl()
    else:
        with open(sys.argv[1], encoding = 'utf-8') as f:
            _eval(f.read())
            #print(kaiseki(f.read()))
