package com.aicareercoach.mobile.ui.screens.admin

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

private val dayFormat: DateTimeFormatter = DateTimeFormatter.ofPattern("d MMM yyyy")

/** Turns a server timestamp such as 2026-11-11T09:30:00 into "11 Nov 2026". Returns "" when it cannot be read. */
internal fun shortDate(timestamp: String): String =
    runCatching { LocalDate.parse(timestamp.take(10)).format(dayFormat) }.getOrDefault("")

/** "today", "yesterday", "5 days ago" or a date, for showing when a student was last active. */
internal fun daysAgo(timestamp: String): String {
    val day = runCatching { LocalDate.parse(timestamp.take(10)) }.getOrNull() ?: return ""
    val days = ChronoUnit.DAYS.between(day, LocalDate.now())
    return when {
        days <= 0L -> "today"
        days == 1L -> "yesterday"
        days < 30L -> "$days days ago"
        else -> day.format(dayFormat)
    }
}
