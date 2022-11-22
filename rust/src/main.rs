#[macro_use]
extern crate lazy_static;

use regex::Regex;
use rustyline::Editor;
use chrono::naive::NaiveDate;
use std::process::{Command, Stdio};
use std::io::BufReader;
use std::io::BufRead;
use std::rc::Rc;

#[derive(thiserror::Error, Debug)]
pub enum LKErr<'a> {
    #[error("Failed to parse {0}: {1}")]
    ParseError(&'a str, &'a str),
    #[error("Failed to parse {0}: {1}")]
    ParseErrorS(&'a str, String),
}

#[derive(Debug, PartialEq)]
pub enum PassMode {
    Regular,
    HexaDecimal,
    Base64,
    Decimal,
}

#[derive(Debug, PartialEq)]
pub struct Password {
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
        for line in buf.lines() {
            let line = &*line.expect("buffer should return lines");
            match Password::from_line(line) {
                Ok(p) => result.push(p),
                Err(e) => println!("ERROR: parsing of {:?} not successfull: {:?}", line, e),
            }
        }
        result
    }

    fn from_line(line: &str) -> Result<Password, LKErr> {
        lazy_static! {
            static ref RE: Regex = Regex::new(r"^\s*(?:(\S+)\s+)?(\S+)\s+([0-9]+)?([rR]|[uU]|[uU][rR]|[uU][nNhHbB]|[nNhHbBdD]|[nN][dD]|[dD])\s+([0-9]+)\s+(\d{4}-\d{2}-\d{2})(?:\s+(.*))?\s*$").unwrap();
        }
        let caps = match RE.captures(line) {
            Some(caps) => caps,
            None => return Err(LKErr::ParseError(line, "correct string not found")),
        };
        let mut upcase: bool = false;
        let mut nospaces: bool = false;
        let mode = match caps.get(4).unwrap().as_str().to_uppercase().as_str() {
            "R" => PassMode::Regular,
            "U" | "UR" => { upcase = true; PassMode::Regular },
            "N" => { nospaces = true; PassMode::Regular },
            "UN" => { upcase = true; nospaces = true; PassMode::Regular },
            "H" => PassMode::HexaDecimal,
            "UH" => { upcase = true; PassMode::HexaDecimal },
            "B" => PassMode::Base64,
            "UB" => { upcase = true; PassMode::Base64 },
            "D" => PassMode::Decimal,
            "ND" => { nospaces = true; PassMode::Decimal },
            _ => return Err(LKErr::ParseError(line, "internal error")),
        };
        let length = match caps.get(3) {
            None => 0,
            Some(n) => match n.as_str().parse::<u8>() { Ok(x) => x, Err(e) => return Err(LKErr::ParseErrorS(line, e.to_string())) },
        };
        println!("DEBUG: {:?}", caps);
        Ok(Password { name: caps.get(2).unwrap().as_str().to_string(),
                      parent: None,
                      prefix: match caps.get(1) { None => None, Some(ma) => Some(ma.as_str().to_string()) },
                      mode: mode,
                      length: length,
                      upcase: upcase,
                      nospaces: nospaces,
                      date: NaiveDate::parse_from_str(caps.get(6).unwrap().as_str(), "%Y-%m-%d").expect("Should be checked by the regular expression."),
                      comment: match caps.get(7) { None => None, Some(ma) => Some(ma.as_str().to_string()) } })
    }
}

#[derive(Debug)]
struct LK {
    db: Vec<Password>,
}

#[derive(Debug)]
struct LKRead {
    rl: Editor::<()>,
    sep: Regex,
    prompt: String,
    state: Rc<LK>,
}

#[derive(Debug)]
struct LKEval {
    cmd: Vec<String>,
    state: Rc<LK>,
}

#[derive(Debug)]
struct LKPrint {
    out: Vec<String>,
    quit: bool,
    state: Rc<LK>,
}

impl LKRead {
    fn new(rl: Editor::<()>, sep: Regex, prompt: String, state: Rc<LK>) -> Self {
         Self { rl, sep, prompt, state }
    }

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
        LKEval::new(cmd, self.state.clone())
    }

    fn refresh(&mut self) {

    }

    fn quit(&mut self) {

    }
}

impl LKEval {
    fn new(cmd: Vec<String>, state: Rc<LK>) -> Self { Self { cmd, state } }

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

        LKPrint::new(out, quit, self.state.clone())
    }
}

impl LKPrint {
    fn new(out: Vec<String>, quit: bool, state: Rc<LK>) -> Self { Self { out, quit, state } }

    fn print(&mut self) -> bool {
        for line in &self.out {
            println!("{}", line);
        }
        return !self.quit;
    }
}

pub fn main() {
    let lk = Rc::new(LK { db: Password::read() });
    let mut lkread = LKRead::new(
        Editor::<()>::new().unwrap(),
        Regex::new(r"[\s\r\n\t]+").unwrap(),
        String::from("❯ "),
        lk.clone());

    while lkread.read().eval().print() {
        lkread.refresh();
    }
    lkread.quit();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_simple_test() {
        assert_eq!(Password::from_line("ableton89 R 99 2020-12-09 xx.ableton@domain.info https://www.ableton.com").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: None, mode: PassMode::Regular,
                              length: 0, upcase: false, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("xx.ableton@domain.info https://www.ableton.com".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 R 99 2020-12-09 xx.ableton@domain.info https://www.ableton.com").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Regular,
                              length: 0, upcase: false, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("xx.ableton@domain.info https://www.ableton.com".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 N 99 2020-12-09 xx.ableton@domain.info https://www.ableton.com").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Regular,
                              length: 0, upcase: false, nospaces: true, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("xx.ableton@domain.info https://www.ableton.com".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 UN 99 2020-12-09 xx.ableton@domain.info https://www.ableton.com").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Regular,
                              length: 0, upcase: true, nospaces: true, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("xx.ableton@domain.info https://www.ableton.com".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 20R 99 2020-12-09 a b c").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Regular,
                              length: 20, upcase: false, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("a b c".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 20UR 99 2020-12-09 a b c").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Regular,
                              length: 20, upcase: true, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("a b c".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 20UH 99 2020-12-09 a b c").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::HexaDecimal,
                              length: 20, upcase: true, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("a b c".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 20UB 99 2020-12-09 a b c").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Base64,
                              length: 20, upcase: true, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("a b c".to_string()) });
        assert_eq!(Password::from_line("#W9 ableton89 20D 99 2020-12-09 a b c").unwrap(),
                   Password { name: "ableton89".to_string(), parent: None, prefix: Some("#W9".to_string()), mode: PassMode::Decimal,
                              length: 20, upcase: false, nospaces: false, date: NaiveDate::from_ymd(2020, 12, 09),
                              comment: Some("a b c".to_string()) });
    }
}
