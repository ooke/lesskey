use regex::Regex;
use rustyline::Editor;
use chrono::naive::NaiveDate;
use std::process::{Command, Stdio};
use std::io::BufReader;
use std::io::BufRead;
use std::rc::Rc;

#[derive(Debug)]
enum PassMode {
    Regular,
    HexaDecimal,
    Base64,
    Decimal,
}

#[derive(Debug)]
struct Password {
    name: String,
    parent: Option<Rc<Password>>,
    prefix: Option<String>,
    mode: PassMode,
    length: u8,
    upcase: bool,
    nospaces: bool,
    date: NaiveDate,
    comment: Option<String>,
}

impl Password {
    fn read() -> Vec<Password> {
        let mut result: Vec<Password> = vec![];
        let process = match Command::new("logins").stdout(Stdio::piped()).spawn() {
            Err(why) => panic!("Could not spawn 'logins' command: {:?}", why),
            Ok(proc) => proc,
        };
        let buf = BufReader::new(process.stdout.unwrap());
        let re = Regex::new(r"^\s*(?:(\S+)\s+)?*(\S+)(?:\s+([0-9]*)([rR]|[uU]|[uU][rR]|[uU][nNhHbB]|[nNhHbBdD]|[nN][dD]|[dD]))?(?:\s+([0-9]+)\s*(?:[-]?\s*(.*))?)?\s*$").unwrap();
        for line in buf.lines() {
            let line = &*line.expect("buffer should return lines");
            println!("DEBUG: {:?}", line);
            let caps = match re.captures(line) {
                None => { println!("PARSE ERROR: {:?}", line); continue; },
                Some(cap) => cap,
            };
        }
        result
    }
}

#[derive(Debug)]
struct LKRead {
    rl: Editor::<()>,
    sep: Regex,
    prompt: String,
}

#[derive(Debug)]
struct LKEval {
    cmd: Vec<String>,
}

#[derive(Debug)]
struct LKPrint {
    out: Vec<String>,
    quit: bool,
}

impl LKRead {
    fn new(rl: Editor::<()>, sep: Regex, prompt: String) -> Self { Self { rl, sep, prompt } }

    fn read(&mut self) -> LKEval {
        let text = match self.rl.readline(&*self.prompt) {
            Ok(str) => str,
            Err(err) => format!("error {:?}", err.to_string()),
        };
        let mut cmd: Vec<String> = vec![];
        for part in self.sep.split(&text) {
            cmd.push(part.to_string())
        }
        println!("DEBUG: {:?}", cmd);
        LKEval::new(cmd)
    }

    fn refresh(&mut self) {

    }

    fn quit(&mut self) {

    }
}

impl LKEval {
    fn new(cmd: Vec<String>) -> Self { Self { cmd } }

    fn eval(&mut self) -> LKPrint {
        let mut out: Vec<String> = vec![];
        let mut quit: bool = false;

        match &self.cmd {
            cmd if cmd[0] == "quit" => {
                out.push("Bye!".to_string());
                quit = true;
            }
            cmd if cmd[0] == "print" => {
                for line in 1..cmd.len() {
                    out.push(format!("{}: {:?}", line, cmd[line]));
                }
            }
            cmd => {
                out.push(format!("UNKNOWN: {:?}", cmd));
            }
        }

        LKPrint::new(out, quit)
    }
}

impl LKPrint {
    fn new(out: Vec<String>, quit: bool) -> Self { Self { out, quit } }

    fn print(&mut self) -> bool {
        for line in &self.out {
            println!("{}", line);
        }
        return !self.quit;
    }
}

pub fn main() {
    let mut passwords = Password::read();
    let mut lkread = LKRead::new(
        Editor::<()>::new().unwrap(),
        Regex::new(r"[\s\r\n\t]+").unwrap(),
        String::from("> "));

    while lkread.read().eval().print() {
        lkread.refresh();
    }
    lkread.quit();
}
