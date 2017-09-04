function invert_endian(a, inpl) {
    var t = inpl ? a : Array(a.length);
    for (var i = 0; i < a.length; ++i) {
	var t1 = (a[i] & 0xff) << 24;
	var t2 = ((a[i] >> 8) & 0xff) << 16;
	var t3 = ((a[i] >> 16) & 0xff) << 8;
	var t4 = (a[i] >> 24) & 0xff;
	t[i] = t1 | t2 | t3 | t4;
    }
    return t;
}

function gen_otp_sha1(secret, seed, n) {
    var t = seed.toString().toLowerCase() + secret;
    t = sha1_fold(core_sha1(str2binb(t), t.length * 8));
    for (var i = n; i > 0; --i) { t = sha1_fold(core_sha1(t, 64)); }
    // convert back to little-endian
    t = invert_endian(t, true);
    return t;
}

function sha1_fold(h) {
    h = invert_endian(h, true);
    return Array(h[0] ^ h[2] ^ h[4], h[1] ^ h[3]);
}

function a_to_both(a) { return a_to_6word(a) + " (" + a_to_hex(a) + ")"; }

function a_to_hex(a) {
    var s = "";
    for (var i = 0; i < 2; ++i) {
	for (var j = 0; j < 4; ++j) {
	    var t = (a[i] >> (8*j)) & 0xff;
	    t = t.toString(16).toLowerCase();
	    s += (t.length == 1) ? ('0' + t) : t; // 1 octet = 2 hex digits
	}
    }
    //return s.substr(0, s.length-1); // drop the last space
    return s.trim();
}

function a_to_dec6(h) {
    var s = "";
    var parity = 0;
    for (var i = 0; i < 2; ++i) {
	for (var j = 0; j < 32; j += 2) {
	    parity += (h[i] >> j) & 0x3;
	}
    }
    var ind;
    ind = (h[0] & 0xff) << 3;
    ind |= (h[0] >> 13) & 0x7;
    s += ind.toString(10) + " ";
    ind = ((h[0] >> 8) & 0x1f) << 6;
    ind |= (h[0] >> 18) & 0x3f;
    s += ind.toString(10) + " ";
    ind = ((h[0] >> 16) & 0x3) << 9;
    ind |= ((h[0] >> 24) & 0xff) << 1;
    ind |= (h[1] >> 7) & 0x1;
    s += ind.toString(10) + " ";
    ind = (h[1] & 0x7f) << 4;
    ind |= (h[1] >> 12) & 0xf;
    s += ind.toString(10) + " ";
    ind = ((h[1] >> 8) & 0xf) << 7;
    ind |= (h[1] >> 17) & 0x7f;
    s += ind.toString(10) + " ";
    ind = ((h[1] >> 16) & 0x1) << 10;
    ind |= ((h[1] >> 24) & 0xff) << 2;
    ind |= (parity & 0x03);
    s += ind.toString(10);
    return s;
}

function a_to_dec(a) {
    var s = "";
    for (var i = 0; i < 2; ++i) {
	for (var j = 0; j < 4; ++j) {
	    var t = (a[i] >> (8*j)) & 0xff;
	    t = t.toString(10).toLowerCase();
            s += t;
            if (i == 0 || j < 3) s += ' ';
	}
    }
    //return s.substr(0, s.length-1); // drop the last space
    return s.trim();
}

function a_to_b(a) {
    var s = "";
    for (var i = 0; i < 2; ++i) {
	for (var j = 0; j < 4; ++j) {
	    var t = (a[i] >> (8*j)) & 0xff;
            s += String.fromCharCode(t);
	}
    }
    return window.btoa(s).replace('=', '').trim();
}

function a_to_6word(h) {
    var s = "";
    // Calculate parity by summing pairs of bits and taking two LSB's of sum.
    var parity = 0;
    for (var i = 0; i < 2; ++i) {
	for (var j = 0; j < 32; j += 2) {
	    parity += (h[i] >> j) & 0x3;
	}
    }
    // Now look up words in the dictionary and output to string. This manual
    // method kind of sucks, but I didn't feel like figuring out a more
    // elegant way to do it.

    // first: 11 bits
    var ind;
    ind = (h[0] & 0xff) << 3;
    ind |= (h[0] >> 13) & 0x7;
    s += WORDS[ind] + " ";
    // second: 11 bits
    ind = ((h[0] >> 8) & 0x1f) << 6;
    ind |= (h[0] >> 18) & 0x3f;
    s += WORDS[ind] + " ";
    // third: 11 bits
    ind = ((h[0] >> 16) & 0x3) << 9;
    ind |= ((h[0] >> 24) & 0xff) << 1;
    ind |= (h[1] >> 7) & 0x1;
    s += WORDS[ind] + " ";
    // fourth: 11 bits
    ind = (h[1] & 0x7f) << 4;
    ind |= (h[1] >> 12) & 0xf;
    s += WORDS[ind] + " ";
    // fifth: 11 bits
    ind = ((h[1] >> 8) & 0xf) << 7;
    ind |= (h[1] >> 17) & 0x7f;
    s += WORDS[ind] + " ";
    // sixth: 9 bits + 2 parity bits
    ind = ((h[1] >> 16) & 0x1) << 10;
    ind |= ((h[1] >> 24) & 0xff) << 2;
    ind |= (parity & 0x03);
    s += WORDS[ind];
    return s;
}

var password_last_changed = new Date().getTime();

function now_changed() {
    password_last_changed = new Date().getTime();
}

function switch_passwords() {
    hide_all();
    now_changed();
    var pass = document.getElementById('secret');
    var pass2 = document.getElementById('secret2');
    var resn = document.getElementById('resn');
    pass2.value = "";
    pass.value = resn.innerHTML;
}   

function calculate() {
    hide_all();
    now_changed();
    try {
        var resn = document.getElementById('resn');
        var resm = document.getElementById('resm');
        var resx = document.getElementById('resx');
        var resb = document.getElementById('resb');
        var resd = document.getElementById('resd');

        resn.innerHTML = "";
        resm.innerHTML = "";
        resx.innerHTML = "";
        resb.innerHTML = "";
        resd.innerHTML = "";
        resd.title = "";

        try {
            var pass = document.getElementById('secret');
            var pass2 = document.getElementById('secret2');
            var seed = document.getElementById('seed').value;
            var prefix = document.getElementById('prefix').value;
            var iter = parseInt(document.getElementById('seq').value);
            var pw = pass.value;
            var pw2 = pass2.value;

            if (pw == "") throw {message: "no password given"};

            /*var seednum = seed.replace(/[^0-9]/g, '');
            if (seednum == "") {
                seednum = Math.floor(Math.random() * 100) + "";
                seed = seed + seednum;
                document.getElementById('seed').value = seed;
            }*/
            var seedname = seed.replace(/X+$/, '');
            if (seed != seedname) {
                var tmplen = (seed.length - seedname.length);
                if (tmplen > 8) { tmplen = 8; }
                else if (tmplen < 1) { tmplen = 1; }
                var seednum = Math.floor(Math.random() * Math.pow(10, tmplen)) + "";
                seed = seedname + seednum;
                document.getElementById('seed').value = seed;
            }

            if (pw2 != "" &&  pw != pw2) {
                resn.innerHTML = "passwords do not match";
                result_show();
            } else if (isNaN(iter) || iter < 1) {
                resn.innerHTML = "sequence need to be > 0";
                result_show();
            } else {
                var p = gen_otp_sha1(pw, seed, iter);
                var pw = a_to_6word(p);
                if (prefix == "") {
                    resn.innerHTML = pw;
                    resm.innerHTML = pw.replace(/ /g, '-');
                    resx.innerHTML = a_to_hex(p);
                    resb.innerHTML = a_to_b(p);
                } else {
                    resn.innerHTML = prefix + ' ' + pw;
                    resm.innerHTML = prefix + '-' + pw.replace(/ /g, '-');
                    resx.innerHTML = prefix + a_to_hex(p);
                    resb.innerHTML = prefix + a_to_b(p);
                }
                resd.title = a_to_dec6(p);
                resd.innerHTML = a_to_dec(p);
            }
        } catch (err) { resn.innerHTML = err.message; }
    } catch (err) { alert("ERROR: " + err.message); }
    return false;
}

var black_color = "#000";
function result_show() {
    document.getElementById('resn').style.color = "#000";
    document.getElementById('resm').style.color = "#000";
    document.getElementById('resx').style.color = "#000";
    document.getElementById('resb').style.color = "#000";
    document.getElementById('resd').style.color = "#000";
    black_color = document.getElementById('resn').style.color;
}

function result_hide() {
    document.getElementById('resn').style.color = "#fff";
    document.getElementById('resm').style.color = "#fff";
    document.getElementById('resx').style.color = "#fff";
    document.getElementById('resb').style.color = "#fff";
    document.getElementById('resd').style.color = "#fff";
}

function result_toggle() {
    var resncolor = document.getElementById('resn').style.color;
    secret_hide();
    if (resncolor == black_color) {
        result_hide();
    } else {
        result_show();
    }
}

function secret_show() {
    document.getElementById('secret').type = "text";
}

function secret_hide() {
    var secret = document.getElementById('secret')
    secret.type = "password";
}

function secret_toggle() {
    var sectype = document.getElementById('secret').type;
    result_hide();
    if (sectype == "text") {
        secret_hide();
    } else {
        secret_show();
    }
}

function hide_all() {
    secret_hide();
    result_hide();
}

function remove_selection() {
    if (window.getSelection) {
        if (window.getSelection().empty) {  // Chrome
            window.getSelection().empty();
        } else if (window.getSelection().removeAllRanges) {  // Firefox
            window.getSelection().removeAllRanges();
        }
    } else if (document.selection) {  // IE?
        document.selection.empty();
    }
}

function clear_passwords_after_timeout() {
    var t = new Date().getTime();
    if ((t - password_last_changed) > 180000) {
        document.getElementById('resn').innerHTML = "";
        document.getElementById('resm').innerHTML = "";
        document.getElementById('resx').innerHTML = "";
        document.getElementById('resb').innerHTML = "";
        document.getElementById('resd').innerHTML = "";
        document.getElementById('resd').title = "";
        document.getElementById('secret').value = "";
        document.getElementById('secret2').value = "";
        document.getElementById('prefix').value = "";
        hide_all();
    }
}

function deselect_obj(o) {
    o.selectionStart = o.selectionEnd;
}

window.setInterval(clear_passwords_after_timeout, 10000);
document.getElementById("seed").focus();
