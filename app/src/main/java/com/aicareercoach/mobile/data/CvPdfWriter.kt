package com.aicareercoach.mobile.data

import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.text.StaticLayout
import android.text.TextPaint
import java.io.OutputStream

/**
 * Turns the CV's simple Markdown (headings, bullets, notes) into an A4 PDF.
 * Text is wrapped to the page width and continues onto new pages as needed.
 */
object CvPdfWriter {
    private const val PAGE_WIDTH = 595   // A4 at 72 points per inch
    private const val PAGE_HEIGHT = 842
    private const val MARGIN = 48f

    private fun textPaint(size: Float, bold: Boolean, textColor: Int): TextPaint =
        TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = size
            typeface = Typeface.create(Typeface.SANS_SERIF, if (bold) Typeface.BOLD else Typeface.NORMAL)
            color = textColor
        }

    fun write(markdown: String, output: OutputStream) {
        val namePaint = textPaint(20f, true, Color.BLACK)
        val headingPaint = textPaint(13f, true, Color.rgb(37, 99, 235))
        val bodyPaint = textPaint(10.5f, false, Color.rgb(17, 24, 39))
        val notePaint = textPaint(9f, false, Color.GRAY)
        val contentWidth = (PAGE_WIDTH - 2 * MARGIN).toInt()

        val document = PdfDocument()
        try {
            var pageNumber = 1
            var page = document.startPage(PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create())
            var y = MARGIN

            for (raw in markdown.lines()) {
                val line = raw.replace("**", "").trimEnd()
                if (line.isBlank()) {
                    y += 6f
                    continue
                }
                val text: String
                val paint: TextPaint
                val spaceBefore: Float
                when {
                    line.startsWith("## ") -> {
                        text = line.removePrefix("## ").uppercase()
                        paint = headingPaint
                        spaceBefore = 10f
                    }
                    line.startsWith("# ") -> {
                        text = line.removePrefix("# ")
                        paint = namePaint
                        spaceBefore = 0f
                    }
                    line.startsWith("- ") -> {
                        text = "•  " + line.removePrefix("- ")
                        paint = bodyPaint
                        spaceBefore = 2f
                    }
                    line.startsWith("> ") -> {
                        text = line.removePrefix("> ")
                        paint = notePaint
                        spaceBefore = 6f
                    }
                    else -> {
                        text = line
                        paint = bodyPaint
                        spaceBefore = 2f
                    }
                }
                val layout = StaticLayout.Builder.obtain(text, 0, text.length, paint, contentWidth)
                    .setLineSpacing(0f, 1.15f)
                    .build()
                y += spaceBefore
                if (y + layout.height > PAGE_HEIGHT - MARGIN) {
                    document.finishPage(page)
                    pageNumber += 1
                    page = document.startPage(
                        PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create()
                    )
                    y = MARGIN
                }
                val canvas = page.canvas
                canvas.save()
                canvas.translate(MARGIN, y)
                layout.draw(canvas)
                canvas.restore()
                y += layout.height
            }
            document.finishPage(page)
            document.writeTo(output)
        } finally {
            document.close()
        }
    }
}
