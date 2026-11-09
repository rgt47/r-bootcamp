-- contents.qmd is an HTML-only page (its body sits in a
-- content-visible block), but a PDF book still opens a chapter for
-- every listed file, titled from its heading, which leaves an empty
-- 'Contents' chapter. Drop that one heading from non-HTML output; the
-- PDF keeps its own printed table of contents.

function Header(h)
  if quarto.doc.is_format('html') then
    return nil
  end
  if h.level == 1 and h.identifier == 'contents'
     and pandoc.utils.stringify(h.content) == 'Contents' then
    return {}
  end
  return nil
end
