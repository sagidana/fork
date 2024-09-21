[
  "import"
  "var"
  "func"
  "if"
  "return"
  "else"
  "package"
] @keyword

(nil) @keyword

(qualified_type) @variable
(comment) @comment
(interpreted_string_literal) @string
(call_expression
  (selector_expression
    (field_identifier) @entity.name.function))
(call_expression
  (identifier) @entity.name.function)

