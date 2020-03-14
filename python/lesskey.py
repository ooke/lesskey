#!/usr/bin/env python3

import hashlib, sys, getpass, re, time, os, base64, random
from subprocess import run, Popen, PIPE, DEVNULL

sys.setrecursionlimit(99999)
storefile = os.path.expanduser('~/.lesskey')

class UserIO(object):
    def __init__(self):
        pass

    def clear(self):
        os.system('clear');

    def output(self, data):
        print(data)

    def input(self, prompt, password = False):
        if password:
            return getpass.getpass(prompt)
        return input(prompt)

    def copy_mac(self, data, verbose = True, name = 'password'):
        try:
            with Popen(['pbcopy'], stdin = PIPE, stdout = DEVNULL, stderr = DEVNULL) as fd:
                fd.stdin.write(data.encode('utf-8'))
            if verbose:
                self.output("%s copied to Mac OS X pasteboard" % name)
        except:
            if verbose:
                self.output("failed to copy %s to Mac OS X pasteboard" % name)

    def copy_x11(self, data, verbose = True, name = 'password'):
        try:
            with Popen(['xclip'], stdin = PIPE, stdout = DEVNULL, stderr = DEVNULL) as fd:
                fd.stdin.write(data.encode('utf-8'))
            if verbose:
                self.output("%s copied to X11 clipboard" % name)
        except:
            if verbose:
                self.output("failed to copy %s to X11 clipboard" % name)

    def copy_tmux(self, data, verbose = True, name = 'password'):
        try:
            with Popen(['tmux', 'set-buffer', data], stdin = None, stderr = DEVNULL) as fd:
                pass
            if verbose:
                self.output("%s copied to tmux buffer" % name)
        except Exception as err:
            if verbose:
                self.output("failed to copy %s to tmux buffer" % name)

class Storage(object):
    def __init__(self, storefile):
        self._storefile = storefile

    def _readstored(self):
        stored = set()
        try:
            with open(self._storefile, 'rb') as fd:
                for line in fd:
                    line = line.decode('utf-8').strip()
                    if line == '': continue
                    stored.add(line)
        except: pass
        return stored

    def store(self, nseed, master):
        stored = self._readstored()
        stored.add(hashlib.sha1(nseed.encode('utf-8')).hexdigest())
        stored.add(hashlib.sha1(master.encode('utf-8')).hexdigest())
        stored.add(hashlib.sha1((nseed + master).encode('utf-8')).hexdigest())
        with open(self._storefile + ".tmp", 'wb') as fd:
            for cksum in stored:
                fd.write(("%s\n" % cksum).encode('utf-8'))
        os.rename(self._storefile + ".tmp", self._storefile)

    def delete(self, nseed, master):
        stored = self._readstored()
        try: stored.remove(hashlib.sha1(nseed.encode('utf-8')).hexdigest())
        except: pass
        try: stored.remove(hashlib.sha1(master.encode('utf-8')).hexdigest())
        except: pass
        try: stored.remove(hashlib.sha1((nseed + master).encode('utf-8')).hexdigest())
        except: pass
        with open(self._storefile + ".tmp", 'w') as fd:
            for cksum in stored:
                fd.write("%s\n" % cksum)
        os.rename(self._storefile + ".tmp", self._storefile)

    def __enter__(self):
        return self._readstored()
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class SKey(object):
    def __init__(self, seed, secret, n):
        self._h = self._get_otp_sha1(secret, seed, n)

    def _sha1(self, x):
        h = hashlib.sha1()
        for w in x:
            h.update(w)
        h = h.digest()
        r = [int.from_bytes(h[i:i+4], 'little') for i in range(0, 20, 4)]
        x, y = (r[0] ^ r[2] ^ r[4]), (r[1] ^ r[3])
        z = [int.to_bytes(x, 4, 'big'), int.to_bytes(y, 4, 'big')]
        return z

    def _get_otp_sha1(self, secret, seed, n):
        x = [(seed.lower() + secret).encode()]
        for _ in range(n+1):
            x = self._sha1(x)
        x = [int.from_bytes(x[0], 'little'), int.from_bytes(x[1], 'little')]
        return [int.to_bytes(x[0], 4, 'big'), int.to_bytes(x[1], 4, 'big')]

    def tob64(self):
        h = [int.from_bytes(x, 'big') for x in self._h]
        s = []
        for i in range(2):
            for j in range(4):
                t = (h[i] >> (8*j)) & 0xff
                s.append(int.to_bytes(t, 1, 'big'))
        s = b"".join(s)
        return base64.b64encode(s).decode('utf-8').replace('=', '').strip()

    def todec(self):
        h = [int.from_bytes(x, 'big') for x in self._h]
        parity = 0
        for i in range(2):
            for j in range(0, 32, 2):
                parity += (h[i] >> j) & 0x3
        s = []
        s.append((h[0] & 0xff) << 3 | (h[0] >> 13) & 0x7)
        s.append(((h[0] >> 8) & 0x1f) << 6 | (h[0] >> 18) & 0x3f)
        s.append(((h[0] >> 16) & 0x3) << 9 | ((h[0] >> 24) & 0xff) << 1 | (h[1] >> 7) & 0x1)
        s.append((h[1] & 0x7f) << 4 | (h[1] >> 12) & 0xf)
        s.append(((h[1] >> 8) & 0xf) << 7 | (h[1] >> 17) & 0x7f)
        s.append(((h[1] >> 16) & 0x1) << 10 | ((h[1] >> 24) & 0xff) << 2 | (parity & 0x03))
        return s

    def towords(self):
        return [WORDS[n] for n in self.todec()]

    def tohex(self):
        s = []
        for i in range(2):
            for j in range(4):
                s.append("%02x" % self._h[i][j])
        return ''.join(s)

class Seed(object):
    def __init__(self, seed, genstate = None):
        self._seed = seed
        self._genstate = genstate
        self._parse_seed()

    def _parse_seed(self):
        ma_seed = re.match(r'^\s*(\S+)(?:\s+([0-9]*)([rR]|[uU]|[uU][rR]|[uU][nNhHbB]|[nNhHbBdD]|[nN][dD]|[dD]))?(?:\s+([0-9]+)\s*(?:[-]?\s*(.*))?)?\s*$', self._seed)
        if ma_seed is None:
            ma_seed = re.match(r'^\s*(?:(\S+)\s+(\S+)(?:\s+([0-9]*)([rR]|[uU]|[uU][rR]|[uU][nNhHbB]|[nNhHbB]))?(?:\s+([0-9]+)\s*(?:[-]?\s*(.*))?)?)?\s*$', self._seed)
            if ma_seed is None:
                raise SyntaxError("seed can not be parsed: %s" % str(self._seed))
            prefix, name, maxchars, ntype, seq, desc = ma_seed.groups()
        else: prefix, name, maxchars, ntype, seq, desc = (None,) + ma_seed.groups()
        if ntype is None: ntype = 'R'
        if seq is None: seq = 99
        if maxchars == '' or maxchars is None: maxchars = 0
        sa_xxx = re.search(r'(X+)$', name)
        if sa_xxx:
            num = random.randint(1, 10**len(sa_xxx.group(1))-1)
            name = re.sub(r'(X+)$', str(num), name)
        sa_ggg = re.search(r'(G+)$', name)
        ggg_maxnum = 0
        if sa_ggg:
            ggg_maxnum = 10**len(sa_ggg.group(1))-1
            name = re.sub(r'(G+)$', '', name)
        name = name.lower(); ntype = ntype.upper()
        try:
            maxchars, seq = int(maxchars), int(seq)
            if maxchars < 0 or seq < 1: raise('maxchars or seq is smaller then 1')
        except Exception as err:
            raise SyntaxError('maxchars or seq is wrong %s: %s' % (repr((maxchars, seq)), repr(err)))
        if desc in (None, ''):
            desc = time.strftime('%Y-%m-%d')
        if ggg_maxnum > 0:
            if self._genstate is None:
                self._genstate = ggg_maxnum
        self._prefix = prefix
        self._name = name
        self._maxchars = maxchars
        self._ntype = ntype
        self._seq = seq
        self._desc = desc

    def prefix(self, sep = ''):
        if self._prefix is None: return ''
        return self._prefix + sep
    def name(self, plain = False):
        if self._genstate is not None and not plain:
            return "%s%d" % (self._name, self._genstate)
        return self._name
    def maxchars(self): return self._maxchars
    def nmaxchars(self): return '' if self._maxchars == 0 else str(self._maxchars)
    def ntype(self): return self._ntype
    def seq(self): return self._seq
    def desc(self): return self._desc
    def genstate(self): return self._genstate

    def short(self, plain = False):
        return "%s%s %s%s" % (self.prefix(sep = ' '), self.name(plain), self.nmaxchars(), self._ntype)

    def regular(self, plain = False):
        return "%s %d" % (self.short(plain), self._seq)

    def full(self, plain = False):
        return "%s %s" % (self.regular(plain), self._desc)

class LesSKEY(object):
    def __init__(self, seed, uio, storage, master = None, logins = None, genstate = None):
        self._seed_str = seed
        self._uio = uio
        self._storage = storage
        self._master = master
        self._logins = logins
        self._genstate = genstate
        self._clear_screen = False
        self._found_seeds = {}

    def get_logins_seed(self):
        if self._seed_str is None and self._logins is not None:
            counter = 1
            with Popen(['logins', self._logins], stdout = PIPE) as fd:
                self._uio.output("output of the logins command:")
                for line in fd.stdout:
                    self._seed_str = line.decode('utf-8').strip()
                    seedkey = hex(counter)[2:]
                    counter += 1
                    self._found_seeds[seedkey] = self._seed_str
                    self._uio.output("%s: %s" % (seedkey, self._seed_str))
            if fd.returncode != 0:
                self._uio.output("ERROR: Failed to call command 'logins'!")
                return False
            if self._seed_str is not None:
                ma_seed = re.match(r'^[^ :]+:\s+[0-9]+\s+(.*)$', self._seed_str)
                if ma_seed: self._seed_str = ma_seed.group(1)
        if self._seed_str is None:
            try: self._seed_str = self._uio.input('name> ')
            except:
                self._uio.output("")
                return False
        return True

    def storage_state(self):
        sseed = hashlib.sha1(self._seed.short().encode('utf-8')).hexdigest()
        smaster = hashlib.sha1(self._master.encode('utf-8')).hexdigest()
        sseedmaster = hashlib.sha1((self._seed.short() + self._master).encode('utf-8')).hexdigest()
        with self._storage as stored:
            if sseedmaster in stored: sstate = "correct"
            elif sseed in stored and smaster in stored: sstate = "incorrect"
            elif sseed in stored: sstate = "known seed"
            elif smaster in stored: sstate = "known password"
            else: sstate = "unknown"
        return sstate

    def password(self):
        skey = SKey(self._seed.name(), self._master, self._seed.seq())
        passstr = None

        if self._seed.ntype() in ('R', 'U', 'UR'):
            passstr = self._seed.prefix(sep = ' ') + ' '.join(skey.towords())
        elif self._seed.ntype().endswith('N'):
            passstr = self._seed.prefix(sep = '-') + '-'.join(skey.towords())
        elif self._seed.ntype().endswith('B'):
            passstr = self._seed.prefix() + skey.tob64()
        elif self._seed.ntype().endswith('H'):
            passstr = self._seed.prefix() + skey.tohex()
        elif self._seed.ntype() == 'D':
            passstr = ' '.join([str(x) for x in skey.todec()])
        elif self._seed.ntype() == 'ND':
            passstr = ''.join([str(x) for x in skey.todec()])
        else: raise RuntimeError('Unknown type: %s' % repr(self._seed.ntype()))

        if self._seed.maxchars() > 0:
            passstr = passstr.replace(' ', '')[:self._seed.maxchars()]
        if self._seed.ntype().startswith('U'):
            passstr = passstr.upper()
        return passstr

    def next_genstate(self):
        if self._seed.genstate() > 0:
            passstring = self.password()
            self._uio.output("% 2d/% 4d % 20s: %s" % (len(passstring), self._seed.genstate(), self._seed.regular(), passstring))
            return LesSKEY(self._seed.regular(plain = True), uio, storage, master = self._master, logins = None, genstate = self._seed.genstate() - 1)
        return None

    def initialize_master(self):
        if self._master is None:
            try: self._master = self._uio.input('master> ', password = True)
            except: self._uio.output(""); sys.exit(1)
            if len(self._master) < 4 and re.match(r'^[0-9a-f]+$', self._master) and self._master in self._found_seeds:
                return LesSKEY(self._found_seeds[self._master], uio = uio, storage = storage, logins = self._logins)
            elif self._master == 'n':
                return LesSKEY(None, uio = uio, storage = storage, master = None)
        return None

    def __call__(self):
        if not self.get_logins_seed():
            return None
        while True:
            try:
                self._seed = Seed(self._seed_str, self._genstate)
                break
            except SyntaxError as err:
                self._io.output('failed to parse seed: %s' % err.msg)
                try: self._seed_str = self._uio.input('new seed> ')
                except:
                    self._uio.output("")
                    return None
        if self._seed.genstate() is None:
            self._uio.output("using %s as seed" % repr(self._seed.regular()))
        next_master = self.initialize_master()
        if next_master is not None:
            return next_master
        if self._seed.genstate() is not None:
            return self.next_genstate()

        self._uio.output("seed (%s): %s" % (self.storage_state(), self._seed.full()))
        self._uio.output("password is generated, how you want to get it?")
        while True:
            try: next_cmd = self._uio.input('command (? for help)> ')
            except: next_cmd = ''
            if next_cmd == 'l':
                break
            elif next_cmd == 'n':
                return LesSKEY(None, uio, storage, master = self.password(), logins = self._logins)
            elif next_cmd.startswith('n '):
                next_seed = next_cmd[2:].strip()
                if next_seed != '' and next_seed not in self._found_seeds:
                    return LesSKEY(None, uio, storage, master = self.password(), logins = next_seed)
                elif next_seed in self._found_seeds:
                    return LesSKEY(self._found_seeds[next_seed], uio, storage, master = self.password(), logins = self._logins)
                return LesSKEY(None, uio, storage, master = self.password(), logins = self._logins)
            elif next_cmd == 'o':
                return LesSKEY(None, uio, storage, master = self._master, logins = self._logins)
            elif next_cmd == 'r':
                return LesSKEY(self._seed.full(), uio, storage, master = None, logins = self._logins)
            elif next_cmd.startswith('o '):
                next_seed = next_cmd[2:].strip()
                if next_seed != '' and next_seed not in self._found_seeds:
                    return LesSKEY(None, uio, storage, master = self._master, logins = next_seed)
                elif next_seed in self._found_seeds:
                    return LesSKEY(self._found_seeds[next_seed], uio, storage, master = self._master, logins = self._logins)
                return LesSKEY(None, uio, storage, master = self._master, logins = self._logins)
            elif next_cmd == 's':
                self._storage.store(self._seed.short(), self._master)
            elif next_cmd == 'd':
                self._storage.delete(self._seed.short(), self._master)
            elif next_cmd == 'p':
                self._clear_screen = True
                self._uio.output(self.password())
            elif next_cmd == 'm':
                self._uio.copy_mac(self.password())
            elif next_cmd == 'x':
                self._uio.copy_x11(self.password())
            elif next_cmd == 't':
                self._uio.copy_tmux(self.password())
            elif next_cmd == 'S':
                full_seed = self._seed.full()
                self._uio.copy_mac(full_seed, name = 'seed')
                self._uio.copy_x11(full_seed, name = 'seed')
                self._uio.copy_tmux(full_seed, name = 'seed')
            elif next_cmd == 'q':
                if self._clear_screen:
                    self._uio.clear()
                break
            else:
                self._uio.output("""
Available commands next commands:
p - print generated password
t - copy to tmux buffer
x - copy to X11 clipboard using xclip utility
m - copy to Mac OS X paste board
S - copy seed with all avaible methods
q - clear screen and exit
l - exit, don't clear screen
n - next name in hierarchy (give next seed as optional argument)
o - other seed with same master (give seed as optional argument)
r - retype master with current seed
s - store password and name (as SHA1 checksum)
d - delete stored name and password
""")
        return None

def usage(msg = None):
    if msg is not None:
        sys.stderr.write('ERROR: %s\n\n' % msg)
    sys.stderr.write('Usage: %s <seed>\n' % sys.argv[0])
    with Popen(['less', '-S'], stdin = PIPE) as fd:
        fd.stdin.write(b"""Usage: %s [-h|-l <search term>|<seed>]

LesS/KEY password manager.

This is a project to build a password management tool based on the S/Key system
described in the RFC2289. This password manager is made with following goals in
mind:

- Passwords need to be memorable, secure and easy to type on any keyboard.
- The passwords which are generated with LesS/KEY can be easy momoized and used
  without the generator. Generate the passwords only if you forgot a password,
  it reduces the number of times you enter your master password and make the
  system much more secure.
- It should work every where.
- In fact you even do not require this particular tool, but can use any tool
  which is capable of generating S/Key SHA-1 passwords. So you have the
  garantee, that you can generate the password also without access to this
  particular tool. For most UNIX systems you can install the skey or equivalent
  command, which also generate exactly the same passwords.
- You should be able to use it in a safe way even if the whole time you generate
  a password some body look on your screen.
- With LesS/KEY you can generate your passwords securely, also if some body look
  on your screen and you are on a foreign PC. (do not generate passwords on
  devices that you do not trust!)
- It should work offline and should never send anything through network.
- Files from this repository and a browser are enought to use this tool, you do
  not need to install something. It is also usable on any smart phone or similar
  devices, also without permanent connection to the internet.
- It should not store anything anywhere and should be also usable on foreign
  systems.

More information here: https://github.com/ooke/lesskey

Command line arguments:
-h|--help                  show this help
-l|--login <search term>   call 'logins <search term>' command for seed
<seed>                     the seed to use as string


<seed> should be specified as a single string with following format:
  [prefix] <name> [length][mode] [seq]

Samples:
     amazon            (same as: amazan R 99)
     amazon R 99       (simple name)
     amazon4 R 99      (more unique)
     amazon4 8B 99     (8 characters)
     @T amazon4 B 99   (with "@T" prefix)

The name can be simply entered as string without spaces, default mode and seq
will be added automatically.

<prefix>
  Optional string which will be appended to the generated password as it
  is. This string is useful only to comply with meaningless policy rules.

<name> The name to use for generating, all uppercase X characters at the end
  will be replaced by a random number. Use the numbers to make the names more
  unique and easier changable. If the name contains one or several uppercase G
  characters, then the system will generate passwords for all possible numbers
  of the given length to choose from.

[length]
  Length is optional and specifies maximal number of characters the password
  should have.

[mode]
  The mode to use for generating:
       R	regular password
       U	uppercase password (fully S/Key compatible)
       N	mode R with '-' instead of spaces
       UN	mode N in uppercase
       H	password as hexadecimal string
       UH	mode H in uppecase
       B	password in base64 format
       UB	mode B in uppercase
       D	decimal format (digets only)

[seq]
  The S/Key sequence number, default is 99 and should only be changed if you
  really understand what you do.

If <search term> is used, than a hardcoded script named 'logins' is used, to
find stored seeds text, this command should be written by user, f.e. it can be
written as follows:

#!/bin/sh
exec grep "$1" ~/.my_seeds

In this mode the master also accepts the id of the found seeds to restart and
use the specified seed instead of the last one.
""")
    return 1

WORDS = ["a",     "abe",   "ace",   "act",   "ad",    "ada",   "add",
         "ago",   "aid",   "aim",   "air",   "all",   "alp",   "am",    "amy",
         "an",    "ana",   "and",   "ann",   "ant",   "any",   "ape",   "aps",
         "apt",   "arc",   "are",   "ark",   "arm",   "art",   "as",    "ash",
         "ask",   "at",    "ate",   "aug",   "auk",   "ave",   "awe",   "awk",
         "awl",   "awn",   "ax",    "aye",   "bad",   "bag",   "bah",   "bam",
         "ban",   "bar",   "bat",   "bay",   "be",    "bed",   "bee",   "beg",
         "ben",   "bet",   "bey",   "bib",   "bid",   "big",   "bin",   "bit",
         "bob",   "bog",   "bon",   "boo",   "bop",   "bow",   "boy",   "bub",
         "bud",   "bug",   "bum",   "bun",   "bus",   "but",   "buy",   "by",
         "bye",   "cab",   "cal",   "cam",   "can",   "cap",   "car",   "cat",
         "caw",   "cod",   "cog",   "col",   "con",   "coo",   "cop",   "cot",
         "cow",   "coy",   "cry",   "cub",   "cue",   "cup",   "cur",   "cut",
         "dab",   "dad",   "dam",   "dan",   "dar",   "day",   "dee",   "del",
         "den",   "des",   "dew",   "did",   "die",   "dig",   "din",   "dip",
         "do",    "doe",   "dog",   "don",   "dot",   "dow",   "dry",   "dub",
         "dud",   "due",   "dug",   "dun",   "ear",   "eat",   "ed",    "eel",
         "egg",   "ego",   "eli",   "elk",   "elm",   "ely",   "em",    "end",
         "est",   "etc",   "eva",   "eve",   "ewe",   "eye",   "fad",   "fan",
         "far",   "fat",   "fay",   "fed",   "fee",   "few",   "fib",   "fig",
         "fin",   "fir",   "fit",   "flo",   "fly",   "foe",   "fog",   "for",
         "fry",   "fum",   "fun",   "fur",   "gab",   "gad",   "gag",   "gal",
         "gam",   "gap",   "gas",   "gay",   "gee",   "gel",   "gem",   "get",
         "gig",   "gil",   "gin",   "go",    "got",   "gum",   "gun",   "gus",
         "gut",   "guy",   "gym",   "gyp",   "ha",    "had",   "hal",   "ham",
         "han",   "hap",   "has",   "hat",   "haw",   "hay",   "he",    "hem",
         "hen",   "her",   "hew",   "hey",   "hi",    "hid",   "him",   "hip",
         "his",   "hit",   "ho",    "hob",   "hoc",   "hoe",   "hog",   "hop",
         "hot",   "how",   "hub",   "hue",   "hug",   "huh",   "hum",   "hut",
         "i",     "icy",   "ida",   "if",    "ike",   "ill",   "ink",   "inn",
         "io",    "ion",   "iq",    "ira",   "ire",   "irk",   "is",    "it",
         "its",   "ivy",   "jab",   "jag",   "jam",   "jan",   "jar",   "jaw",
         "jay",   "jet",   "jig",   "jim",   "jo",    "job",   "joe",   "jog",
         "jot",   "joy",   "jug",   "jut",   "kay",   "keg",   "ken",   "key",
         "kid",   "kim",   "kin",   "kit",   "la",    "lab",   "lac",   "lad",
         "lag",   "lam",   "lap",   "law",   "lay",   "lea",   "led",   "lee",
         "leg",   "len",   "leo",   "let",   "lew",   "lid",   "lie",   "lin",
         "lip",   "lit",   "lo",    "lob",   "log",   "lop",   "los",   "lot",
         "lou",   "low",   "loy",   "lug",   "lye",   "ma",    "mac",   "mad",
         "mae",   "man",   "mao",   "map",   "mat",   "maw",   "may",   "me",
         "meg",   "mel",   "men",   "met",   "mew",   "mid",   "min",   "mit",
         "mob",   "mod",   "moe",   "moo",   "mop",   "mos",   "mot",   "mow",
         "mud",   "mug",   "mum",   "my",    "nab",   "nag",   "nan",   "nap",
         "nat",   "nay",   "ne",    "ned",   "nee",   "net",   "new",   "nib",
         "nil",   "nip",   "nit",   "no",    "nob",   "nod",   "non",   "nor",
         "not",   "nov",   "now",   "nu",    "nun",   "nut",   "o",     "oaf",
         "oak",   "oar",   "oat",   "odd",   "ode",   "of",    "off",   "oft",
         "oh",    "oil",   "ok",    "old",   "on",    "one",   "or",    "orb",
         "ore",   "orr",   "os",    "ott",   "our",   "out",   "ova",   "ow",
         "owe",   "owl",   "own",   "ox",    "pa",    "pad",   "pal",   "pam",
         "pan",   "pap",   "par",   "pat",   "paw",   "pay",   "pea",   "peg",
         "pen",   "pep",   "per",   "pet",   "pew",   "phi",   "pi",    "pie",
         "pin",   "pit",   "ply",   "po",    "pod",   "poe",   "pop",   "pot",
         "pow",   "pro",   "pry",   "pub",   "pug",   "pun",   "pup",   "put",
         "quo",   "rag",   "ram",   "ran",   "rap",   "rat",   "raw",   "ray",
         "reb",   "red",   "rep",   "ret",   "rib",   "rid",   "rig",   "rim",
         "rio",   "rip",   "rob",   "rod",   "roe",   "ron",   "rot",   "row",
         "roy",   "rub",   "rue",   "rug",   "rum",   "run",   "rye",   "sac",
         "sad",   "sag",   "sal",   "sam",   "san",   "sap",   "sat",   "saw",
         "say",   "sea",   "sec",   "see",   "sen",   "set",   "sew",   "she",
         "shy",   "sin",   "sip",   "sir",   "sis",   "sit",   "ski",   "sky",
         "sly",   "so",    "sob",   "sod",   "son",   "sop",   "sow",   "soy",
         "spa",   "spy",   "sub",   "sud",   "sue",   "sum",   "sun",   "sup",
         "tab",   "tad",   "tag",   "tan",   "tap",   "tar",   "tea",   "ted",
         "tee",   "ten",   "the",   "thy",   "tic",   "tie",   "tim",   "tin",
         "tip",   "to",    "toe",   "tog",   "tom",   "ton",   "too",   "top",
         "tow",   "toy",   "try",   "tub",   "tug",   "tum",   "tun",   "two",
         "un",    "up",    "us",    "use",   "van",   "vat",   "vet",   "vie",
         "wad",   "wag",   "war",   "was",   "way",   "we",    "web",   "wed",
         "wee",   "wet",   "who",   "why",   "win",   "wit",   "wok",   "won",
         "woo",   "wow",   "wry",   "wu",    "yam",   "yap",   "yaw",   "ye",
         "yea",   "yes",   "yet",   "you",   "abed",  "abel",  "abet",  "able",
         "abut",  "ache",  "acid",  "acme",  "acre",  "acta",  "acts",  "adam",
         "adds",  "aden",  "afar",  "afro",  "agee",  "ahem",  "ahoy",  "aida",
         "aide",  "aids",  "airy",  "ajar",  "akin",  "alan",  "alec",  "alga",
         "alia",  "ally",  "alma",  "aloe",  "also",  "alto",  "alum",  "alva",
         "amen",  "ames",  "amid",  "ammo",  "amok",  "amos",  "amra",  "andy",
         "anew",  "anna",  "anne",  "ante",  "anti",  "aqua",  "arab",  "arch",
         "area",  "argo",  "arid",  "army",  "arts",  "arty",  "asia",  "asks",
         "atom",  "aunt",  "aura",  "auto",  "aver",  "avid",  "avis",  "avon",
         "avow",  "away",  "awry",  "babe",  "baby",  "bach",  "back",  "bade",
         "bail",  "bait",  "bake",  "bald",  "bale",  "bali",  "balk",  "ball",
         "balm",  "band",  "bane",  "bang",  "bank",  "barb",  "bard",  "bare",
         "bark",  "barn",  "barr",  "base",  "bash",  "bask",  "bass",  "bate",
         "bath",  "bawd",  "bawl",  "bead",  "beak",  "beam",  "bean",  "bear",
         "beat",  "beau",  "beck",  "beef",  "been",  "beer",  "beet",  "bela",
         "bell",  "belt",  "bend",  "bent",  "berg",  "bern",  "bert",  "bess",
         "best",  "beta",  "beth",  "bhoy",  "bias",  "bide",  "bien",  "bile",
         "bilk",  "bill",  "bind",  "bing",  "bird",  "bite",  "bits",  "blab",
         "blat",  "bled",  "blew",  "blob",  "bloc",  "blot",  "blow",  "blue",
         "blum",  "blur",  "boar",  "boat",  "boca",  "bock",  "bode",  "body",
         "bogy",  "bohr",  "boil",  "bold",  "bolo",  "bolt",  "bomb",  "bona",
         "bond",  "bone",  "bong",  "bonn",  "bony",  "book",  "boom",  "boon",
         "boot",  "bore",  "borg",  "born",  "bose",  "boss",  "both",  "bout",
         "bowl",  "boyd",  "brad",  "brae",  "brag",  "bran",  "bray",  "bred",
         "brew",  "brig",  "brim",  "brow",  "buck",  "budd",  "buff",  "bulb",
         "bulk",  "bull",  "bunk",  "bunt",  "buoy",  "burg",  "burl",  "burn",
         "burr",  "burt",  "bury",  "bush",  "buss",  "bust",  "busy",  "byte",
         "cady",  "cafe",  "cage",  "cain",  "cake",  "calf",  "call",  "calm",
         "came",  "cane",  "cant",  "card",  "care",  "carl",  "carr",  "cart",
         "case",  "cash",  "cask",  "cast",  "cave",  "ceil",  "cell",  "cent",
         "cern",  "chad",  "char",  "chat",  "chaw",  "chef",  "chen",  "chew",
         "chic",  "chin",  "chou",  "chow",  "chub",  "chug",  "chum",  "cite",
         "city",  "clad",  "clam",  "clan",  "claw",  "clay",  "clod",  "clog",
         "clot",  "club",  "clue",  "coal",  "coat",  "coca",  "cock",  "coco",
         "coda",  "code",  "cody",  "coed",  "coil",  "coin",  "coke",  "cola",
         "cold",  "colt",  "coma",  "comb",  "come",  "cook",  "cool",  "coon",
         "coot",  "cord",  "core",  "cork",  "corn",  "cost",  "cove",  "cowl",
         "crab",  "crag",  "cram",  "cray",  "crew",  "crib",  "crow",  "crud",
         "cuba",  "cube",  "cuff",  "cull",  "cult",  "cuny",  "curb",  "curd",
         "cure",  "curl",  "curt",  "cuts",  "dade",  "dale",  "dame",  "dana",
         "dane",  "dang",  "dank",  "dare",  "dark",  "darn",  "dart",  "dash",
         "data",  "date",  "dave",  "davy",  "dawn",  "days",  "dead",  "deaf",
         "deal",  "dean",  "dear",  "debt",  "deck",  "deed",  "deem",  "deer",
         "deft",  "defy",  "dell",  "dent",  "deny",  "desk",  "dial",  "dice",
         "died",  "diet",  "dime",  "dine",  "ding",  "dint",  "dire",  "dirt",
         "disc",  "dish",  "disk",  "dive",  "dock",  "does",  "dole",  "doll",
         "dolt",  "dome",  "done",  "doom",  "door",  "dora",  "dose",  "dote",
         "doug",  "dour",  "dove",  "down",  "drab",  "drag",  "dram",  "draw",
         "drew",  "drub",  "drug",  "drum",  "dual",  "duck",  "duct",  "duel",
         "duet",  "duke",  "dull",  "dumb",  "dune",  "dunk",  "dusk",  "dust",
         "duty",  "each",  "earl",  "earn",  "ease",  "east",  "easy",  "eben",
         "echo",  "eddy",  "eden",  "edge",  "edgy",  "edit",  "edna",  "egan",
         "elan",  "elba",  "ella",  "else",  "emil",  "emit",  "emma",  "ends",
         "eric",  "eros",  "even",  "ever",  "evil",  "eyed",  "face",  "fact",
         "fade",  "fail",  "fain",  "fair",  "fake",  "fall",  "fame",  "fang",
         "farm",  "fast",  "fate",  "fawn",  "fear",  "feat",  "feed",  "feel",
         "feet",  "fell",  "felt",  "fend",  "fern",  "fest",  "feud",  "fief",
         "figs",  "file",  "fill",  "film",  "find",  "fine",  "fink",  "fire",
         "firm",  "fish",  "fisk",  "fist",  "fits",  "five",  "flag",  "flak",
         "flam",  "flat",  "flaw",  "flea",  "fled",  "flew",  "flit",  "floc",
         "flog",  "flow",  "flub",  "flue",  "foal",  "foam",  "fogy",  "foil",
         "fold",  "folk",  "fond",  "font",  "food",  "fool",  "foot",  "ford",
         "fore",  "fork",  "form",  "fort",  "foss",  "foul",  "four",  "fowl",
         "frau",  "fray",  "fred",  "free",  "fret",  "frey",  "frog",  "from",
         "fuel",  "full",  "fume",  "fund",  "funk",  "fury",  "fuse",  "fuss",
         "gaff",  "gage",  "gail",  "gain",  "gait",  "gala",  "gale",  "gall",
         "galt",  "game",  "gang",  "garb",  "gary",  "gash",  "gate",  "gaul",
         "gaur",  "gave",  "gawk",  "gear",  "geld",  "gene",  "gent",  "germ",
         "gets",  "gibe",  "gift",  "gild",  "gill",  "gilt",  "gina",  "gird",
         "girl",  "gist",  "give",  "glad",  "glee",  "glen",  "glib",  "glob",
         "glom",  "glow",  "glue",  "glum",  "glut",  "goad",  "goal",  "goat",
         "goer",  "goes",  "gold",  "golf",  "gone",  "gong",  "good",  "goof",
         "gore",  "gory",  "gosh",  "gout",  "gown",  "grab",  "grad",  "gray",
         "greg",  "grew",  "grey",  "grid",  "grim",  "grin",  "grit",  "grow",
         "grub",  "gulf",  "gull",  "gunk",  "guru",  "gush",  "gust",  "gwen",
         "gwyn",  "haag",  "haas",  "hack",  "hail",  "hair",  "hale",  "half",
         "hall",  "halo",  "halt",  "hand",  "hang",  "hank",  "hans",  "hard",
         "hark",  "harm",  "hart",  "hash",  "hast",  "hate",  "hath",  "haul",
         "have",  "hawk",  "hays",  "head",  "heal",  "hear",  "heat",  "hebe",
         "heck",  "heed",  "heel",  "heft",  "held",  "hell",  "helm",  "herb",
         "herd",  "here",  "hero",  "hers",  "hess",  "hewn",  "hick",  "hide",
         "high",  "hike",  "hill",  "hilt",  "hind",  "hint",  "hire",  "hiss",
         "hive",  "hobo",  "hock",  "hoff",  "hold",  "hole",  "holm",  "holt",
         "home",  "hone",  "honk",  "hood",  "hoof",  "hook",  "hoot",  "horn",
         "hose",  "host",  "hour",  "hove",  "howe",  "howl",  "hoyt",  "huck",
         "hued",  "huff",  "huge",  "hugh",  "hugo",  "hulk",  "hull",  "hunk",
         "hunt",  "hurd",  "hurl",  "hurt",  "hush",  "hyde",  "hymn",  "ibis",
         "icon",  "idea",  "idle",  "iffy",  "inca",  "inch",  "into",  "ions",
         "iota",  "iowa",  "iris",  "irma",  "iron",  "isle",  "itch",  "item",
         "ivan",  "jack",  "jade",  "jail",  "jake",  "jane",  "java",  "jean",
         "jeff",  "jerk",  "jess",  "jest",  "jibe",  "jill",  "jilt",  "jive",
         "joan",  "jobs",  "jock",  "joel",  "joey",  "john",  "join",  "joke",
         "jolt",  "jove",  "judd",  "jude",  "judo",  "judy",  "juju",  "juke",
         "july",  "june",  "junk",  "juno",  "jury",  "just",  "jute",  "kahn",
         "kale",  "kane",  "kant",  "karl",  "kate",  "keel",  "keen",  "keno",
         "kent",  "kern",  "kerr",  "keys",  "kick",  "kill",  "kind",  "king",
         "kirk",  "kiss",  "kite",  "klan",  "knee",  "knew",  "knit",  "knob",
         "knot",  "know",  "koch",  "kong",  "kudo",  "kurd",  "kurt",  "kyle",
         "lace",  "lack",  "lacy",  "lady",  "laid",  "lain",  "lair",  "lake",
         "lamb",  "lame",  "land",  "lane",  "lang",  "lard",  "lark",  "lass",
         "last",  "late",  "laud",  "lava",  "lawn",  "laws",  "lays",  "lead",
         "leaf",  "leak",  "lean",  "lear",  "leek",  "leer",  "left",  "lend",
         "lens",  "lent",  "leon",  "lesk",  "less",  "lest",  "lets",  "liar",
         "lice",  "lick",  "lied",  "lien",  "lies",  "lieu",  "life",  "lift",
         "like",  "lila",  "lilt",  "lily",  "lima",  "limb",  "lime",  "lind",
         "line",  "link",  "lint",  "lion",  "lisa",  "list",  "live",  "load",
         "loaf",  "loam",  "loan",  "lock",  "loft",  "loge",  "lois",  "lola",
         "lone",  "long",  "look",  "loon",  "loot",  "lord",  "lore",  "lose",
         "loss",  "lost",  "loud",  "love",  "lowe",  "luck",  "lucy",  "luge",
         "luke",  "lulu",  "lund",  "lung",  "lura",  "lure",  "lurk",  "lush",
         "lust",  "lyle",  "lynn",  "lyon",  "lyra",  "mace",  "made",  "magi",
         "maid",  "mail",  "main",  "make",  "male",  "mali",  "mall",  "malt",
         "mana",  "mann",  "many",  "marc",  "mare",  "mark",  "mars",  "mart",
         "mary",  "mash",  "mask",  "mass",  "mast",  "mate",  "math",  "maul",
         "mayo",  "mead",  "meal",  "mean",  "meat",  "meek",  "meet",  "meld",
         "melt",  "memo",  "mend",  "menu",  "mert",  "mesh",  "mess",  "mice",
         "mike",  "mild",  "mile",  "milk",  "mill",  "milt",  "mimi",  "mind",
         "mine",  "mini",  "mink",  "mint",  "mire",  "miss",  "mist",  "mite",
         "mitt",  "moan",  "moat",  "mock",  "mode",  "mold",  "mole",  "moll",
         "molt",  "mona",  "monk",  "mont",  "mood",  "moon",  "moor",  "moot",
         "more",  "morn",  "mort",  "moss",  "most",  "moth",  "move",  "much",
         "muck",  "mudd",  "muff",  "mule",  "mull",  "murk",  "mush",  "must",
         "mute",  "mutt",  "myra",  "myth",  "nagy",  "nail",  "nair",  "name",
         "nary",  "nash",  "nave",  "navy",  "neal",  "near",  "neat",  "neck",
         "need",  "neil",  "nell",  "neon",  "nero",  "ness",  "nest",  "news",
         "newt",  "nibs",  "nice",  "nick",  "nile",  "nina",  "nine",  "noah",
         "node",  "noel",  "noll",  "none",  "nook",  "noon",  "norm",  "nose",
         "note",  "noun",  "nova",  "nude",  "null",  "numb",  "oath",  "obey",
         "oboe",  "odin",  "ohio",  "oily",  "oint",  "okay",  "olaf",  "oldy",
         "olga",  "olin",  "oman",  "omen",  "omit",  "once",  "ones",  "only",
         "onto",  "onus",  "oral",  "orgy",  "oslo",  "otis",  "otto",  "ouch",
         "oust",  "outs",  "oval",  "oven",  "over",  "owly",  "owns",  "quad",
         "quit",  "quod",  "race",  "rack",  "racy",  "raft",  "rage",  "raid",
         "rail",  "rain",  "rake",  "rank",  "rant",  "rare",  "rash",  "rate",
         "rave",  "rays",  "read",  "real",  "ream",  "rear",  "reck",  "reed",
         "reef",  "reek",  "reel",  "reid",  "rein",  "rena",  "rend",  "rent",
         "rest",  "rice",  "rich",  "rick",  "ride",  "rift",  "rill",  "rime",
         "ring",  "rink",  "rise",  "risk",  "rite",  "road",  "roam",  "roar",
         "robe",  "rock",  "rode",  "roil",  "roll",  "rome",  "rood",  "roof",
         "rook",  "room",  "root",  "rosa",  "rose",  "ross",  "rosy",  "roth",
         "rout",  "rove",  "rowe",  "rows",  "rube",  "ruby",  "rude",  "rudy",
         "ruin",  "rule",  "rung",  "runs",  "runt",  "ruse",  "rush",  "rusk",
         "russ",  "rust",  "ruth",  "sack",  "safe",  "sage",  "said",  "sail",
         "sale",  "salk",  "salt",  "same",  "sand",  "sane",  "sang",  "sank",
         "sara",  "saul",  "save",  "says",  "scan",  "scar",  "scat",  "scot",
         "seal",  "seam",  "sear",  "seat",  "seed",  "seek",  "seem",  "seen",
         "sees",  "self",  "sell",  "send",  "sent",  "sets",  "sewn",  "shag",
         "sham",  "shaw",  "shay",  "shed",  "shim",  "shin",  "shod",  "shoe",
         "shot",  "show",  "shun",  "shut",  "sick",  "side",  "sift",  "sigh",
         "sign",  "silk",  "sill",  "silo",  "silt",  "sine",  "sing",  "sink",
         "sire",  "site",  "sits",  "situ",  "skat",  "skew",  "skid",  "skim",
         "skin",  "skit",  "slab",  "slam",  "slat",  "slay",  "sled",  "slew",
         "slid",  "slim",  "slit",  "slob",  "slog",  "slot",  "slow",  "slug",
         "slum",  "slur",  "smog",  "smug",  "snag",  "snob",  "snow",  "snub",
         "snug",  "soak",  "soar",  "sock",  "soda",  "sofa",  "soft",  "soil",
         "sold",  "some",  "song",  "soon",  "soot",  "sore",  "sort",  "soul",
         "sour",  "sown",  "stab",  "stag",  "stan",  "star",  "stay",  "stem",
         "stew",  "stir",  "stow",  "stub",  "stun",  "such",  "suds",  "suit",
         "sulk",  "sums",  "sung",  "sunk",  "sure",  "surf",  "swab",  "swag",
         "swam",  "swan",  "swat",  "sway",  "swim",  "swum",  "tack",  "tact",
         "tail",  "take",  "tale",  "talk",  "tall",  "tank",  "task",  "tate",
         "taut",  "teal",  "team",  "tear",  "tech",  "teem",  "teen",  "teet",
         "tell",  "tend",  "tent",  "term",  "tern",  "tess",  "test",  "than",
         "that",  "thee",  "them",  "then",  "they",  "thin",  "this",  "thud",
         "thug",  "tick",  "tide",  "tidy",  "tied",  "tier",  "tile",  "till",
         "tilt",  "time",  "tina",  "tine",  "tint",  "tiny",  "tire",  "toad",
         "togo",  "toil",  "told",  "toll",  "tone",  "tong",  "tony",  "took",
         "tool",  "toot",  "tore",  "torn",  "tote",  "tour",  "tout",  "town",
         "trag",  "tram",  "tray",  "tree",  "trek",  "trig",  "trim",  "trio",
         "trod",  "trot",  "troy",  "true",  "tuba",  "tube",  "tuck",  "tuft",
         "tuna",  "tune",  "tung",  "turf",  "turn",  "tusk",  "twig",  "twin",
         "twit",  "ulan",  "unit",  "urge",  "used",  "user",  "uses",  "utah",
         "vail",  "vain",  "vale",  "vary",  "vase",  "vast",  "veal",  "veda",
         "veil",  "vein",  "vend",  "vent",  "verb",  "very",  "veto",  "vice",
         "view",  "vine",  "vise",  "void",  "volt",  "vote",  "wack",  "wade",
         "wage",  "wail",  "wait",  "wake",  "wale",  "walk",  "wall",  "walt",
         "wand",  "wane",  "wang",  "want",  "ward",  "warm",  "warn",  "wart",
         "wash",  "wast",  "wats",  "watt",  "wave",  "wavy",  "ways",  "weak",
         "weal",  "wean",  "wear",  "weed",  "week",  "weir",  "weld",  "well",
         "welt",  "went",  "were",  "wert",  "west",  "wham",  "what",  "whee",
         "when",  "whet",  "whoa",  "whom",  "wick",  "wife",  "wild",  "will",
         "wind",  "wine",  "wing",  "wink",  "wino",  "wire",  "wise",  "wish",
         "with",  "wolf",  "wont",  "wood",  "wool",  "word",  "wore",  "work",
         "worm",  "worn",  "wove",  "writ",  "wynn",  "yale",  "yang",  "yank",
         "yard",  "yarn",  "yawl",  "yawn",  "yeah",  "year",  "yell",  "yoga",
         "yoke"]

if __name__ == '__main__':
    uio = UserIO()
    storage = Storage(storefile)
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        sys.exit(usage())
    elif len(sys.argv) == 3 and sys.argv[1] in ('-l', '--logins'):
        lk = LesSKEY(None, uio, storage, master = None, logins = sys.argv[2])
    elif len(sys.argv) == 1:
        lk = LesSKEY(None, uio, storage, master = None)
    elif len(sys.argv) == 2:
        lk = LesSKEY(sys.argv[1], uio, storage, master = None)
    else: sys.exit(usage())
    while lk is not None:
        lk = lk()
    sys.exit(0)
