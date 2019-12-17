# LesS/KEY

This is a project to build a password management tool based on the
S/Key system described in the
[RFC2289](https://tools.ietf.org/html/rfc2289). This password manager
is made with following goals in mind:

1. Passwords need to be memorable, secure and easy to type on any keyboard.

   The passwords which are generated with LesS/KEY can be easily memorized and
   used without the generator. Generate the passwords only if you forgot a
   password, it reduces the number of times you enter your master password
   dramatically. You also don't need to remember all of your passwords, remember
   those you really use, for the rest use LesS/KEY. I have managed over 500
   passwords with this password manager for years now and I memorized
   approximately 10 of often used used passwords.

1. It should work everywhere.

   In fact, you even do not require this particular tool, but can use any tool
   which is capable of generating S/Key SHA-1 passwords. So you have the
   guarantee, that you can generate the password also without access to this
   particular tool. For most UNIX systems you can install the `skey` or
   equivalent command, which also generate exactly the same passwords.
   
1. You should be able to use it in a safe way, even if the whole time you
   generate a password somebody look on your screen.
   
   With LesS/KEY you can generate your passwords securely, also if somebody
   looks on your screen and you are on a foreign PC. (do not generate passwords
   on devices that you do not trust!)
   
1. It should work offline and should never send anything through the network.
   
   Files from this repository and a browser are enough to use this tool, you do
   not need to install something. It is also usable on any smart phone or
   similar devices, also without permanent connection to the internet.
   
1. It should not store anything anywhere and should be also usable on foreign
   systems.
   
   This password manager doesn't store your passwords or the names somewhere, so
   you should write your password names down and it is safe to do so, names have
   no security value. You have here a store button, it stores the checksum of
   your password name and the checksum of the master password in your
   browser. If you use this feature, the system will show you whether you typed
   an already used name or already used master password. It helps avoiding typos
   in master passwords a lot.

Fully usable installation: https://ooke.github.io/sk/

To use it in a shell, you can take the Python implementation here: <br/>
https://github.com/ooke/lesskey/blob/master/lesskey.py

On *BSD systems you could also just use `skey -t sha1 99 test3`, it is usually
preinstalled, but does not support different modes. For some strange reason, on
Linux systems it is no easy way to install this tool.

# General use case

This is password manager and a password generator, you need a main
password (`secret`) and you can generate a password based on a
name (`seed`). Typical usage:

1. Enter a name to the `seed` field, f.e. if you need a password for
   Amazon, just type `amazon` there. It is also possible to enter
   `amazonXX` with any number of `X` after the name, in this case the
   system will replace all `X` characters with a random number with
   maximum number of digits equals to number of `X` entered. This is
   usefull if you think to change the password on a regular basis,
   simply enter again `XX` and it will generate a new number and a new
   password. The format of the seed field is following:

   ```
     [prefix] <name> [length][mode] [seq] [desc]
   ```
   
   Samples:
   ```
        amazon            (same as: amazan R 99)
        amazon R 99       (simple name)
        amazon4 R 99      (more unique)
        amazon4 8B 99     (8 characters)
        @T amazon4 B 99   (with "@T" prefix)
   ```
   
   The name can be simply entered as string without spaces, default mode and seq
   will be added automatically.
   
   - `<prefix>`
     Optional string which will be appended to the generated password as it
     is. This string is useful only to comply with meaningless policy rules.
   
   - `<name>`
     The name to use for generating, all uppacase X characters at the end will
     be replaced by a random number. Use the numbers to make the names more unique
     and easier changable.
   
   - `[length]`
     Length is optional and specifies maximal number of characters the password
     should have.
   
   - `[mode]`
     The mode to use for generating:
          - `R` regular password
          - `U` uppercase password (fully S/Key compatible)
          - `N` mode `R` with `-` instead of spaces
          - `UN` mode `N` in uppercase
          - `H` password as hexadecimal string
          - `UH` mode `H` in uppecase
          - `B` password in base64 format
          - `UB` mode `B` in uppercase
          - `D` decimal format (digits only)
   
   - `[seq]`
     The S/Key sequence number, default is 99 and should only be changed if you
     really understand what you do.
     
   - `[desc]`
     Description of the name, if nothing entered, then the system will put the
     current date in there automatically. I copy paste new names always with the
     date, to know later the date I have generated the password on.

      
1. Enter your master password and you can directly copy your generated password
   from next field, after pressing enter or tab the generated password will be
   selected and ready to copy to clipboard. If you click on the button `show`,
   then the master password became visible. If the password was stored once, the
   button `store` became light blue and if the password with this seed was
   stored once, than it bacame green.

This password manager do not store any names or passwords and do not communicate
with anything, all calculations are done within your browser. Common way is to
write down the meta information about each generated password in a system, which
you can access as easy as possible, like in a file. Personally I use
[Evernote](http://www.evernote.com) for it, because I can access it through
browser, on any smart phone through a app and also on the UNIX shell with the
Evernote API. I store following information there:

- Exact `seed` I have used, with prefix and modes
- Date on which the password was generated or changed
- URL of the web page or something else to identify the system
- Login name, birthday entered and similar meta data to be able to
  login or recover password later

The `seed` has no security value, so you do not need to encrypt this
information, only your secret should stay really secret.

Usually you do not need to change the `seq` part of the `seed` (usually `99`),
it is only needed if you use this password manager as a real S/Key calculator,
playing with thin number without knowing what you are doing can lead to security
problems.

# S/Key usage

This password manager can also be used as a S/Key calculator, if you login to a
system with enabled S/Key athentication method, then type the sequence number,
seed and secret and copy/paste your password. Usually it looks like follows:

```
$> ssh karam@outer.space.unknown
Password [ otp-sha1 45 oute52436 ]:
```

From this example you would need to type folowing as seed:
```
oute52436 U 45
```

Warning: only SHA-1 S/Key mode is supported and S/Key is not always safe to
use. Do not use it through unencrypted connections! (I know, S/Key was developed
initally for this case, but trust me, you should not use unencrypted
connections at all, never!)

This is usefull, if your need f.e. login through SSH to your server from a PC,
which you do not fully trust (internet caffee f.e.). You should use then
LesS/KEY on a device you trust, like your smartphone to generate the one time
password and type it on this PC. Even if some body logs the keyboard, this
password became invalid and useless after you typed it in. Man in the middle
attack is still possible but it is very hard to do and to prepare and you are
usually safe, as long you use encrypted connections.

# Hierarchical passwords

It is possible to use multiple master passwords in a hierarhical way:

1. Type a root `seed` and your master-master password.

1. Press enter and type your child `seed` and copy generated password

The reason to use hierarchical passwords is to use different master passwords
for different types of systems. Typically you memoize the generated master
passwords and use it, instead of using the master-master password all the
type. In this way, if you loose the master password you need only reset the
passwords on a bunch of services instead of all services you have ever generated
passwords for.

For example I use one master password for home, one for work and one for regular
web pages. All of the master passwords are still generatable, but I memoize them
and do typically never type the master-master password somewhere. I do also
memoize the generated passwords for all important systems, but if I forget one
(f.e. after a vacation) I can generate it again any time. Some times I do also
forget the master passwords, but they can also be generated, only my main
master-master password is something I need really care about.

# Security considerations

This password manager was inspired by the XKCD commic:

[![password_strength](https://imgs.xkcd.com/comics/password_strength.png)](https://www.xkcd.com/936/)

Internally it generates SHA-1 checksum chained `seq` number of times from `seed`
and `secret` concatenated together. The result is reduced to a 64 bit number
with bitwise XOR and represented as 6 words, with the scheme from
[RFC2289](https://tools.ietf.org/html/rfc2289). Other representations are simply
different representations of this 64 bit number.

The [SHA-1](https://en.wikipedia.org/wiki/SHA-1) is considered as insecure,
because it is possible to generate multiple documents with same checksum. This
weakness do not apply here at all, because the possibility to genarate multiple
seed/secret combinations which creates same password is irrelevant for the use
case here. It is still no known possibilty to generate your master password from
password and `seed` you have used, so `SHA-1` is absolutely safe to use here.

Also S/Key is considered as insecure, because it is unsafe to use it on
unencrypted links. Do not use unencrypted links, interfaces or systems, whether
S/Key nor OTP nor this password manager can not help you in such cases. Using
the S/Key method for authentication is always MUCH more secure, than typing your
real password.

Do not generate passwords on devices that you do not trust!
