divert(-1)

define(`about_url', `https://github.com/ooke/lesskey')
define(`about_title', `source code repository')
define(`about_name', `LesS/KEY')
define(`about_class', `github-button')
define(`show_about_url', `true')
define(`show_page_icon', `true')
define(`double_click_on_result', `ondblclick="copy_content($1)"')
define(`click_on_key_label', `onclick="result_toggle()"')
define(`click_on_seed_label', `onclick="clear_passwords()"')
define(`default_clear_passwords_timeout', `60000')
define(`keep_clear_passwords_timeout', `1200000')
define(`show_new_window_button', `true')
define(`use_small_fonts', `false')
define(`install_files', `files_web.conf')

define(`m4_format', defn(`format')) undefine(`format')

divert(1)dnl
