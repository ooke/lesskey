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
var def_clear_timeout = default_clear_passwords_timeout;
var keep_clear_timeout = keep_clear_passwords_timeout;
var selected_id = '';
var selected_border_style = "2px solid #337ab7";
var copied_border_style = "2px solid #359335";
var copied_background = "#359335";
var copied_borderColor = "#248224";

var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '=': '&#x3D;'
};

function escapeHtml (string) {
  return String(string).replace(/[&<>"'=\/]/g, function (s) {
    return entityMap[s];
  });
}

var fakeLocalStorage = {};
function storeItem (data) {
    data = 'lesskey:' + data;
    window.localStorage.setItem(data, "true");
    if (window.localStorage.getItem(data) != "true")
        fakeLocalStorage[data] = true;
}
function isStored (data) {
    data = 'lesskey:' + data;
    if (window.localStorage.getItem(data) == "true")
        return true;
    return fakeLocalStorage[data] == true;
}
function removeStored (data) {
    data = 'lesskey:' + data;
    window.localStorage.removeItem(data);
    delete fakeLocalStorage[data];
}

function now_changed() {
    restart_timer();
    reset_generated();
    var mcorrect = document.getElementById('mcorrect');
    var correct = document.getElementById('correct');
    var secret = document.getElementById('secret');
    var seed = document.getElementById('seed').value;
    var prefix = document.getElementById('prefix').value;
    var ptype = document.getElementById('ptype').value;
    if (secret.value.trim() != '') {
        secret_sha1 = binb2b64(core_sha1(str2binb(secret.value), secret.value.length * 8));
        fulldata = seed + ":" + prefix + ":" + ptype + ":" + secret_sha1;
        fulldata_sha1 = binb2b64(core_sha1(str2binb(fulldata), fulldata.length * 8));
        if (isStored(fulldata_sha1) && !isStored(secret_sha1))
            storeItem(secret_sha1);
        if (isStored(secret_sha1)) {
            if (isStored(fulldata_sha1)) {
                secret.style.background = '#33dd33';
                mcorrect.checked = true;
                correct.checked = true;
            } else {
                secret.style.background = '#33dddd';
                mcorrect.checked = true;
                correct.checked = false;
            }
        } else secret.style.background = '#ffffff';
        if (isStored(fulldata_sha1)) {
            generate();
        } else correct.checked = false;
    }
}

function restart_timer() {
    password_last_changed = new Date().getTime();
}

function switch_passwords() {
    hide_all();
    now_changed();
    var pass = document.getElementById('secret');
    var pass2 = document.getElementById('secret2');
    var res = document.getElementById('res');
    pass2.value = "";
    pass.value = res.innerHTML;
    var seed = document.getElementById('seed');
    now_changed();
    seed.select();
    seed.selectionStart = seed.selectionEnd;
    document.getElementById('res').innerHTML = "";
    document.getElementById('res').tile = "";
}

var already_in_generate = false;
function generate() {
    if (already_in_generate) return false;
    already_in_generate = true;
    hide_all();
    now_changed();
    try {
        var res = document.getElementById('res');
        res.innerHTML = "";
        res.title = "";

        try {
            var pass = document.getElementById('secret');
            var pass2 = document.getElementById('secret2');
            var seed = document.getElementById('seed').value;
            var calc = document.getElementById('calc');
            var test = document.getElementById('test');
            var prefix = escapeHtml(document.getElementById('prefix').value);
            var iter = parseInt(document.getElementById('seq').value);
            var pw = pass.value;
            var pw2 = pass2.value;

            if (pw == "") throw {message: "no password given"};

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
                res.innerHTML = "the passwords don't match!";
                result_show();
            } else if (isNaN(iter) || iter < 1) {
                res.innerHTML = "sequence need to be > 0";
                result_show();
            } else {
                var p = gen_otp_sha1(pw, seed, iter);
                var pw = a_to_6word(p);
                switch (document.getElementById('ptype').value) {
                case "dec": 
                    res.title = a_to_dec6(p);
                    res.innerHTML = a_to_dec(p);
                    break;
                case "nsp":
                    if (prefix == "") res.innerHTML = pw.replace(/ /g, '-');
                    else res.innerHTML = prefix + '-' + pw.replace(/ /g, '-');
                    break;
                case "hex":
                    if (prefix == "") res.innerHTML = a_to_hex(p);
                    else res.innerHTML = prefix + a_to_hex(p);
                    break;
                case "b64":
                    if (prefix == "") res.innerHTML = a_to_b(p);
                    else res.innerHTML = prefix + a_to_b(p);
                    break;
                default:
                    if (prefix == "") res.innerHTML = pw;
                    else res.innerHTML = prefix + ' ' + pw;
                    break;
                }
                calc.textContent = "GENERATED";
                document.getElementById('show_hide').removeAttribute('disabled');
                test.removeAttribute('disabled');
                test.style.background = "#fff";
                test.value = "";
                calc.style.background = copied_background;
                calc.style.borderColor = copied_borderColor;
                store_selected('res');
                test.select();
            }
        } catch (err) { res.innerHTML = err.message; result_show();}
    } catch (err) { alert("ERROR: " + err.message); }
    already_in_generate = false;
    return false;
}

var black_color = "#000";
function result_show() {
    document.getElementById('res').style.fontFamily = "monospace";
    black_color = document.getElementById('res').style.fontFamily;
    document.getElementById('show_hide').textContent = "hide";
    /* restart the timer in order to give the user more time */
    if (document.getElementById('keep').checked == false) {
        restart_timer();
    }
}

function result_hide() {
    document.getElementById('res').style.fontFamily = "password";
    document.getElementById('show_hide').textContent = "show";
}

function result_toggle() {
    var rescolor = document.getElementById('res').style.fontFamily;
    secret_hide();
    if (rescolor == black_color) {
        result_hide();
    } else {
        result_show();
    }
}

function secret_show() {
    document.getElementById('secret').type = "text";
    document.getElementById('secret2').type = "text";
    document.getElementById('prefix').type = "text";
    /* restart the timer in order to give the user more time */
    if (document.getElementById('keep').checked == false) {
        restart_timer();
    }
}

function secret_hide() {
    var secret = document.getElementById('secret').type = "password";
    var secret2 = document.getElementById('secret2').type = "password";
    document.getElementById('prefix').type = "password"
}

function secret_toggle() {
    var sectype = document.getElementById('secret').type;
    result_hide();
    if (sectype == "text") {
        secret_hide();
    }
    /* don't make secret visible if 'keep' is checked */
    else if (document.getElementById('keep').checked == false) {
        secret_show();
    }
}

function hide_all() {
    secret_hide();
    result_hide();
    reset_selected();
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
    var clear_timeout = def_clear_timeout;
    if (document.getElementById('keep').checked) {
        clear_timeout = keep_clear_timeout;
    }
    var t = new Date().getTime();
    if (((clear_timeout - (t - password_last_changed)) <= 61000) && (document.getElementById('secret').value != "")) {
        document.getElementById('keepstr').innerHTML = "&nbsp;(" + Math.max(0, Math.floor((clear_timeout - (t - password_last_changed)) / 1000)) + "s)";
    }
    else if (((clear_timeout - (t - password_last_changed)) <= keep_clear_timeout) && (document.getElementById('secret').value != "")) {
        document.getElementById('keepstr').innerHTML = "&nbsp;(" + Math.max(0, Math.ceil((clear_timeout - (t - password_last_changed)) / 60000)) + "m)";
    }
    else {
        document.getElementById('keepstr').innerHTML = "";
    }
    if ((t - password_last_changed) > clear_timeout) {
        clear_passwords();
    }
}

function check_clear_passwords(cb) {
    secret_hide();
    if (cb.checked == false) {
        clear_passwords();
    }
}

function store_password(tb) {
    secret_hide();
    seed = document.getElementById('seed').value;
    prefix = document.getElementById('prefix').value;
    ptype = document.getElementById('ptype').value;
    secret = document.getElementById('secret').value;
    secret_sha1 = binb2b64(core_sha1(str2binb(secret), secret.length * 8));
    fulldata = seed + ":" + prefix + ":" + ptype + ":" + secret_sha1;
    fulldata_sha1 = binb2b64(core_sha1(str2binb(fulldata), fulldata.length * 8))
    if (tb.checked == true) {
        storeItem(secret_sha1);
    } else {
        if (isStored(secret_sha1)) removeStored(secret_sha1);
        if (isStored(fulldata_sha1)) removeStored(fulldata_sha1);
        document.getElementById('mcorrect').checked = false;
    }
    now_changed();
}

function correct_password(tb) {
    secret_hide();
    seed = document.getElementById('seed').value;
    prefix = document.getElementById('prefix').value;
    ptype = document.getElementById('ptype').value;
    secret = document.getElementById('secret').value;
    secret_sha1 = binb2b64(core_sha1(str2binb(secret), secret.length * 8));
    fulldata = seed + ":" + prefix + ":" + ptype + ":" + secret_sha1;
    fulldata_sha1 = binb2b64(core_sha1(str2binb(fulldata), fulldata.length * 8))
    if (tb.checked == true) {
        document.getElementById('correct').checked = true;
        storeItem(fulldata_sha1);
    } else {
        if (isStored(fulldata_sha1)) removeStored(fulldata_sha1);
    }
    now_changed();
}

function clear_passwords() {
    document.getElementById('res').innerHTML = "";
    document.getElementById('res').title = "";
    document.getElementById('test').innerHTML = "";
    document.getElementById('secret').value = "";
    document.getElementById('secret').style.background = "#fff";
    document.getElementById('secret2').value = "";
    document.getElementById('prefix').value = "";
    document.getElementById('seed').value = "";
    document.getElementById('ptype').value = "reg";
    document.getElementById('correct').checked = false;
    document.getElementById('mcorrect').checked = false;
    document.getElementById('copy_btn').setAttribute('disabled', 'disabled');
    document.getElementById('show_hide').setAttribute('disabled', 'disabled');
    document.getElementById('test').value = "";
    document.getElementById('test').setAttribute('disabled', 'disabled');
    document.getElementById('test').style.background = "#fff";
    hide_all();
    reset_generated();
}

function reset_selected() {
    selected_id = '';
    document.getElementById('res').style.border = '';
    document.getElementById('copy_btn').textContent = "copy selected";
    document.getElementById('copy_btn').style.background = '';
    document.getElementById('copy_btn').style.borderColor = '';
}

function reset_generated() {
    document.getElementById('calc').textContent = "generate";
    document.getElementById('calc').style.background = '';
    document.getElementById('calc').style.borderColor = '';
}

function deselect_obj(o) {
    o.selectionStart = o.selectionEnd;
}

function store_selected(id) {
    reset_selected();
    selected_id = id;
    document.getElementById(id).style.border = selected_border_style;
    document.getElementById('copy_btn').removeAttribute('disabled');
    document.getElementById(id).focus();
    if (document.selection) {
        var range = document.body.createTextRange();
        range.moveToElementText(document.getElementById(id));
        range.select();
    } else if (window.getSelection) {
        var range = document.createRange();
        range.selectNode(document.getElementById(id));
        window.getSelection().addRange(range);
    }
}

function copy_hidden(text) {
    try {
        if (document.queryCommandSupported('copy') == true) {
            var textArea = document.createElement("textarea");
            textArea.style.position = "fixed";
            textArea.style.top = 0;
            textArea.style.left = 0;
            textArea.style.background  ="transparent";
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            var copy_res = document.execCommand('copy');
            document.body.removeChild(textArea);
            remove_selection();
            if (copy_res == false) {
                console.log("Copy command failed!");
            }
            return copy_res;
        }
        else{
            console.log("Copy command is not supported!");
            return false;
        }
    }
    catch (err) {
        console.log("Caught exception while trying to copy!");
        return false;
    }
}

function copy_selected() {
    if (selected_id != '') {
        copy_content(selected_id);
    }
}

function copy_content(id) {
    var e = document.getElementById(id);
    if (e.innerHTML != '') {
        if (copy_hidden(e.innerHTML) == true) {
            document.getElementById('copy_btn').textContent = "COPIED";
            document.getElementById('copy_btn').style.background = copied_background;
            document.getElementById('copy_btn').style.borderColor = copied_borderColor;
            e.style.border = copied_border_style;
        }
    }
}

var test_points = 0;
function test_password() {
    var test = document.getElementById('test');
    var res = document.getElementById('res');
    var points = document.getElementById('points');
    if (test.value == res.innerHTML) {
        test.style.background = "#33dd33";
        test.value = "";
        test_points += 1;
        points.innerHTML = test_points + "&nbsp;points";
    } else if (test.value.length >= res.innerHTML.length) {
        test.style.background = "#dd8888";
        test.style.fontFamily = "monospace";
        test_points = 0;
        points.innerHTML = "&nbsp;";
        result_show();
    } else if (test.value != "") {
        test.style.background = "#ffffff";
        test.style.fontFamily = "password";
        result_hide();
    } else {
        test.style.background = "#ffffff";
        test.style.fontFamily = "monospace";
        result_hide();
    }
}

function test_reset() {
    var res = document.getElementById('res');
    var test = document.getElementById('test');
    var points = document.getElementById('points');
    test.value = "";
    if (res.innerHTML == "") {
        test.setAttribute('disabled', 'disabled');
    } else {
        test.removeAttribute('disabled');
    }
    test.style.background = "#fff";
    test.style.fontFamily = "monospace";
    test_points = 0;
    points.innerHTML = "&nbsp;";
}

window.setInterval(clear_passwords_after_timeout, 1000);
document.getElementById("seed").focus();
document.getElementById('copy_btn').setAttribute('disabled', 'disabled');
document.getElementById('show_hide').setAttribute('disabled', 'disabled');
test_reset();
