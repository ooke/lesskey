#!/usr/bin/env python3

import lesskey, unittest, hashlib

class TestUIO(lesskey.UserIO):
    def __init__(self, verbose = False):
        self.verbose = verbose
        self.input_data = []
        self.output_data = []
        self.clipboard = {'x11': None, 'tmux': None, 'mac': None}

    def clear(self):
        if self.verbose:
            print("-> clear")
        self.output_data.insert(0, None)

    def output(self, data):
        if self.verbose:
            print("-> %s" % repr(data))
        self.output_data.insert(0, data)

    def input(self, prompt, password = False):
        data, is_passwd = self.input_data.pop()
        if self.verbose:
            print("<- %s: %s" % (repr(prompt), repr(data)))
        if password != is_passwd:
            raise RuntimeError("Expected password=%s but got password=%s" % (repr(password), repr(is_passwd)))
        return data

    def copy_mac(self, data, verbose = True, name = 'password'):
        self.clipboard['mac'] = (data, name)
    def copy_tmux(self, data, verbose = True, name = 'password'):
        self.clipboard['tmux'] = (data, name)
    def copy_x11(self, data, verbose = True, name = 'password'):
        self.clipboard['x11'] = (data, name)
        
    def push(self, data, password = False):
        self.input_data.insert(0, (data, password))

    def pop(self):
        return self.output_data.pop()

class Storage(lesskey.Storage):
    def __init__(self):
        super().__init__('/nonexistent')
        self.stored = set()
    def store(self, nseed, master):
        self.stored.add(hashlib.sha1(nseed.encode('utf-8')).hexdigest())
        self.stored.add(hashlib.sha1(master.encode('utf-8')).hexdigest())
        self.stored.add(hashlib.sha1((nseed + master).encode('utf-8')).hexdigest())
    def delete(self, nseed, master):
        try: self.stored.remove(hashlib.sha1(nseed.encode('utf-8')).hexdigest())
        except: pass
        try: self.stored.remove(hashlib.sha1(master.encode('utf-8')).hexdigest())
        except: pass
        try: self.stored.remove(hashlib.sha1((nseed + master).encode('utf-8')).hexdigest())
        except: pass
    def __enter__(self):
        return self.stored
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class TestLesskey(unittest.TestCase):
    def _regularTest(self, seed, seed2, result, callback = None, store = None, seed_state = 'unknown', password = 'mypasswd1'):
        uio = TestUIO()
        if store is None:
            store = Storage()
        uio.push(password, password = True)
        uio.push('p')
        if callback:
            callback(uio)
        lk = lesskey.LesSKEY(seed, uio, store)
        while lk is not None:
            lk = lk()
        self.assertEqual(uio.pop(), "using '%s' as seed" % seed)
        self.assertRegex(uio.pop(), r"seed \(%s\): %s .*" % (seed_state, seed2))
        self.assertEqual(uio.pop(), "password is generated, how you want to get it?")
        self.assertEqual(uio.pop(), result)
        self.assertEqual(uio.pop(), None)
        return uio

    def test_simple(self):
        self._regularTest('test', 'test R 99', 'cork buck neon lock ross abe')
        self._regularTest('#P3 test', '#P3 test R 99', '#P3 cork buck neon lock ross abe')
        self._regularTest('#P3 test R 99', '#P3 test R 99', '#P3 cork buck neon lock ross abe')
        self._regularTest('test B', 'test B 99', 'a0vvDVitKAA')
        self._regularTest('test B 99', 'test B 99', 'a0vvDVitKAA')
        self._regularTest('#P0 test B', '#P0 test B 99', '#P0a0vvDVitKAA')
        self._regularTest('#P3 test B 99', '#P3 test B 99', '#P3a0vvDVitKAA')
        self._regularTest('test R', 'test R 99', 'cork buck neon lock ross abe')
        self._regularTest('test R 99', 'test R 99', 'cork buck neon lock ross abe')
        self._regularTest('test R 99 my comment', 'test R 99', 'cork buck neon lock ross abe')
        self._regularTest('test N 99', 'test N 99', 'cork-buck-neon-lock-ross-abe')
        self._regularTest('#P3 test N 99', '#P3 test N 99', '#P3-cork-buck-neon-lock-ross-abe')
        self._regularTest('test U 99', 'test U 99', 'CORK BUCK NEON LOCK ROSS ABE')
        self._regularTest('test H 99', 'test H 99', '0def4b6b0028ad58')
        self._regularTest('#P2 test H 99', '#P2 test H 99', '#P20def4b6b0028ad58')
        self._regularTest('test UH 99', 'test UH 99', '0DEF4B6B0028AD58')
        self._regularTest('#P2 test UH 99', '#P2 test UH 99', '#P20DEF4B6B0028AD58')
        self._regularTest('test D 99', 'test D 99', '858 763 1562 1418 1684 1')
        self._regularTest('test 4D 99', 'test 4D 99', '8587')
        self._regularTest('test 5D 99', 'test 5D 99', '85876')
        self._regularTest('#P1 test 4D 99', '#P1 test R 4', '#P1 brae quod roe dome aim vail')
        self._regularTest('test 5UH 99', 'test 5UH 99', '0DEF4')
        self._regularTest('#P2 test 5UH 99', '#P2 test 5UH 99', '#P20D')
        self._regularTest('test 5R 99', 'test 5R 99', 'corkb')
        self._regularTest('#P3 test 5R 99', '#P3 test 5R 99', '#P3co')
        self._regularTest('test 5U 99', 'test 5U 99', 'CORKB')
        self._regularTest('test 5H 99', 'test 5H 99', '0def4')
        self._regularTest('#P2 test 5H 99', '#P2 test 5H 99', '#P20d')

    def test_clipboard(self):
        uio = self._regularTest('#P3 test R 99', '#P3 test R 99', '#P3 cork buck neon lock ross abe',
                                callback = lambda uio: uio.push('m'))
        self.assertEqual(uio.clipboard, {'x11': None, 'tmux': None, 'mac': ('#P3 cork buck neon lock ross abe', 'password')})
        uio = self._regularTest('#P3 test R 99', '#P3 test R 99', '#P3 cork buck neon lock ross abe',
                                callback = lambda uio: uio.push('x'))
        self.assertEqual(uio.clipboard, {'mac': None, 'tmux': None, 'x11': ('#P3 cork buck neon lock ross abe', 'password')})
        uio = self._regularTest('#P3 test R 99', '#P3 test R 99', '#P3 cork buck neon lock ross abe',
                                callback = lambda uio: uio.push('t'))
        self.assertEqual(uio.clipboard, {'mac': None, 'x11': None, 'tmux': ('#P3 cork buck neon lock ross abe', 'password')})
        uio = self._regularTest('#P3 test R 99 comment', '#P3 test R 99', '#P3 cork buck neon lock ross abe',
                                callback = lambda uio: uio.push('S'))
        self.assertEqual(uio.clipboard, {'mac': ('#P3 test R 99 comment', 'seed'),
                                         'x11': ('#P3 test R 99 comment', 'seed'),
                                         'tmux': ('#P3 test R 99 comment', 'seed')})

    def test_storage(self):
        store = Storage()
        self._regularTest('test R 99', 'test R 99', 'cork buck neon lock ross abe',
                          callback = lambda uio: uio.push('s'),
                          store = store, seed_state = 'unknown')
        self._regularTest('test R 99', 'test R 99', 'cork buck neon lock ross abe',
                          store = store, seed_state = 'correct')
        self._regularTest('test R 99', 'test R 99', 'comb took been swat muff fund',
                          password = 'myotherpasswd',
                          store = store, seed_state = 'known seed')
        self._regularTest('test2 R 99', 'test2 R 99', 'bawd kick oral ames beer find',
                          store = store, seed_state = 'known password')
        self._regularTest('test3 R 99', 'test3 R 99', 'alp swam swan kent grey tow',
                          callback = lambda uio: uio.push('s'),
                          password = 'mywrongpassword1',
                          store = store, seed_state = 'unknown')
        self._regularTest('test R 99', 'test R 99', 'kurd bury aura bits alia bane',
                          password = 'mywrongpassword1',
                          store = store, seed_state = 'incorrect')
        self._regularTest('test3 R 99', 'test3 R 99', 'alp swam swan kent grey tow',
                          callback = lambda uio: uio.push('d'),
                          password = 'mywrongpassword1',
                          store = store, seed_state = 'correct')
        self._regularTest('test3 R 99', 'test3 R 99', 'alp swam swan kent grey tow',
                          password = 'mywrongpassword1',
                          store = store, seed_state = 'unknown')
        
if __name__ == '__main__':
    unittest.main()
