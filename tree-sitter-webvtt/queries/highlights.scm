(header_magic) @keyword
(timestamp) @number
(timing_arrow) @operator
(cue_identifier) @label
(setting_name) @property
((setting_value) @number
 (#match? @number "^-?[0-9]+(\\.[0-9]+)?%?$"))
((setting_value) @string
 (#not-match? @string "^-?[0-9]+(\\.[0-9]+)?%?$"))
(note_keyword) @comment
(comment_header) @comment
(comment_line) @comment
(style_keyword) @keyword
(region_keyword) @keyword

(region_setting_name) @property
(region_line ":" @punctuation.delimiter)
((region_setting_value) @number
 (#match? @number "^[0-9]+(\\.[0-9]+)?%?(,[ \\t]*[0-9]+(\\.[0-9]+)?%?)?[ \\t]*$"))
((region_setting_value) @string
 (#not-match? @string "^[0-9]+(\\.[0-9]+)?%?(,[ \\t]*[0-9]+(\\.[0-9]+)?%?)?[ \\t]*$"))

(tag_name) @tag
; Voice names use the same string color as Vue class attribute values.
((start_tag
  (tag_name) @_voice_tag
  (tag_annotation) @string)
 (#eq? @_voice_tag "v"))

((start_tag
  (tag_name) @_annotation_tag
  (tag_annotation) @attribute)
 (#not-eq? @_annotation_tag "v"))
(entity) @string.escape
[(tag_open) (tag_close_open) (tag_end)] @punctuation.bracket
