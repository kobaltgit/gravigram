import re
import html

def markdown_to_telegram_html(text: str) -> str:
    """
    Converts LLM Markdown (GitHub Flavored Markdown) to valid Telegram HTML.
    Telegram HTML supports:
    - <b>bold</b>, <strong>bold</strong>
    - <i>italic</i>, <em>italic</em>
    - <u>underline</u>, <ins>underline</ins>
    - <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
    - <span class="tg-spoiler">spoiler</span>
    - <a href="http://www.example.com/">inline URL</a>
    - <code>inline fixed-width code</code>
    - <pre><code class="language-python">pre-formatted fixed-width code block</code></pre>
    - <blockquote>blockquote</blockquote>
    """
    if not text:
        return ""

    # Placeholder storage for code blocks and inline code to prevent double-escaping
    code_blocks = []
    inline_codes = []

    def save_code_block(match):
        lang = match.group(1) or ""
        code_content = match.group(2)
        # Escape HTML entities inside code
        escaped_code = html.escape(code_content.strip("\r\n"))
        index = len(code_blocks)
        if lang:
            tag = f'<pre><code class="language-{html.escape(lang)}">{escaped_code}</code></pre>'
        else:
            tag = f'<pre><code>{escaped_code}</code></pre>'
        code_blocks.append(tag)
        # Use tokens without underscores or asterisks to avoid markdown regex collision
        return f"XTOKENCODEBLOCK{index}XTOKEN"

    def save_inline_code(match):
        code_content = match.group(1)
        escaped_code = html.escape(code_content)
        index = len(inline_codes)
        tag = f'<code>{escaped_code}</code>'
        inline_codes.append(tag)
        # Use tokens without underscores or asterisks to avoid markdown regex collision
        return f"XTOKENINLINECODE{index}XTOKEN"

    # 1. Extract triple-backtick code blocks
    text = re.sub(r'```([a-zA-Z0-9_\-\+]*)\n?([\s\S]*?)```', save_code_block, text)

    # 2. Extract single-backtick inline code
    text = re.sub(r'`([^`\n]+)`', save_inline_code, text)

    # 3. Escape HTML in regular text
    text = html.escape(text)

    # 4. Headers: ### Header -> <b>Header</b>
    text = re.sub(r'^(#{1,6})\s+(.+)$', r'<b>\2</b>', text, flags=re.MULTILINE)

    # 5. Bold: **text** or __text__ -> <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

    # 6. Italic: *text* or _text_ -> <i>text</i>
    text = re.sub(r'(?<!\w)\*([^\*\n]+?)\*(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'<i>\1</i>', text)

    # 7. Strikethrough: ~~text~~ -> <s>text</s>
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)

    # 8. Links: [title](url) -> <a href="\2">\1</a>
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2">\1</a>', text)

    # 9. Blockquotes: > text -> <blockquote>text</blockquote>
    lines = text.split("\n")
    new_lines = []
    in_quote = False
    quote_acc = []

    for line in lines:
        if line.startswith("&gt; "):
            quote_acc.append(line[5:])
            in_quote = True
        else:
            if in_quote:
                quote_joined = "\n".join(quote_acc)
                new_lines.append(f"<blockquote>{quote_joined}</blockquote>")
                quote_acc = []
                in_quote = False
            new_lines.append(line)
    if in_quote:
        quote_joined = "\n".join(quote_acc)
        new_lines.append(f"<blockquote>{quote_joined}</blockquote>")

    text = "\n".join(new_lines)

    # 10. Restore code blocks and inline code
    for i, tag in enumerate(inline_codes):
        text = text.replace(f"XTOKENINLINECODE{i}XTOKEN", tag)

    for i, tag in enumerate(code_blocks):
        text = text.replace(f"XTOKENCODEBLOCK{i}XTOKEN", tag)

    return text
