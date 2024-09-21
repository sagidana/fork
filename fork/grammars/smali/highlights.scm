[
  "->"
] @operator

[
  ".class"
  ".super"
  ".source"
  ".method"
  ".end method"
  ".locals"
  ".param"
  ".end param"
  ".annotation"
  ".end annotation"
  ".field"
  ".catch"
  ".implements"
  ".catchall"
] @keyword

(line_directive) @keyword

(opcode) @keyword
(number) @constant.numeric
(comment) @comment
(string) @string
(class_identifier) @support.type
(method_identifier) @entity.name.function
(field_identifier) @entity.name.function
(access_modifier) @entity.other.attribute-name
(label) @entity.name.tag
(parameter) @variable.parameter
