package com.aicareercoach.mobile.ui.components

import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle

/**
 * The coach's replies come back with simple Markdown (**bold**, * bullets, # headings).
 * This turns that into styled text so students see bold words and bullet points instead of asterisks.
 */
fun markdownToStyled(text: String): AnnotatedString = buildAnnotatedString {
    val lines = text.replace("\r\n", "\n").split("\n")
    lines.forEachIndexed { index, raw ->
        var line = raw.trimEnd()
        var wholeLineBold = false
        val heading = Regex("^\\s{0,3}#{1,6}\\s+").find(line)
        if (heading != null) {
            line = line.substring(heading.range.last + 1)
            wholeLineBold = true
        }
        val bullet = Regex("^(\\s*)[*\\-+]\\s+").find(line)
        if (bullet != null) {
            line = bullet.groupValues[1] + "\u2022 " + line.substring(bullet.range.last + 1)
        }
        if (wholeLineBold) withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { appendInline(line) }
        else appendInline(line)
        if (index < lines.lastIndex) append("\n")
    }
}

/** Add one line of text, turning **bold** and *italic* markers into real styling. */
private fun AnnotatedString.Builder.appendInline(line: String) {
    // **bold** or __bold__, then *italic*; anything unmatched is shown as it is.
    val pattern = Regex("(\\*\\*|__)(.+?)\\1|(?<![*\\w])\\*(?!\\s)(.+?)(?<!\\s)\\*(?![*\\w])")
    var last = 0
    for (match in pattern.findAll(line)) {
        append(line.substring(last, match.range.first))
        val boldText = match.groups[2]?.value
        if (boldText != null) withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append(boldText) }
        else withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { append(match.groups[3]?.value.orEmpty()) }
        last = match.range.last + 1
    }
    append(line.substring(last))
}
