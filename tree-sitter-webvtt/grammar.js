/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: "webvtt",

  extras: $ => [],

  rules: {
    document: $ => seq(
      optional($.bom),
      $.header,
      repeat(choice($.blank_line, $._block)),
    ),

    bom: _ => "\uFEFF",

    header: $ => seq(
      $.header_magic,
      optional(seq($._hspace, $.header_text)),
      $.newline,
    ),

    header_magic: _ => "WEBVTT",
    header_text: _ => /[^\r\n]+/,

    _block: $ => choice(
      $.note_block,
      $.style_block,
      $.region_block,
      $.cue,
    ),

    note_block: $ => seq(
      $.note_keyword,
      optional(seq($._hspace, $.comment_header)),
      $.newline,
      repeat($.comment_line),
    ),

    note_keyword: _ => "NOTE",
    comment_header: _ => /[^\r\n]+/,
    comment_line: $ => seq($.comment_text, optional($.newline)),
    comment_text: _ => /[^\r\n]+/,

    style_block: $ => seq(
      $.style_keyword,
      $.newline,
      $.style_content,
      optional($.newline),
    ),

    style_keyword: _ => "STYLE",
    // A single range lets the embedded CSS parser see complete rule sets.
    // An empty line terminates the WebVTT block.
    style_content: _ => /[^\r\n]+(?:\r?\n[^\r\n]+)*/,

    region_block: $ => seq(
      $.region_keyword,
      $.newline,
      repeat1($.region_line),
    ),

    region_keyword: _ => "REGION",
    region_line: $ => seq(
      optional($._hspace),
      $.region_setting_name,
      ":",
      optional($._hspace),
      $.region_setting_value,
      optional($.newline),
    ),
    region_setting_name: _ => /[A-Za-z][A-Za-z0-9_-]*/,
    region_setting_value: _ => /[^ \t\r\n][^\r\n]*/,

    cue: $ => choice(
      seq($.timing_line, repeat1($.cue_text_line)),
      seq($.cue_identifier_line, $.timing_line, repeat1($.cue_text_line)),
    ),

    cue_identifier_line: $ => seq($.cue_identifier, $.newline),
    // A cue identifier must not contain the timing arrow. For this small
    // grammar we reject '>' entirely, which keeps timing lines unambiguous.
    cue_identifier: _ => token(prec(-1, /[^>\r\n]+/)),

    timing_line: $ => seq(
      field("start", $.timestamp),
      $._hspace,
      $.timing_arrow,
      $._hspace,
      field("end", $.timestamp),
      optional(seq($._hspace, $.cue_settings)),
      $.newline,
    ),

    timing_arrow: _ => "-->",

    timestamp: _ => token(prec(1, choice(
      /[0-9]{2,}:[0-9]{2}:[0-9]{2}\.[0-9]{3}/,
      /[0-9]{2}:[0-9]{2}\.[0-9]{3}/,
    ))),

    cue_settings: $ => seq(
      $.cue_setting,
      repeat(seq($._hspace, $.cue_setting)),
    ),

    cue_setting: $ => seq(
      $.setting_name,
      ":",
      $.setting_value,
    ),

    setting_name: _ => /[A-Za-z][A-Za-z0-9_-]*/,
    setting_value: _ => /[^ \t\r\n]+/,

    // Keep adjacent text and tags in the same line, including at EOF.
    cue_text_line: $ => prec.right(seq(
      repeat1(choice(
        $.timestamp_tag,
        $.end_tag,
        $.start_tag,
        $.entity,
        $.cue_text,
        $.cue_text_symbol,
      )),
      optional($.newline),
    )),

    timestamp_tag: $ => seq(
      $.tag_open,
      $.timestamp,
      $.tag_end,
    ),

    start_tag: $ => seq(
      $.tag_open,
      $.tag_name,
      optional($.tag_annotation),
      $.tag_end,
    ),

    end_tag: $ => seq(
      $.tag_close_open,
      $.tag_name,
      $.tag_end,
    ),

    tag_open: _ => "<",
    tag_close_open: _ => "</",
    tag_end: _ => ">",
    tag_name: _ => /[A-Za-z][A-Za-z0-9-]*/,
    tag_annotation: _ => token.immediate(/[^>\r\n]+/),

    entity: _ => /&[A-Za-z0-9#]+;/,
    cue_text: _ => /[^<>&\r\n]+/,
    cue_text_symbol: _ => token(prec(-1, /[<>&]/)),

    blank_line: _ => /[ \t]*\r?\n/,
    newline: _ => token(prec(1, /\r?\n/)),
    _hspace: _ => /[ \t]+/,
  },
});
