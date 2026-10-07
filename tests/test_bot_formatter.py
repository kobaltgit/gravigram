from src.bot.formatter import markdown_to_telegram_html

def test_empty_and_plain_text():
    assert markdown_to_telegram_html("") == ""
    assert markdown_to_telegram_html("Hello World") == "Hello World"

def test_headers_conversion():
    res = markdown_to_telegram_html("# Header 1\n### Header 3")
    assert "<b>Header 1</b>" in res
    assert "<b>Header 3</b>" in res

def test_bold_and_italic():
    res = markdown_to_telegram_html("This is **bold** and this is *italic*.")
    assert "<b>bold</b>" in res
    assert "<i>italic</i>" in res

def test_strikethrough():
    res = markdown_to_telegram_html("This is ~~removed~~ text.")
    assert "<s>removed</s>" in res

def test_links_conversion():
    res = markdown_to_telegram_html("Check out [Google](https://google.com)!")
    assert '<a href="https://google.com">Google</a>' in res

def test_code_blocks_with_language():
    md = "```python\ndef test():\n    return 42\n```"
    res = markdown_to_telegram_html(md)
    assert '<pre><code class="language-python">def test():\n    return 42</code></pre>' in res

def test_inline_code():
    res = markdown_to_telegram_html("Use `git status` command")
    assert "<code>git status</code>" in res

def test_html_escaping_in_text():
    res = markdown_to_telegram_html("If a < b & b > c:")
    assert "a &lt; b &amp; b &gt; c" in res

def test_blockquotes():
    res = markdown_to_telegram_html("> Important notice\n> Next line")
    assert "<blockquote>Important notice\nNext line</blockquote>" in res

def test_code_with_markdown_symbols_not_corrupted():
    md = "```bash\nexport VAR_A=1\nexport VAR_B=2\necho *all*\n```"
    res = markdown_to_telegram_html(md)
    assert "VAR_A=1" in res
    assert "VAR_B=2" in res
    assert "*all*" in res
    assert "<i>" not in res
