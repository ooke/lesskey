use regex::Regex;

#[derive(Debug)]
enum State {
    Wait,
    Read { line: String },
    Parsed { cmd: Vec<String> },
    Evaluated { out: Vec<String> },
    Error { msg: String },
    Quit,
}

struct LesSKEY {
    prompt: String,
    sep: Regex,
    rl: rustyline::Editor<()>,
    state: State,
}

impl LesSKEY {
    fn new(prompt: &str) -> LesSKEY {
        LesSKEY {
            prompt: String(prompt),
            sep: Regex::new(r"[\s\t\r\n]+").unwrap(),
            rl: rustyline::Editor<()>::new(),
            state: State::Wait,
        }
    }

    fn step(&mut self, state: State) -> LesSKEY {
        LesSKEY { prompt: self.prompt, sep: self.sep, rl: self.rl, state }
    }

    fn read(&mut self) -> LesSKEY {
        self.step(match self.state {
            Wait => match self.rl.readline(self.prompt) {
                Ok(line) => State::Read { line },
                Err(msg) => State::Error { msg: format!("{:?}", msg) }
            },
            Err(err) => err,
            state => State::Error {
                msg: format!("System in wrong state: {:?}", state)
            },
        })
    }

    fn parse(&mut self) -> LesSKEY {
        self.step(match self.state {
            State::Read { line } => State::Parsed { cmd: self.sep.split(line) },
            Err(err) => err,
            state => State::Error {
                msg: format!("System in wrong state: {:?}", state)
            }
        })
    }

    fn eval(&mut self) -> LesSKEY {
        self.step(match self.state {
            State::Parsed { cmd } => State::Evaluated { out: self.evaluate(cmd) },
            Err(err) => err,
            state => State::Error {
                msg: format!("System in wrong state: {:?}", state)
            }
        })
    }
}

pub fn main() {
    let mut cmd = LesSKEY::new("> ");

    loop {
        match cmd.read().parse().eval().print() {
            LesSKEY { state: State::Quit, .. } => break,
            new_cmd => cmd = new_cmd,
        }
    }
}