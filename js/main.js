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

var password_last_changed = new Date().getTime();
var def_clear_timeout = default_clear_passwords_timeout;
var keep_clear_timeout = keep_clear_passwords_timeout;
var clear_timeout = def_clear_timeout;
var default_fontfamily = "monospace";
var secure_fontfamily = "password";
var activated_background = "#359335";

function clear_passwords() {
    password_last_changed = new Date().getTime();
    document.getElementById('fname').value = "";
    document.getElementById('fmaster').value = "";
    document.getElementById('fmaster').style.fontFamily = "password";
    document.getElementById('fpassword').value = "";
    document.getElementById('fpassword').style.fontFamily = "password";
    document.getElementById('ftest').value = "";
    document.getElementById('ftest').style = "password";
    document.getElementById('store').style.background = "";
    document.getElementById('show').style.background = "";
    document.getElementById('copy').style.background = '';
}

function clear_passwords_after_timeout() {
    var t = new Date().getTime();
    if ((t - password_last_changed) > clear_timeout) {
        clear_passwords();
    }
}

function changed() {
    password_last_changed = new Date().getTime();
    generate();
}

var already_in_generate = false;
function generate() {
    if (already_in_generate) return false;
    already_in_generate = true;
    try {
        changed();
        var re_name = /^\s*(\S+)(\s+([rR]|[uU]|[uU][rR]|[uU][nNhH]|[nNhHbBdD]))?(\s+([0-9]+))?\s*$/g;
        var fname = document.getElementById('fname');
        var fmaster = document.getElementById('fmaster');
        var fpassword = document.getElementById('fpassword');
        var ftest = document.getElementById('ftest');
        var ma_name = re_name.exec(fname.value);
        var prefix = "";
        var prefixs = "";
        var name = "";
        var type = "R";
        var seq = 99;
        var master = fmaster.value;

        document.getElementById('store').style.background = '';
        document.getElementById('copy').style.background = '';
        fmaster.placeholder = "master password";
        fpassword.value = "";
        ftest.value = "";
        document.getElementById("show").style.background = '';
        fmaster.style.fontFamily = secure_fontfamily;
        fpassword.style.fontFamily = secure_fontfamily;

        if (ma_name != null) {
            name = ma_name[1];
            if (ma_name[3] != undefined) type = ma_name[3].toUpperCase();
            if (ma_name[5] != undefined) seq = parseInt(ma_name[5]);
        } else {
            var re_name = /^\s*((\S+)\s+)?(\S+)(\s+([rR]|[uU]|[uU][rR]|[uU][nNhH]|[nNhHbB]))?(\s+([0-9]+))?\s*$/g;
            var ma_name = re_name.exec(fname.value);
            if (ma_name != null) {
                if (ma_name[2] != undefined) prefix = ma_name[2];
                name = ma_name[3];
                if (ma_name[5] != undefined) type = ma_name[5].toUpperCase();
                if (ma_name[7] != undefined) seq = parseInt(ma_name[7]);
            }
        }
        if (prefix != "") { prefixs = prefix + " "; }

        if (name != "") {
            var seedname = name.replace(/X+$/, '');
            if (name != seedname) {
                var tmplen = (name.length - seedname.length);
                if (tmplen > 8) { tmplen = 8; }
                else if (tmplen < 1) { tmplen = 1; }
                var seednum = Math.floor(Math.random() * Math.pow(10, tmplen)) + "";
                name = seedname + seednum;
            }
            new_name = "";
            if (prefix != "")  new_name = prefix + " ";
            new_name = new_name + name + " " + type + " " + seq;
            fname.value = new_name;
        } else {
            if (fname.value != "") {
                fmaster.placeholder = "ERROR: failed to parse name!";
            } else {
                fmaster.placeholder = "master password";
            }
            already_in_generate = false;
            return;
        }

        if (master != "") {
            var passkey = gen_otp_sha1(master, name, seq);
            var password = "";
            switch (type) {
            case "R": password = prefixs + a_to_6word(passkey); break;
            case "U": password = prefixs + a_to_6word(passkey).toUpperCase(); break;
            case "UH": password = prefix + a_to_hex(passkey).toUpperCase(); break;
            case "UN": password = (prefixs + a_to_6word(passkey).toUpperCase()).replace(/ /g, '-'); break;
            case "H": password = prefix + a_to_hex(passkey); break;
            case "B": password = prefix + a_to_b(passkey); break;
            case "D": password = a_to_dec6(passkey); break;
            case "N": password = (prefixs + a_to_6word(passkey)).replace(/ /g, '-'); break;
            default: throw new SyntaxError("Unknown type '" + type + "'");
            }
            fpassword.value = password;
            var fullval = fname.value + ":" + fmaster.value;
            secret_sha1 = binb2b64(core_sha1(str2binb(fullval), fullval.length * 8));
            if (isStored(secret_sha1)) {
                document.getElementById('store').style.background = activated_background;
            }
        }
    } catch (err) { alert("ERROR: " + err.message); }
    already_in_generate = false;
}

function password_select() {
    var fpassword = document.getElementById("fpassword");
    fpassword.focus();
    var range = document.createRange();
    range.selectNodeContents(fpassword);
    var s = window.getSelection();
    s.removeAllRanges();
    s.addRange(range);
    fpassword.setSelectionRange(0, 999999);
}

function button_show() {
    var fmaster = document.getElementById("fmaster");
    var fpassword = document.getElementById("fpassword");
    var ftest = document.getElementById("ftest");
    if (fpassword.style.fontFamily == default_fontfamily || fmaster.style.fontFamily == default_fontfamily) {
        fmaster.style.fontFamily = secure_fontfamily;
        fpassword.style.fontFamily = secure_fontfamily;
        ftest.style.fontFamily = secure_fontfamily;
        document.getElementById("show").style.background = '';
    } else {
        fpassword.style.fontFamily = default_fontfamily;
        ftest.style.fontFamily = default_fontfamily;
        document.getElementById("show").style.background = activated_background;
    }
}

function button_show_master() {
    var fmaster = document.getElementById("fmaster");
    var fpassword = document.getElementById("fpassword");
    var ftest = document.getElementById("ftest");
    if (fpassword.style.fontFamily == default_fontfamily || fmaster.style.fontFamily == default_fontfamily) {
        fmaster.style.fontFamily = secure_fontfamily;
        fpassword.style.fontFamily = secure_fontfamily;
        ftest.style.fontFamily = secure_fontfamily;
        document.getElementById("show").style.background = '';
    } else {
        fmaster.style.fontFamily = default_fontfamily;
        document.getElementById("show").style.background = activated_background;
    }
}

function button_copy() {
    password_select();
    if(!document.execCommand('copy')) {
        alert("ERROR: failed to copy");
    } else {
        document.getElementById('copy').style.background = activated_background;
    }
}

function button_switch() {
    var fname = document.getElementById('fname');
    var fmaster = document.getElementById('fmaster');
    var fpassword = document.getElementById('fpassword');
    var ftest = document.getElementById('ftest');
    ftest.value = "";
    fmaster.value = fpassword.value;
    fpassword.value = "";
    fname.value = "";
    fname.focus();
}

function button_store() {
    var fname = document.getElementById('fname');
    var fmaster = document.getElementById('fmaster');
    var fpassword = document.getElementById('fpassword');
    var store = document.getElementById('store');

    if (fname.value != "" && fmaster.value != "") {
        var fullval = fname.value + ":" + fmaster.value;
        secret_sha1 = binb2b64(core_sha1(str2binb(fullval), fullval.length * 8));
        if (store.style.background != '') {
            removeStored(secret_sha1);
        } else {
            storeItem(secret_sha1);
        }
        changed();
        fpassword.focus();
        password_select();
    }
}

function verify_test() {
    var fpassword = document.getElementById("fpassword");
    var ftest = document.getElementById("ftest");
    if (fpassword.value == ftest.value) {
        ftest.value = "";
    } else {
        ftest.style.background = '';
    }
}

function testchanged() {
    var fmaster = document.getElementById("fmaster");
    var fpassword = document.getElementById("fpassword");
    var ftest = document.getElementById("ftest");
    fmaster.style.fontFamily = secure_fontfamily;
    fpassword.style.fontFamily = secure_fontfamily;
    ftest.style.fontFamily = secure_fontfamily;
    document.getElementById("show").style.background = '';
    password_last_changed = new Date().getTime();
}

function button_keep() {
    if (clear_timeout == def_clear_timeout) {
        clear_timeout = keep_clear_timeout;
        document.getElementById("keep").style.background = activated_background;
    } else {
        clear_timeout = def_clear_timeout;
        document.getElementById("keep").style.background = '';
        clear_passwords();
    }
}

function button_clear() {
    clear_passwords();
    document.getElementById("fname").focus();
}

function resize_input_fields() {
    if ($(window).width() <= 630) {
        $(".flarge").removeClass("input-sm");
        $(".flarge").removeClass("input-md");
        $(".flarge").removeClass("input-lg");
        $(".flarge").addClass("input-sm");
    } else if ($(window).width() <= 1014) {
        $(".flarge").removeClass("input-sm");
        $(".flarge").removeClass("input-md");
        $(".flarge").removeClass("input-lg");
        $(".flarge").addClass("input-md");
    } else if ($(window).width() > 1014) {
        $(".flarge").removeClass("input-sm");
        $(".flarge").removeClass("input-md");
        $(".flarge").removeClass("input-lg");
        $(".flarge").addClass("input-lg");
    }
}

window.setInterval(clear_passwords_after_timeout, 1000);
document.getElementById("fname").focus();
$("#fname").on('keyup', function(e) { if (e.keyCode == 13) {
    var fmaster = document.getElementById('fmaster');
    var fpassword = document.getElementById('fpassword');
    if (fmaster.value != "") {
        fpassword.focus();
        password_select();
    } else fmaster.focus();
}});
$("#fmaster").on('keyup', function(e) { if (e.keyCode == 13) {
    document.getElementById("fpassword").focus();
    password_select();
}});
$("#fpassword").on('keyup', function(e) { if (e.keyCode == 13) {
    button_switch();
}});
$("#ftest").on('keyup', function(e) { if (e.keyCode == 13) {
    verify_test();
    document.getElementById("ftest").focus();
}});
resize_input_fields();
$(window).resize(resize_input_fields);
        
