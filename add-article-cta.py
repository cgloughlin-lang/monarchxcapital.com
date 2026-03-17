#!/usr/bin/env python3
"""
add-article-cta.py
Batch-update all MonarchX Capital article HTML files to:
1. Replace the existing .article-cta block with a full contact form + Calendly CTA
2. Inject new CSS into the <style> block
3. Inject Calendly script before </body>
4. Fix mailto links to open mail client (keep copy as secondary icon)

Run from any directory. Modifies files in-place.
"""

import os
import re
import glob

INSIGHTS_DIR = os.path.join(os.path.dirname(__file__), "insights")

# ── CSS to inject (appended inside the existing <style> block) ──────────────
INJECT_CSS = """
  /* ===== ARTICLE CONTACT CTA ===== */
  .article-contact-cta {
    border-top: 2px solid var(--gold);
    background: var(--charcoal);
    padding: 52px 56px;
    margin: 64px 0 0;
  }
  .article-contact-cta-inner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: start;
  }
  .article-cta-headline {
    font-family: var(--font-serif);
    font-size: clamp(22px, 3vw, 32px);
    font-weight: 500;
    color: var(--white);
    margin-bottom: 12px;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }
  .article-cta-headline em { font-style: italic; color: var(--gold); }
  .article-cta-sub {
    font-size: 14px;
    color: var(--white-dim);
    line-height: 1.7;
    margin-bottom: 32px;
  }
  /* Compact form */
  .article-contact-form { display: flex; flex-direction: column; gap: 12px; }
  .article-contact-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .article-contact-input, .article-contact-textarea {
    background: var(--charcoal-mid);
    border: 1px solid var(--border);
    padding: 12px 16px;
    color: var(--white);
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 300;
    outline: none;
    transition: border-color 0.2s;
    width: 100%;
  }
  .article-contact-input::placeholder, .article-contact-textarea::placeholder { color: var(--white-faint); }
  .article-contact-input:focus, .article-contact-textarea:focus { border-color: var(--gold); }
  .article-contact-textarea { resize: vertical; min-height: 72px; }
  .article-contact-submit {
    background: var(--gold);
    color: var(--black);
    border: none;
    padding: 14px 28px;
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s;
    align-self: flex-start;
  }
  .article-contact-submit:hover { background: var(--gold-light); }
  .article-contact-success {
    display: none;
    font-size: 13px;
    color: var(--gold);
    padding: 10px 0;
    letter-spacing: 0.03em;
  }
  /* Calendly column */
  .article-calendly-col { display: flex; flex-direction: column; }
  .article-calendly-label {
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 16px;
    display: block;
  }
  .article-calendly-widget {
    background: var(--charcoal-mid);
    border: 1px solid var(--border);
    overflow: hidden;
    flex: 1;
    min-height: 500px;
  }
  .article-calendly-widget .calendly-inline-widget {
    min-width: 100%;
    height: 500px;
  }
  /* Original article-cta kept for backward compat but hidden if new one present */
  .article-contact-cta + .article-cta { display: none; }
  /* Responsive */
  @media (max-width: 768px) {
    .article-contact-cta { padding: 40px 28px; }
    .article-contact-cta-inner { grid-template-columns: 1fr; gap: 40px; }
    .article-contact-form-row { grid-template-columns: 1fr; }
    .article-contact-submit { width: 100%; text-align: center; }
  }
"""

# ── The new CTA HTML block (inserted BEFORE existing .article-cta) ──────────
# {FORM_ID} will be replaced with a unique per-file ID to avoid conflicts
NEW_CTA_HTML = """
  <div class="article-contact-cta">
    <div class="article-contact-cta-inner">
      <div>
        <h3 class="article-cta-headline">Want to discuss this for<br><em>your business?</em></h3>
        <p class="article-cta-sub">We work with a select number of clients at any given time. If this resonates, let's talk.</p>
        <form class="article-contact-form" id="articleForm{FORM_ID}" action="https://formspree.io/f/xpwzgkdl" method="POST">
          <div class="article-contact-form-row">
            <input type="text" class="article-contact-input" name="name" placeholder="Name" required>
            <input type="email" class="article-contact-input" name="email" placeholder="Email" required>
          </div>
          <input type="text" class="article-contact-input" name="message" placeholder="What are you working on?">
          <input type="hidden" name="_source" value="{SOURCE_PAGE}">
          <button type="submit" class="article-contact-submit" id="articleSubmit{FORM_ID}">Start a Conversation</button>
          <p class="article-contact-success" id="articleSuccess{FORM_ID}">Thank you. Charlotte will be in touch within 24 hours.</p>
        </form>
        <p style="font-size:12px;color:var(--white-faint);margin-top:20px;line-height:1.6;">Or email directly: <a href="mailto:charlotte@monarchxcapital.com" style="color:var(--gold);">charlotte@monarchxcapital.com</a></p>
      </div>
      <div class="article-calendly-col">
        <span class="article-calendly-label">Or book 15 minutes directly</span>
        <div class="article-calendly-widget">
          <div class="calendly-inline-widget" data-url="https://calendly.com/christopherloughlin/30min?hide_gdpr_banner=1&background_color=111118&text_color=f0f0f0&primary_color=C9A962" style="min-width:100%;height:500px;"></div>
        </div>
      </div>
    </div>
  </div>
"""

# ── JS to inject before </body> ──────────────────────────────────────────────
INJECT_JS = """<script>
(function() {
  var forms = document.querySelectorAll('.article-contact-form');
  forms.forEach(function(form) {
    var formId = form.id.replace('articleForm', '');
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var btn = document.getElementById('articleSubmit' + formId);
      var success = document.getElementById('articleSuccess' + formId);
      btn.disabled = true;
      btn.textContent = 'Sending...';
      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'Accept': 'application/json' }
      }).then(function(r) {
        if (r.ok) {
          form.reset();
          btn.style.display = 'none';
          success.style.display = 'block';
        } else {
          btn.disabled = false;
          btn.textContent = 'Start a Conversation';
          success.textContent = 'Something went wrong — please email charlotte@monarchxcapital.com';
          success.style.display = 'block';
        }
      }).catch(function() {
        btn.disabled = false;
        btn.textContent = 'Start a Conversation';
        success.textContent = 'Something went wrong — please email charlotte@monarchxcapital.com';
        success.style.display = 'block';
      });
    });
  });
})();
</script>
<script type="text/javascript" src="https://assets.calendly.com/assets/external/widget.js" async></script>
"""


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Derive a short unique ID from the filename
    basename = os.path.splitext(os.path.basename(filepath))[0]
    form_id = re.sub(r'[^a-zA-Z0-9]', '', basename)[:20]

    # ── 1. Inject CSS before closing </style> ───────────────────────────────
    if "article-contact-cta" not in content:
        # Find the last </style> in the head
        style_close = content.rfind("</style>")
        if style_close != -1:
            content = content[:style_close] + INJECT_CSS + "\n</style>" + content[style_close + 8:]

    # ── 2. Replace existing article-cta block with new CTA + old CTA ─────────
    # The existing block looks like:
    #   <div class="article-cta">...</div>
    # We insert our new block immediately before it.
    if "article-contact-cta" not in content:
        existing_cta_pattern = r'(<div class="article-cta">)'
        new_html = NEW_CTA_HTML.replace("{FORM_ID}", form_id).replace("{SOURCE_PAGE}", basename)
        # Replace only the first occurrence (there's typically one per article)
        content, n = re.subn(existing_cta_pattern, new_html + r'\1', content, count=1)
        if n == 0:
            # No existing .article-cta — insert before <footer>
            content = content.replace("<footer>", new_html + "\n\n<footer>", 1)

    # ── 3. Fix mailto links: remove onclick=preventDefault pattern ────────────
    # Pattern: onclick="event.preventDefault();navigator.clipboard..." on mailto hrefs
    # Change: keep href as-is (mailto:), remove the onclick entirely
    content = re.sub(
        r' onclick="event\.preventDefault\(\);navigator\.clipboard[^"]*"',
        '',
        content
    )
    # Also fix any article-cta mailto links that use the arrow pattern — keep them
    # (they're already fine as mailto: links, just ensure they open properly)

    # ── 4. Inject JS + Calendly script before </body> ────────────────────────
    if "assets.calendly.com" not in content:
        content = content.replace("</body>", INJECT_JS + "\n</body>")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    pattern = os.path.join(INSIGHTS_DIR, "*.html")
    files = sorted(glob.glob(pattern))
    # Exclude insights/index.html
    files = [f for f in files if os.path.basename(f) != "index.html"]

    modified = []
    skipped = []

    for filepath in files:
        try:
            changed = process_file(filepath)
            if changed:
                modified.append(filepath)
                print(f"  ✓  {os.path.basename(filepath)}")
            else:
                skipped.append(filepath)
                print(f"  –  {os.path.basename(filepath)} (no changes needed)")
        except Exception as e:
            print(f"  ✗  {os.path.basename(filepath)}: {e}")

    print(f"\nDone. {len(modified)} modified, {len(skipped)} already up to date.")
    return modified


if __name__ == "__main__":
    main()
