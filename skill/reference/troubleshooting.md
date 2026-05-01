# Troubleshooting — known failure modes

These are the issues that hit during the Bio Study Tutor build, with their root causes and fixes.

## "Front page does not show anything" / "games don't work"

**Symptom**: Study Guide tab is empty; clicking quiz choices does nothing.

**Cause**: the Shiny reactive graph is silently erroring. Most often this is a `@reactive.effect` reading from a dynamic input that doesn't exist yet:

```python
# BAD — fails when the button hasn't been rendered yet
@reactive.effect
def _watch_clicks():
    for c in range(4):
        if f"quiz_choice_{c}" in input and input[f"quiz_choice_{c}"]() > 0:
            ...
```

**Fix**: use plain HTML buttons + `Shiny.setInputValue` with `priority: 'event'`:

```python
# in the rendered HTML:
'<button class="quiz-choice" data-choice-idx="0">A. First option</button>'

# in NAV_JS (head):
$(document).on('click', '.quiz-choice', function(e) {
    Shiny.setInputValue('quiz_choice_made',
                        {idx: $(this).data('choice-idx'), ts: Date.now()},
                        {priority: 'event'});
});

# in server:
@reactive.effect
@reactive.event(input.quiz_choice_made)
def _on_choice():
    payload = input.quiz_choice_made()
    c = int(payload.get("idx"))
    ...
```

The reference `app/app.py` uses this pattern throughout for clickable cards, match-game tiles, and quiz choices.

## "Flip cards do not flip"

**Symptom**: clicking the Flip button does nothing.

**Cause**: same dynamic-input issue, but specifically for the flashcard flip button. The body-click handler sends a `Shiny.setInputValue('fc_card_clicked', ...)` but the `@reactive.event(input.fc_card_clicked)` doesn't always wire up correctly.

**Fix**: have the JS programmatically click the existing Shiny action button:

```javascript
$(document).on('click', '.flashcard-clickable', function(e) {
    if ($(e.target).closest('button').length) return;
    e.preventDefault();
    var btn = document.getElementById('fc_flip');
    if (btn) btn.click();
});
```

Then the server only watches the action button:
```python
@reactive.event(input.fc_flip)
def _():
    fc_flipped.set(not fc_flipped.get())
```

## Knowledge Graph tab is blank

**Symptom**: graph tab shows no graph or a broken iframe.

**Cause**: the original `srcdoc=` approach with quote-escaping (`html.replace(chr(39), chr(34))`) corrupts PyVis HTML containing both single and double quotes in JSON literals.

**Fix**: write the graph HTML to a static file directory and reference via iframe `src=`:

```python
# In app
PRINT_DIR = APP_DIR.parent / "print"
GRAPH_DIR = APP_DIR / "www"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

app = App(app_ui, server, static_assets={
    "/print-static": PRINT_DIR,
    "/graph-static": GRAPH_DIR,
    "/assets": GRAPH_DIR,
})

# In the graph render:
filename = write_graph_file(NODES_JSON, EDGES, GRAPH_DIR, ...)
ts = int(time.time() * 1000)  # cache-bust
return ui.tags.iframe(src=f"graph-static/{filename}?t={ts}", ...)
```

## "Static assets 404 on deployed shinyapps.io"

**Symptom**: print, graph, or logo paths return 404 on the deployed app but work locally.

**Cause**: shinyapps.io serves your app under a sub-path like `/bio_study_tutor/`. Absolute paths miss the sub-path.

**Fix**: see `deployment.md` Gotcha 2 — use relative paths everywhere.

## "Application deployment failed: Manifest file checksum mismatch"

**Cause**: edited a file after generating the manifest.

**Fix**: regenerate the manifest before each deploy. See `deployment.md` Gotcha 3.

## "Loading code from 'app' / Failed to find an application object"

**Cause**: package shadowing — both `app.py` and `app/__init__.py` exist, package wins, package is empty.

**Fix**: put the loader in `app/__init__.py`. See `deployment.md` Gotcha 1.

## OpenRouter API rejects the key

**Symptom**: chat tutor returns "OpenRouter error 401" or similar.

**Cause**: `.env` not loaded, key has typo, or the model ID is wrong.

**Fix**:
1. Check `.env` has `OPENROUTER_API_KEY=sk-or-v1-...` on its own line.
2. Test the key with curl:
   ```bash
   curl https://openrouter.ai/api/v1/auth/key \
        -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```
3. Verify the model in `app/llm.py` exists:
   ```bash
   curl https://openrouter.ai/api/v1/models | jq '.data[] | select(.id | contains("gemma"))'
   ```

## Quiz / flashcard generation produces invalid JSON

**Symptom**: clicking "Add quiz to queue" raises a `JSONDecodeError`.

**Cause**: the LLM ignored the JSON-mode instruction and returned prose with code fences.

**Fix**: `app/llm.py` already has `extract_json()` that strips code fences and tries multiple parse strategies. If it still fails:
1. Lower the model's `temperature` in the call (already 0.5–0.7; try 0.3).
2. Switch to a model with stronger structured output (Claude Haiku, GPT-4o-mini, Gemini Flash).
3. Add explicit "respond ONLY with JSON, no prose, no markdown fences" to the system prompt.

## "Knowledge graph is impossibly slow / freezes the browser"

**Symptom**: graph tab loads but interaction is unusable.

**Cause**: too many nodes/edges in one view. Default with all 254 nodes and ~1200 edges, all visible, with full physics simulation, is borderline on older laptops.

**Fix**:
- Default the chapter filter to a single chapter, not "all chapters".
- Default `Hide weak edges` to checked (drops `mentioned_in` edges).
- Reduce label size in the slider.
- Increase edge length (less crowding).

## Wiki authoring is overwhelming

**Symptom**: the LLM (or you) is staring at 254 pages to write and getting paralyzed.

**Fix**: do it in passes, not one at a time:
1. **Pass 1 (skeleton)**: write all chapter overview pages + all exam-topic pages. Just the frontmatter + a 1-2 sentence Summary. ~30-50 pages, fast.
2. **Pass 2 (atomic concepts)**: walk each chapter and write the "headline" concepts only — processes, principles, key structures. ~80-120 pages.
3. **Pass 3 (vocab)**: terms, people, comparisons, edge cases. ~80-120 pages.
4. **Pass 4 (cross-link)**: read every page once and add wikilinks to terms that have their own pages but aren't yet linked.

Run `python3 tools/build_kg.py && python3 tools/validate.py` after each pass to catch broken links early.
