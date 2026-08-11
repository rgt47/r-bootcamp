#!/usr/bin/env Rscript

# Procedurally generate the book cover and favicon.
# Forest gradient anchored on the brand green #2d5016,
# overlaid with title typography. Reproducible: re-running
# regenerates identical output (seed is fixed).
#
# This volume uses the single-gradient idiom shared with the
# Git, Quarto, and Python boot-camp volumes, rather than the
# two-zone watercolor composition used by the textbooks.

set.seed(47)

out_dir <- if (interactive()) "images" else
  dirname(sub("--file=", "", grep("--file=", commandArgs(),
    value = TRUE)))
if (length(out_dir) == 0 || is.na(out_dir)) out_dir <- "."

brand <- "#2d5016"

# Vertical gradient from deep forest to pale lime.
ramp <- grDevices::colorRampPalette(
  c("#12200a", brand, "#5a8c3a", "#a8c88a", "#eaf2df")
)

draw_cover <- function(path, width, height, with_text) {
  grDevices::png(path, width = width, height = height,
    units = "px", res = 150, bg = brand)
  on.exit(grDevices::dev.off(), add = TRUE)

  op <- graphics::par(mar = c(0, 0, 0, 0))
  on.exit(graphics::par(op), add = TRUE)

  n <- 400
  cols <- ramp(n)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = c(0, 1),
    xaxs = "i", yaxs = "i")
  ys <- seq(0, 1, length.out = n + 1)
  for (i in seq_len(n)) {
    graphics::rect(0, ys[i], 1, ys[i + 1], col = cols[i],
      border = NA)
  }

  # Faint stratigraphy suggesting daily session layers.
  for (y in seq(0.08, 0.92, by = 0.06)) {
    graphics::segments(0, y, 1, y,
      col = grDevices::adjustcolor("#ffffff", 0.06),
      lwd = 1)
  }

  if (with_text) {
    graphics::text(0.5, 0.61, "R for",
      col = "#f4f8ee", cex = 3.2, font = 2)
    graphics::text(0.5, 0.52, "Biostatistics",
      col = "#f4f8ee", cex = 3.2, font = 2)
    graphics::text(0.5, 0.40, "A One-Week Boot Camp",
      col = "#f4f8ee", cex = 1.5, font = 3)
    graphics::text(0.5, 0.08, "The rgtlab Curriculum Project",
      col = grDevices::adjustcolor("#f4f8ee", 0.85),
      cex = 1.0)
  }
}

draw_cover(file.path(out_dir, "cover.png"),
  width = 1200, height = 1800, with_text = TRUE)

draw_cover(file.path(out_dir, "favicon.png"),
  width = 128, height = 128, with_text = FALSE)

message("Wrote cover.png and favicon.png to ", out_dir)
