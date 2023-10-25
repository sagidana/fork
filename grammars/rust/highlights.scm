[
    "use"
    "fn"
    "if"
    "for"
    "let"
    "in"
    "const"
    "else"
    "match"
    "false"
    "true"
] @keyword

[
    "-"
    "-="
    "->"
    "="
    "!="
    "*"
    "&"
    "<"
    "=="
    ">"
    "||"
    "&&"
    "+"
    "+="
] @operator

"." @delimiter
";" @delimiter

(integer_literal) @string
(string_literal) @constant.numeric


(line_comment) @comment
(block_comment) @comment

(type_identifier) @entity.name.class
(primitive_type) @entity.name.class

(call_expression
  function: (identifier) @entity.name.function)


